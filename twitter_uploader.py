import time
from asyncio import sleep
from io import BytesIO
from pathlib import Path
from typing import List
import base64
from pytwitter import Api
from telegram import Update
from telegram.ext import ContextTypes

media_types = {
    '.mp4': 'video/mp4',
    '.mov': 'video/quicktime',
    '.gif': 'image/gif',
    '.jpg': 'image/jpeg',
    '.jpeg': 'image/jpeg',
    '.png': 'image/png'
}

class TelegramTwitterTransfer:


    def __init__(self, twitter_api: Api, download_path: str = "temp_downloads"):
        self.twitter_api = twitter_api
        self.download_path = Path(download_path)
        self.download_path.mkdir(exist_ok=True)

    async def transfer_to_twitter(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> str:
        if update.channel_post.photo:
            file = await context.bot.get_file(update.channel_post.photo[-1].file_id)
            extension = ".jpg"
            media_type = "image/jpeg"
        elif update.channel_post.video:
            file = await context.bot.get_file(update.channel_post.video.file_id)
            extension = ".mp4"
            media_type = "video/mp4"
        elif update.channel_post.document:
            file = await context.bot.get_file(update.channel_post.document.file_id)
            extension = Path(update.channel_post.document.file_name).suffix

            media_type = media_types.get(extension.lower())
            if not media_type:
                raise ValueError(f"Unsupported file type: {extension}")
        else:
            raise ValueError("No supported media found in the message")

        filename = f"{file.file_unique_id}{extension}"
        filepath = self.download_path / filename

        try:
            print(f"Downloading file from Telegram: {filename}")
            await file.download_to_drive(filepath)

            print(f"Uploading to Twitter: {filename}")
            return (
                self.upload_image(filepath)
                if media_type.startswith('image/')
                else self._upload_video(filepath, media_type)
            )
        finally:
            if filepath.exists():
                filepath.unlink()

    async def transfer_media_group(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> List[str]:
        if not update.channel_post.media_group_id:
            media_id = await self.transfer_to_twitter(update, context)
            return [media_id]

        if not hasattr(context.bot_data, 'media_groups'):
            context.bot_data.media_groups = {}

        media_group_id = update.channel_post.media_group_id
        if media_group_id not in context.bot_data.media_groups:
            context.bot_data.media_groups[media_group_id] = []

        context.bot_data.media_groups[media_group_id].append(update.channel_post)
        await sleep(1)

        media_messages = context.bot_data.media_groups[media_group_id]
        media_ids = []

        for message in media_messages:
            try:
                if message.photo:
                    file = await context.bot.get_file(message.photo[-1].file_id)
                    extension = ".jpg"
                    media_type = "image/jpeg"
                elif message.video:
                    file = await context.bot.get_file(message.video.file_id)
                    extension = ".mp4"
                    media_type = "video/mp4"
                else:
                    continue  # Skip unsupported media types

                filename = f"{file.file_unique_id}{extension}"
                filepath = self.download_path / filename

                try:
                    print(f"Downloading file from Telegram: {filename}")
                    await file.download_to_drive(filepath)

                    print(f"Uploading to Twitter: {filename}")
                    media_id = (
                        self.upload_image(filepath)
                        if media_type.startswith('image/')
                        else self._upload_video(filepath, media_type)
                    )
                    media_ids.append(media_id)
                finally:
                    if filepath.exists():
                        filepath.unlink()

            except Exception as e:
                print(f"Error processing media: {e}")
                continue

        # Cleanup media group data
        del context.bot_data.media_groups[media_group_id]

        return media_ids

    def upload_image(self, file_path: Path|str) -> str:
        print("Uploading image...")
        with open(file_path, 'rb') as f:
            media_data = base64.b64encode(f.read()).decode("utf-8")
            response = self.twitter_api.upload_media_simple(media_data=media_data)
        return response.media_id_string



    def _upload_video(self, file_path: Path, media_type: str) -> str:
        total_bytes = file_path.stat().st_size
        print(f"Initializing video upload ({total_bytes} bytes)")

        resp = self.twitter_api.upload_media_chunked_init(
            total_bytes=total_bytes,
            media_type=media_type
        )
        media_id = resp.media_id_string

        chunk_size = 1024 * 1024
        segment_index = 0
        bytes_sent = 0

        with open(file_path, 'rb') as file:
            while bytes_sent < total_bytes:
                chunk = file.read(chunk_size)
                if not chunk:
                    break

                print(f"Uploading chunk {segment_index + 1}")
                self.twitter_api.upload_media_chunked_append(
                    media_id=media_id,
                    media=BytesIO(chunk),
                    segment_index=segment_index
                )

                bytes_sent += len(chunk)
                segment_index += 1
                time.sleep(0.1)  # Rate limiting prevention

        print("Finalizing upload...")
        self.twitter_api.upload_media_chunked_finalize(media_id=media_id)
        self._wait_for_processing(media_id)
        return media_id

    def _wait_for_processing(self, media_id: str, check_interval: int = 3, max_attempts: int = 60):
        """Wait for video processing to complete."""
        for _ in range(max_attempts):
            status = self.twitter_api.upload_media_chunked_status(media_id=media_id)
            state = status.processing_info.state

            if state == 'failed':
                error = status.processing_info.error
                raise Exception(f"Processing failed: {error}")

            elif state == 'succeeded':
                print("Processing completed successfully!")
                return
            print(f"Processing status: {state}")
            time.sleep(check_interval)

        raise TimeoutError("Video processing timed out")
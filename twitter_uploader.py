import time
from asyncio import sleep
from io import BytesIO
from pathlib import Path
from typing import List, Optional
import base64
import os
from pytwitter import Api
from telegram import Update
from telegram.ext import ContextTypes


class TelegramTwitterTransfer:
    CHUNK_SIZE = 1024 * 1024  # 1MB chunks
    MEDIA_TYPES = {
        '.mp4': 'video/mp4',
        '.mov': 'video/quicktime',
        '.gif': 'image/gif',
        '.jpg': 'image/jpeg',
        '.jpeg': 'image/jpeg',
        '.png': 'image/png'
    }

    def __init__(self, twitter_api: Api, download_path: str = "temp_downloads"):
        self.twitter_api = twitter_api
        self.download_path = Path(download_path)
        self.download_path.mkdir(exist_ok=True)

    async def transfer_to_twitter(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> str:
        """Transfer a single media file from Telegram to Twitter."""
        file_info = self._get_file_info(update.channel_post)
        if not file_info:
            raise ValueError("No supported media found in the message")

        file, extension, media_type = file_info
        filename = f"{file.file_unique_id}{extension}"
        filepath = self.download_path / filename

        try:
            print(f"Downloading file from Telegram: {filename}")
            await file.download_to_drive(filepath)

            print(f"Uploading to Twitter: {filename}")
            with open(filepath, "rb") as media_file:
                return self._upload_media(media_file, media_type)
        finally:
            if filepath.exists():
                filepath.unlink()

    async def transfer_media_group(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> List[str]:
        """Transfer a group of media files from Telegram to Twitter."""
        if not update.channel_post.media_group_id:
            media_id = await self.transfer_to_twitter(update, context)
            return [media_id]

        # Initialize media groups storage if needed
        if not hasattr(context.bot_data, 'media_groups'):
            context.bot_data.media_groups = {}

        media_group_id = update.channel_post.media_group_id
        if media_group_id not in context.bot_data.media_groups:
            context.bot_data.media_groups[media_group_id] = []

        context.bot_data.media_groups[media_group_id].append(update.channel_post)
        await sleep(1)  # Wait for all media in group to be collected

        media_messages = context.bot_data.media_groups[media_group_id]
        media_ids = []

        try:
            for message in media_messages:
                file_info = self._get_file_info(message)
                if not file_info:
                    continue

                file, extension, media_type = file_info
                filename = f"{file.file_unique_id}{extension}"
                filepath = self.download_path / filename

                try:
                    print(f"Downloading file from Telegram: {filename}")
                    await file.download_to_drive(filepath)

                    print(f"Uploading to Twitter: {filename}")
                    with open(filepath, "rb") as media_file:
                        media_id = self._upload_media(media_file, media_type)
                        media_ids.append(media_id)
                finally:
                    if filepath.exists():
                        filepath.unlink()

        finally:
            # Cleanup media group data
            del context.bot_data.media_groups[media_group_id]

        return media_ids

    def _get_file_info(self, message):
        """Extract file information from a Telegram message."""
        if message.photo:
            return (
                message.bot.get_file(message.photo[-1].file_id),
                ".jpg",
                "image/jpeg"
            )
        elif message.video:
            return (
                message.bot.get_file(message.video.file_id),
                ".mp4",
                "video/mp4"
            )
        elif message.document:
            file = message.bot.get_file(message.document.file_id)
            extension = Path(message.document.file_name).suffix
            media_type = self.MEDIA_TYPES.get(extension.lower())
            return (file, extension, media_type) if media_type else None
        return None

    def _upload_media(self, media_file, media_type: str) -> str:
        """Upload media to Twitter using the appropriate method based on media type."""
        if media_type.startswith('image/'):
            return self._upload_image(media_file)
        else:
            return self._upload_video(media_file, media_type)

    def _upload_image(self, media_file) -> str:
        """Upload an image to Twitter."""
        print("Uploading image...")
        media_data = base64.b64encode(media_file.read()).decode("utf-8")
        response = self.twitter_api.upload_media_simple(media_data=media_data)
        return response.media_id_string

    def _upload_video(self, media_file, media_type: str) -> str:
        """Upload a video to Twitter using multipart upload."""
        media_file.seek(0, 2)  # Seek to end to get file size
        total_bytes = media_file.tell()
        media_file.seek(0)  # Reset to beginning

        print(f"Initializing video upload ({total_bytes} bytes)")

        # Initialize upload
        resp = self.twitter_api.upload_media_chunked_init(
            total_bytes=total_bytes,
            media_type=media_type
        )
        media_id = resp.media_id_string

        # Upload chunks
        segment_index = 0
        bytes_sent = 0

        while bytes_sent < total_bytes:
            chunk = media_file.read(self.CHUNK_SIZE)
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
        for attempt in range(max_attempts):
            status = self.twitter_api.upload_media_chunked_status(media_id=media_id)
            state = status.processing_info.state

            if state == 'failed':
                error = status.processing_info.error
                raise Exception(f"Processing failed: {error}")
            elif state == 'succeeded':
                print("Processing completed successfully!")
                return

            print(f"Processing status: {state} (attempt {attempt + 1}/{max_attempts})")
            time.sleep(check_interval)

        raise TimeoutError("Video processing timed out")



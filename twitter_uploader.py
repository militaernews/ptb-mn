import base64
import time
from io import BytesIO
from pathlib import Path
from typing import List

from pytwitter import Api
from telegram._bot import Bot

from data.db import get_file_id, query_files


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

    async def transfer_to_twitter(self, msg_id: int, bot: Bot) -> str:
        """Transfer a single media file from Telegram to Twitter using stored file information."""
        # Get file_id from database instead of message
        file_id = await get_file_id(msg_id)
        if not file_id:
            raise ValueError("No supported media found in the message")

        file = await bot.get_file(file_id)
        extension = self._get_extension_from_file(file)
        media_type = self.MEDIA_TYPES.get(extension.lower())

        if not media_type:
            raise ValueError(f"Unsupported media type: {extension}")

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

    async def transfer_media_group(self, file_ids:List[str], bot: Bot) -> List[str]:
        """Transfer a group of media files from Telegram to Twitter using stored information."""

        media_ids=[]
        for file_id in file_ids:
            file = await bot.get_file(file_id)
            extension = self._get_extension_from_file(file)
            media_type = self.MEDIA_TYPES.get(extension.lower())

            if not media_type:
                continue

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

        return media_ids

    def upload_local_file(self, file_path: str) -> str:
        """Upload a file from local storage to Twitter.

        Args:
            file_path (str): Path to the local file

        Returns:
            str: Twitter media ID

        Raises:
            ValueError: If file type is not supported
            FileNotFoundError: If file doesn't exist
        """
        file_path = Path(file_path)
        if not file_path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")

        # Get file extension and media type
        extension = file_path.suffix.lower()
        media_type = self.MEDIA_TYPES.get(extension)

        if not media_type:
            raise ValueError(f"Unsupported file type: {extension}")

        print(f"Uploading local file to Twitter: {file_path.name}")
        with open(file_path, "rb") as media_file:
            return self._upload_media(media_file, media_type)

    def _get_extension_from_file(self, file) -> str:
        """Determine file extension based on file path or mime type."""
        return Path(file.file_path).suffix if hasattr(file, 'file_path') else '.jpg'



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
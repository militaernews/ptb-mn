import os
import logging
import asyncio
import yt_dlp
from typing import Optional, List

logger = logging.getLogger(__name__)

async def download_media(url: str, download_dir: str = "/tmp/downloads") -> Optional[List[str]]:
    """
    Downloads media from a given URL (Twitter, Instagram, YouTube) using yt-dlp.
    Returns a list of paths to the downloaded files.
    """
    if not os.path.exists(download_dir):
        os.makedirs(download_dir)

    ydl_opts = {
        'format': 'bestvideo+bestaudio/best',
        'outtmpl': f'{download_dir}/%(id)s.%(ext)s',
        'max_filesize': 50 * 1024 * 1024,  # 50MB limit for Telegram
        'quiet': True,
        'no_warnings': True,
    }

    try:
        loop = asyncio.get_event_loop()
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            # Run extraction in a thread to not block the event loop
            info = await loop.run_in_executor(None, lambda: ydl.extract_info(url, download=True))
            
            if 'entries' in info:
                # It's a playlist or multiple entries
                files = [ydl.prepare_filename(e) for e in info['entries']]
            else:
                files = [ydl.prepare_filename(info)]
            
            # Filter only existing files (sometimes yt-dlp might not download if already exists or other reasons)
            existing_files = [f for f in files if os.path.exists(f)]
            return existing_files if existing_files else None

    except Exception as e:
        logger.error(f"Error downloading media from {url}: {e}")
        return None

def cleanup_files(files: List[str]):
    """Removes the downloaded files."""
    for f in files:
        try:
            if os.path.exists(f):
                os.remove(f)
        except Exception as e:
            logger.error(f"Error deleting file {f}: {e}")

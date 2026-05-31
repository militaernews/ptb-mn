"""
private/video_downloader.py
───────────────────────────
Video download handler for the private bot.

Users (or admins) send a URL in a private chat → the bot downloads the
video via yt-dlp and sends it back as a Telegram video message.

Supported platforms (handled automatically by yt-dlp):
  YouTube, Twitter/X, Instagram, TikTok, Reddit, and ~1 800 others.

Integration in main.py
───────────────────────
    from private.video_downloader import register_video_downloader
    register_video_downloader(application)   # call before register_news()

New dependency in requirements.txt
────────────────────────────────────
    yt-dlp
    # ffmpeg must be installed system-wide (apt/brew/choco install ffmpeg)
"""

import logging
import os
import re
import tempfile
from pathlib import Path
from typing import Optional

from telegram import Update
from telegram.constants import ChatAction, ParseMode
from telegram.ext import Application, ContextTypes, MessageHandler, filters

from settings.config import ADMINS, LOG_GROUP
from util.error_logger import get_error_logger

logger = logging.getLogger(__name__)

# ─── Constants ────────────────────────────────────────────────────────────────

# Telegram Bot API upload limit
MAX_FILE_SIZE_MB: int = 50
MAX_FILE_SIZE_BYTES: int = MAX_FILE_SIZE_MB * 1024 * 1024

# Maximum video resolution – higher means larger files and potential Telegram errors
MAX_HEIGHT: int = 720

# Path to a Netscape-format cookies.txt exported from a logged-in browser.
# Needed to bypass YouTube's bot-detection ("Sign in to confirm you're not a bot").
# Mount the file into the container and set this env var, or leave blank to skip.
# See: https://github.com/yt-dlp/yt-dlp/wiki/FAQ#how-do-i-pass-cookies-to-yt-dlp
COOKIES_PATH: Optional[str] = os.getenv("YT_COOKIES_FILE", "/app/secrets/youtube-cookies.txt")

# ─── URL Detection ────────────────────────────────────────────────────────────

_VIDEO_URL_RE = re.compile(
    r"https?://"
    r"(?:"
    r"(?:www\.)?youtube\.com/(?:watch|shorts)\S+"
    r"|youtu\.be/\S+"
    r"|(?:www\.)?twitter\.com/\S+/status/\d+"
    r"|(?:www\.)?x\.com/\S+/status/\d+"
    r"|(?:www\.)?instagram\.com/(?:p|reel|tv)/\S+"
    r"|(?:vm\.)?tiktok\.com/\S+"
    r"|(?:www\.)?reddit\.com/r/\S+/comments/\S+"
    r")",
    re.IGNORECASE,
)


def _find_url(text: str) -> Optional[str]:
    """Return the first supported video URL found in text, or None."""
    m = _VIDEO_URL_RE.search(text)
    return m.group(0) if m else None


# ─── Download Logic ───────────────────────────────────────────────────────────

async def _download(url: str, output_dir: str) -> tuple[Optional[str], str]:
    """
    Download a video with yt-dlp into output_dir.

    Returns: (filepath, title)        on success
             (None, error_message)    on failure
    """
    try:
        import yt_dlp
        logger.info("yt-dlp version: %s", yt_dlp.version.__version__)
    except ImportError:
        return None, (
            "yt-dlp is not installed.\n"
            "Please add <code>yt-dlp</code> to requirements.txt and redeploy."
        )

    # Log cookies file status so we can confirm it is being picked up
    if COOKIES_PATH:
        exists = os.path.isfile(COOKIES_PATH)
        size = os.path.getsize(COOKIES_PATH) if exists else 0
        logger.info(
            "Cookies file: path=%s exists=%s size=%d bytes",
            COOKIES_PATH, exists, size,
        )
    else:
        logger.info("Cookies file: not configured (YT_COOKIES_FILE not set)")

    cookies_opt = {}
    if COOKIES_PATH and os.path.isfile(COOKIES_PATH):
        cookies_opt = {"cookiefile": COOKIES_PATH}
        logger.info("Passing cookiefile to yt-dlp: %s", COOKIES_PATH)
    else:
        logger.warning(
            "Cookies file not found at '%s' – downloading without authentication. "
            "YouTube may reject the request on datacenter IPs.",
            COOKIES_PATH,
        )

    ydl_opts = {
        # Best quality up to MAX_HEIGHT, merged into a single MP4
        "format": (
            f"bestvideo[height<={MAX_HEIGHT}][ext=mp4]+bestaudio[ext=m4a]"
            f"/bestvideo[height<={MAX_HEIGHT}]+bestaudio"
            f"/best[height<={MAX_HEIGHT}]"
            "/best"
        ),
        "outtmpl": os.path.join(output_dir, "%(title).80s.%(ext)s"),
        "merge_output_format": "mp4",
        "quiet": False,   # set to False so yt-dlp output appears in journald
        "no_warnings": False,
        "noplaylist": True,       # single video only, never entire playlists
        "max_filesize": MAX_FILE_SIZE_BYTES,
        "verbose": True,          # full yt-dlp debug output in journald
        **cookies_opt,
        # Use the web client with the bgutil PO token provider.
        # YouTube now requires a GVS PO Token bound to each video on datacenter IPs.
        # bgutil-ytdlp-pot-provider runs a local Node.js server (port 4416) that
        # generates valid PO tokens; yt-dlp-get-pot picks them up automatically.
        "extractor_args": {
            "youtube": {
                "player_client": ["web"],
            }
        },
        # Point the get-pot plugin at the local bgutil server started in the container
        "pot_bgutil_server_url": "http://localhost:4416",
    }

    logger.info("yt-dlp opts (excluding cookies content): %s", {
        k: v for k, v in ydl_opts.items() if k != "cookiefile"
    })

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            logger.info("Starting extraction for URL: %s", url)
            info = ydl.extract_info(url, download=True)
            title = info.get("title", "Video")
            logger.info("Extraction complete, title: %s", title)
            # Find the downloaded file in the temp directory
            files = list(Path(output_dir).iterdir())
            logger.info("Files in output dir: %s", [str(f) for f in files])
            for f in files:
                if f.is_file():
                    logger.info("Using file: %s (%d bytes)", f, f.stat().st_size)
                    return str(f), title
            return None, "Download finished but file not found."
    except yt_dlp.utils.DownloadError as exc:
        logger.error("yt-dlp DownloadError: %s", exc)
        return None, str(exc)
    except Exception as exc:
        logger.exception("Unexpected error during download")
        return None, f"Unexpected error: {exc}"


# ─── Telegram Handler ─────────────────────────────────────────────────────────

async def handle_video_url(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Fires when a private message contains a supported video URL.

    Flow:
      1. Send a status message immediately to acknowledge the request
      2. Download the video via yt-dlp into a temp directory
      3. Send the file back to the user
      4. Delete the status message on success
    """
    message = update.message
    if not message or not message.text:
        return

    url = _find_url(message.text)
    if not url:
        return  # guard against filter false-positives

    user = message.from_user
    logger.info(
        "Video download requested by %s (id=%s): %s",
        user.username or user.first_name,
        user.id,
        url,
    )

    # Acknowledge the request right away so the user knows something is happening
    status = await message.reply_text(
        f"⬇️ <b>Downloading video…</b>\n<code>{url}</code>",
        parse_mode=ParseMode.HTML,
    )
    await message.chat.send_chat_action(ChatAction.UPLOAD_VIDEO)

    with tempfile.TemporaryDirectory() as tmp:
        filepath, title_or_err = await _download(url, tmp)

        if filepath is None:
            logger.warning("Download failed for %s: %s", url, title_or_err)
            await status.edit_text(
                f"❌ <b>Download failed</b>\n\n<code>{title_or_err}</code>",
                parse_mode=ParseMode.HTML,
            )
            return

        size_bytes = os.path.getsize(filepath)
        size_mb = size_bytes / 1024 / 1024

        if size_bytes > MAX_FILE_SIZE_BYTES:
            await status.edit_text(
                f"❌ <b>File too large for Telegram</b>\n\n"
                f"{size_mb:.1f} MB &gt; {MAX_FILE_SIZE_MB} MB limit.\n"
                f"Try a shorter clip.",
                parse_mode=ParseMode.HTML,
            )
            return

        await status.edit_text("📤 <b>Sending video…</b>", parse_mode=ParseMode.HTML)
        await message.chat.send_chat_action(ChatAction.UPLOAD_VIDEO)

        try:
            with open(filepath, "rb") as fh:
                await message.reply_video(
                    video=fh,
                    caption=f"🎬 <b>{title_or_err}</b>",
                    parse_mode=ParseMode.HTML,
                    supports_streaming=True,
                    read_timeout=180,
                    write_timeout=180,
                )
            await status.delete()
            logger.info("Video sent successfully (%.1f MB): %s", size_mb, title_or_err)

        except Exception as exc:
            logger.error("Sending failed: %s", exc)
            await status.edit_text(
                f"❌ <b>Sending failed</b>\n\n<code>{exc}</code>",
                parse_mode=ParseMode.HTML,
            )
            # Report into the project's existing error infrastructure
            try:
                error_logger = get_error_logger()
                await error_logger.log_error(exc, f"video_downloader – send to user {user.id}")
            except Exception:
                pass


# ─── Registration ─────────────────────────────────────────────────────────────

def register_video_downloader(app: Application) -> None:
    """
    Register the video downloader handler for private chats.

    Call in main.py:
        from private.video_downloader import register_video_downloader
        register_video_downloader(application)
    """
    app.add_handler(
        MessageHandler(
            filters.TEXT & filters.ChatType.PRIVATE & filters.Regex(_VIDEO_URL_RE),
            handle_video_url,
        ),
    )
    logger.info("Video downloader handler registered (private chats).")
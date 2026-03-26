import re
import logging
from telegram import Update
from telegram.ext import ContextTypes, MessageHandler, filters
from util.downloader import download_media, cleanup_files
from settings.config import ADMINS

logger = logging.getLogger(__name__)

# Pattern to match supported URLs
SOCIAL_MEDIA_PATTERN = re.compile(
    r'(https?://(?:www\.)?(?:twitter\.com|x\.com|instagram\.com|youtube\.com|youtu\.be)/\S+)',
    re.IGNORECASE
)

async def handle_social_media_links(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Detects social media links in messages and downloads the media.
    Works for admins in private chats or in groups where the bot is.
    """
    message = update.message or update.edited_message
    if not message or not message.text:
        return

    # Check if admin (if private chat) or in group
    is_private = message.chat.type == 'private'
    is_admin = message.from_user.id in ADMINS

    # We download if:
    # 1. Admin sends in private chat
    # 2. Admin sends in a group (to help with posting)
    # 3. Anyone sends in a group (might be useful, but let's restrict to admins for now to avoid spam/bandwidth issues)
    if not is_admin:
        return

    links = SOCIAL_MEDIA_PATTERN.findall(message.text)
    if not links:
        return

    for link in links:
        try:
            status_msg = await message.reply_text(f"📥 Erkenne Link: {link}\nVersuche Medium herunterzuladen...")
            
            files = await download_media(link)
            
            if files:
                for f in files:
                    try:
                        with open(f, 'rb') as media_file:
                            if f.lower().endswith(('.mp4', '.mkv', '.mov')):
                                await message.reply_video(video=media_file, caption=f"🎥 Heruntergeladen von {link}")
                            elif f.lower().endswith(('.jpg', '.jpeg', '.png', '.webp')):
                                await message.reply_photo(photo=media_file, caption=f"🖼️ Heruntergeladen von {link}")
                            else:
                                await message.reply_document(document=media_file, caption=f"📎 Datei von {link}")
                    except Exception as e:
                        logger.error(f"Error sending file {f}: {e}")
                
                cleanup_files(files)
                await status_msg.delete()
            else:
                await status_msg.edit_text(f"❌ Download fehlgeschlagen oder Medium zu groß für {link}")
        
        except Exception as e:
            logger.error(f"Error handling link {link}: {e}")

def register_media_downloader(application):
    # Only for admins to prevent abuse
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_social_media_links))

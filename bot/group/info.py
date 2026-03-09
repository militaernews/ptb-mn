import logging
from telegram import Update
from telegram.ext import ContextTypes, CommandHandler, filters
from data.db import get_user_stats, get_warnings
from settings.config import GERMAN

logger = logging.getLogger(__name__)

async def show_user_info(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show karma, warnings, message count and join date for a user."""
    message = update.message
    if not message:
        return

    # Check if we are in MNChat (German)
    if message.chat_id != GERMAN.chat_id:
        return

    # Determine target user
    if message.reply_to_message:
        target_user = message.reply_to_message.from_user
    else:
        target_user = message.from_user

    if not target_user or target_user.is_bot:
        return

    # Get stats from DB
    stats = await get_user_stats(target_user.id, message.chat_id)
    warn_count = await get_warnings(target_user.id, message.chat_id)

    if not stats:
        # Initialize if not present (this should rarely happen if tracking is active)
        from data.db import update_user_stats
        await update_user_stats(target_user.id, message.chat_id)
        stats = await get_user_stats(target_user.id, message.chat_id)

    # Format the info message
    join_date = stats['joined_at'].strftime('%d.%m.%Y')
    
    text = (
        f"👤 <b>Nutzer-Info: {target_user.mention_html()}</b>\n\n"
        f"📊 <b>Statistiken:</b>\n"
        f"✨ Karma: <code>{stats['karma']}</code>\n"
        f"💬 Nachrichten: <code>{stats['message_count']}</code>\n"
        f"⚠️ Verwarnungen: <code>{warn_count}</code>\n"
        f"📅 Mitglied seit: <code>{join_date}</code>"
    )

    await message.reply_text(text, parse_mode="HTML")

def register_info_command(application):
    application.add_handler(CommandHandler("info", show_user_info, filters.Chat(GERMAN.chat_id)))

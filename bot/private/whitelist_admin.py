import logging
from telegram import Update
from telegram.ext import ContextTypes, CommandHandler, MessageHandler, filters
from data.db import get_whitelist, add_whitelist, remove_whitelist
from settings.config import ADMINS

logger = logging.getLogger(__name__)

async def show_whitelist_admin(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show the current whitelist to admins in private chat."""
    if update.effective_user.id not in ADMINS:
        return

    links = await get_whitelist()
    if not links:
        await update.message.reply_text("Die Whitelist ist aktuell leer.")
    else:
        text = "📋 <b>Aktuelle Whitelist:</b>\n\n"
        for i, link in enumerate(links, 1):
            text += f"{i}. <code>{link}</code>\n"
        text += "\nVerwende <code>/add_whitelist [link]</code> oder <code>/remove_whitelist [link]</code> zum Bearbeiten."
        await update.message.reply_text(text, parse_mode="HTML")

async def add_to_whitelist(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Add a link to the whitelist."""
    if update.effective_user.id not in ADMINS:
        return

    if not context.args:
        await update.message.reply_text("Bitte gib einen Link oder eine Domain an: <code>/add_whitelist [link]</code>", parse_mode="HTML")
        return

    link = context.args[0].lower().strip()
    await add_whitelist(link)
    await update.message.reply_text(f"✅ <code>{link}</code> wurde zur Whitelist hinzugefügt.", parse_mode="HTML")

async def remove_from_whitelist(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Remove a link from the whitelist."""
    if update.effective_user.id not in ADMINS:
        return

    if not context.args:
        await update.message.reply_text("Bitte gib den Link an, der entfernt werden soll: <code>/remove_whitelist [link]</code>", parse_mode="HTML")
        return

    link = context.args[0].lower().strip()
    await remove_whitelist(link)
    await update.message.reply_text(f"🗑️ <code>{link}</code> wurde von der Whitelist entfernt.", parse_mode="HTML")

def register_whitelist_admin(application):
    # Private chat only for these commands
    application.add_handler(CommandHandler("whitelist_admin", show_whitelist_admin, filters.ChatType.PRIVATE))
    application.add_handler(CommandHandler("add_whitelist", add_to_whitelist, filters.ChatType.PRIVATE))
    application.add_handler(CommandHandler("remove_whitelist", remove_from_whitelist, filters.ChatType.PRIVATE))

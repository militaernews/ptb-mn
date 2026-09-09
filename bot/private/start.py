import logging

from telegram import Update
from telegram.ext import Application, CommandHandler, ChatMemberHandler, ContextTypes
from telegram.helpers import mention_html

from settings.config import ADMINS, LOG_GROUP, THREAD_ID

REQUIRED_CHANNEL_PERMISSIONS = ("post_messages", "edit_messages")


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Start command handler for users who message the bot directly."""
    await update.message.reply_text(
        "🤖 Ich veröffentliche automatisch Beiträge in den MilitaerNews-Kanälen und habe "
        "keine interaktiven Befehle für den privaten Chat."
    )


async def handle_my_chat_member(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Notify LOG_GROUP whenever the bot's own status changes in a channel, so the
    team notices right away if it's missing the posting/editing rights it needs.
    """
    result = update.my_chat_member
    old_status = result.old_chat_member.status
    new_status = result.new_chat_member.status
    if old_status == new_status:
        return

    chat = result.chat
    mentions = "".join(mention_html(admin_id, "​") for admin_id in ADMINS)

    if new_status == "administrator":
        member = result.new_chat_member
        missing = [p for p in REQUIRED_CHANNEL_PERMISSIONS if not getattr(member, f"can_{p}", False)]
        if not missing:
            return
        text = (
            f"{mentions}⚠️ Ich bin jetzt Admin in <b>{chat.title or chat.id}</b>, aber mir fehlen:\n"
            + "\n".join(f"• can_{p}" for p in missing)
        )
    elif new_status == "member":
        text = (
            f"{mentions}👋 Ich wurde zu <b>{chat.title or chat.id}</b> hinzugefügt, bin dort aber kein Admin. "
            f"Ich benötige die Rechte {', '.join(f'can_{p}' for p in REQUIRED_CHANNEL_PERMISSIONS)}, "
            "um Beiträge zu veröffentlichen."
        )
    elif new_status in ("left", "kicked"):
        text = f"{mentions}🚪 Ich wurde aus <b>{chat.title or chat.id}</b> entfernt."
    else:
        return

    try:
        await context.bot.send_message(LOG_GROUP, text, message_thread_id=THREAD_ID)
    except Exception as e:
        logging.error(f"Could not report chat-member update for {chat.id}: {e}")


def register_start(app: Application):
    app.add_handler(CommandHandler("start", start))
    app.add_handler(ChatMemberHandler(handle_my_chat_member, ChatMemberHandler.MY_CHAT_MEMBER))

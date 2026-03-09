import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, MessageHandler, CallbackQueryHandler, filters
from data.db import get_warnings, increment_warnings, reset_warnings
from settings.config import ADMINS, GERMAN

logger = logging.getLogger(__name__)

async def handle_admin_mention(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Detect @admin mention and show warn/ban buttons if replying to a message."""
    message = update.message
    if not message or not message.text or "@admin" not in message.text.lower():
        return

    if not message.reply_to_message:
        return

    replied_user = message.reply_to_message.from_user
    if not replied_user or replied_user.is_bot:
        return

    # Check current warnings
    warn_count = await get_warnings(replied_user.id, message.chat_id)

    keyboard = [
        [
            InlineKeyboardButton(f"⚠️ Warnen ({warn_count})", callback_data=f"warn_{replied_user.id}_{message.reply_to_message.id}"),
            InlineKeyboardButton("🚫 Sperren (Ban)", callback_data=f"ban_{replied_user.id}_{message.reply_to_message.id}")
        ],
        [InlineKeyboardButton("❌ Abbrechen", callback_data=f"cancel_admin_action")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await message.reply_text(
        f"🛡️ <b>Admin-Aktion für {replied_user.mention_html()}</b>\n"
        f"Aktuelle Verwarnungen: {warn_count}",
        reply_markup=reply_markup,
        parse_mode="HTML"
    )

async def admin_action_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle the button clicks for warn/ban."""
    query = update.callback_query
    user_id = query.from_user.id

    # Check if the person clicking is an admin
    if user_id not in ADMINS:
        # Check if they are a chat admin if not in global ADMINS
        chat_admins = [admin.user.id for admin in await context.bot.get_chat_administrators(query.message.chat_id)]
        if user_id not in chat_admins:
            await query.answer("❌ Nur Admins können diese Aktion ausführen!", show_alert=True)
            return

    data = query.data
    if data == "cancel_admin_action":
        await query.message.delete()
        await query.answer("Aktion abgebrochen.")
        return

    action, target_user_id, target_msg_id = data.split("_")
    target_user_id = int(target_user_id)
    target_msg_id = int(target_msg_id)
    chat_id = query.message.chat_id

    try:
        if action == "warn":
            new_count = await increment_warnings(target_user_id, chat_id)
            await query.answer(f"Nutzer verwarnt. Neue Anzahl: {new_count}", show_alert=True)
            
            # Send notification message
            await context.bot.send_message(
                chat_id,
                f"⚠️ {target_user_id} wurde verwarnt. (Gesamt: {new_count})"
            )
            
            # Auto-ban after 3 warnings? (Optional, but good practice)
            if new_count >= 3:
                await context.bot.ban_chat_member(chat_id, target_user_id)
                await context.bot.send_message(chat_id, f"🚫 {target_user_id} wurde nach 3 Verwarnungen automatisch gesperrt.")
                await reset_warnings(target_user_id, chat_id)

        elif action == "ban":
            await context.bot.ban_chat_member(chat_id, target_user_id)
            await query.answer("Nutzer wurde dauerhaft gesperrt.", show_alert=True)
            await context.bot.send_message(chat_id, f"🚫 Nutzer wurde gesperrt.")
            await reset_warnings(target_user_id, chat_id)

        # Remove the message with buttons after action
        await query.message.delete()

    except Exception as e:
        logger.error(f"Admin action failed: {e}")
        await query.answer(f"❌ Fehler: {e}", show_alert=True)

def register_admin_actions(application):
    # Handle @admin mention
    application.add_handler(MessageHandler(filters.Chat(GERMAN.chat_id) & filters.TEXT & ~filters.COMMAND, handle_admin_mention))
    # Handle button callbacks
    application.add_handler(CallbackQueryHandler(admin_action_callback, pattern="^(warn_|ban_|cancel_admin_action)"))

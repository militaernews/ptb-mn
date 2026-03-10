import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.error import BadRequest
from telegram.ext import ContextTypes, MessageHandler, CallbackQueryHandler, filters
from data.db import get_warnings, increment_warnings, decrement_warnings, reset_warnings
from settings.config import ADMINS
from data.lang import GERMAN
from util.helper import remove_reply

logger = logging.getLogger(__name__)

def get_admin_keyboard(user_id: int, chat_id: int, warn_count: int, target_msg_id: int):
    keyboard = [
        [
            InlineKeyboardButton(f"⚠️ Warnen ({warn_count})", callback_data=f"warn_{user_id}_{target_msg_id}"),
            InlineKeyboardButton(f"✅ Entwarnen", callback_data=f"unwarn_{user_id}_{target_msg_id}")
        ],
        [
            InlineKeyboardButton("🚫 Sperren (Ban)", callback_data=f"ban_{user_id}_{target_msg_id}"),
            InlineKeyboardButton("❌ Abbrechen", callback_data=f"cancel_admin_action")
        ]
    ]
    return InlineKeyboardMarkup(keyboard)

@remove_reply
async def handle_admin_mention(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Detect @admin mention and show warn/ban buttons if replying to a message."""
    message = update.message
    if not message or not message.text or "@admin" not in message.text.lower():
        return

    if not message.reply_to_message:
        return

    replied_user = message.reply_to_message.from_user
    # Don't show buttons for bots or if replying to an admin
    if not replied_user or replied_user.is_bot or replied_user.id in ADMINS:
        return

    # Check current warnings
    warn_count = await get_warnings(replied_user.id, message.chat_id)
    reply_markup = get_admin_keyboard(replied_user.id, message.chat_id, warn_count, message.reply_to_message.id)

    # Send the admin-action message. We use send_message instead of reply_text because
    # the @admin message itself is deleted by the remove_reply decorator before this point,
    # which would cause a "Message to be replied not found" BadRequest error.
    try:
        await context.bot.send_message(
            chat_id=message.chat_id,
            text=(
                f"🛡️ <b>Admin-Aktion für {replied_user.mention_html()}</b>\n"
                f"Aktuelle Verwarnungen: {warn_count}"
            ),
            reply_markup=reply_markup,
            parse_mode="HTML",
            reply_to_message_id=message.reply_to_message.message_id,
        )
    except BadRequest:
        # Fallback: reply_to_message was deleted – send without quote
        await context.bot.send_message(
            chat_id=message.chat_id,
            text=(
                f"🛡️ <b>Admin-Aktion für {replied_user.mention_html()}</b>\n"
                f"Aktuelle Verwarnungen: {warn_count}"
            ),
            reply_markup=reply_markup,
            parse_mode="HTML",
        )

async def admin_action_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle the button clicks for warn/ban/unwarn."""
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

    parts = data.split("_")
    if len(parts) != 3:
        await query.answer("Fehlerhaftes Callback-Datenformat.")
        return
        
    action, target_user_id, target_msg_id = parts
    target_user_id = int(target_user_id)
    target_msg_id = int(target_msg_id)
    chat_id = query.message.chat_id

    try:
        if action == "warn":
            new_count = await increment_warnings(target_user_id, chat_id)
            await query.answer(f"Nutzer verwarnt. Neue Anzahl: {new_count}")
            
            # Update the existing message instead of sending a new one
            # Get user mention for the message (we can try to get it from the text or context if needed, 
            # but usually we can just update the count in the text)
            # To keep it simple, we re-fetch or use the existing text structure.
            # We need the user's mention. Since we don't have the User object easily, 
            # we can parse it from the existing message text or just use the ID if necessary.
            # However, handle_admin_mention uses mention_html.
            
            # For a better UX, we just update the keyboard and the warning count in the message.
            current_text = query.message.text_html
            # Simple replacement of the count if we can find it, or just rebuild.
            # Since we want to be safe, let's just update the keyboard first.
            
            new_keyboard = get_admin_keyboard(target_user_id, chat_id, new_count, target_msg_id)
            
            # Try to update the text to reflect the new count
            new_text = f"🛡️ <b>Admin-Aktion</b>\nAktuelle Verwarnungen: {new_count}"
            # Note: We lost the mention_html() here unless we extract it. 
            # Let's try to keep the first line of the original message.
            lines = current_text.split("\n")
            if len(lines) > 0:
                new_text = f"{lines[0]}\nAktuelle Verwarnungen: {new_count}"

            await query.edit_message_text(
                text=new_text,
                reply_markup=new_keyboard,
                parse_mode="HTML"
            )

            # Auto-ban after 3 warnings
            if new_count >= 3:
                await context.bot.ban_chat_member(chat_id, target_user_id)
                await context.bot.send_message(chat_id, f"🚫 Nutzer ID {target_user_id} wurde nach 3 Verwarnungen automatisch gesperrt.")
                await reset_warnings(target_user_id, chat_id)
                await query.message.delete()

        elif action == "unwarn":
            new_count = await decrement_warnings(target_user_id, chat_id)
            await query.answer(f"Verwarnung entfernt. Neue Anzahl: {new_count}")
            
            current_text = query.message.text_html
            lines = current_text.split("\n")
            new_text = f"{lines[0]}\nAktuelle Verwarnungen: {new_count}"
            
            new_keyboard = get_admin_keyboard(target_user_id, chat_id, new_count, target_msg_id)
            await query.edit_message_text(
                text=new_text,
                reply_markup=new_keyboard,
                parse_mode="HTML"
            )

        elif action == "ban":
            await context.bot.ban_chat_member(chat_id, target_user_id)
            await query.answer("Nutzer wurde dauerhaft gesperrt.", show_alert=True)
            await context.bot.send_message(chat_id, f"🚫 Nutzer wurde gesperrt.")
            await reset_warnings(target_user_id, chat_id)
            await query.message.delete()

    except Exception as e:
        logger.error(f"Admin action failed: {e}")
        await query.answer(f"❌ Fehler: {e}", show_alert=True)

def register_admin_actions(application):
    # Handle @admin mention
    application.add_handler(MessageHandler(filters.Chat(GERMAN.chat_id) & filters.TEXT & ~filters.COMMAND, handle_admin_mention))
    # Handle button callbacks
    application.add_handler(CallbackQueryHandler(admin_action_callback, pattern="^(warn_|unwarn_|ban_|cancel_admin_action)"))

import logging
from typing import Optional, Tuple
from telegram import Update, ChatMember, ChatMemberUpdated, User
from telegram.ext import ContextTypes, ChatMemberHandler
from settings.config import PROTOCOL_CHAT
from data.lang import GERMAN

logger = logging.getLogger(__name__)

def extract_status_change(chat_member_update: ChatMemberUpdated) -> Optional[Tuple[bool, bool]]:
    """Extracts whether the user joined or left the chat."""
    status_change = chat_member_update.difference().get("status")
    old_is_member, new_is_member = chat_member_update.difference().get("is_member", (None, None))

    if status_change is None:
        return None

    old_status, new_status = status_change
    was_member = old_status in [ChatMember.MEMBER, ChatMember.ADMINISTRATOR, ChatMember.OWNER] or old_is_member is True
    is_member = new_status in [ChatMember.MEMBER, ChatMember.ADMINISTRATOR, ChatMember.OWNER] or new_is_member is True

    return was_member, is_member

async def log_to_protocol(context: ContextTypes.DEFAULT_TYPE, text: str):
    """Sends a message to the protocol chat."""
    if not PROTOCOL_CHAT:
        return
    try:
        await context.bot.send_message(chat_id=PROTOCOL_CHAT, text=text, parse_mode="HTML")
    except Exception as e:
        logger.error(f"Failed to send protocol message: {e}")

async def chat_member_update(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle chat member updates (join/leave and admin changes)."""
    result = extract_status_change(update.chat_member)
    if result is None:
        return

    was_member, is_member = result
    cause_user = update.chat_member.from_user
    target_user = update.chat_member.new_chat_member.user

    # Join/Leave
    if not was_member and is_member:
        await log_to_protocol(context, f"📥 <b>Beitritt:</b> {target_user.mention_html()} (ID: <code>{target_user.id}</code>)")
    elif was_member and not is_member:
        await log_to_protocol(context, f"📤 <b>Austritt/Entfernung:</b> {target_user.mention_html()} (ID: <code>{target_user.id}</code>)")

    # Admin actions (Promote/Demote/Ban/Unban)
    old_status = update.chat_member.old_chat_member.status
    new_status = update.chat_member.new_chat_member.status

    if old_status != new_status:
        action_text = None
        if new_status == ChatMember.ADMINISTRATOR:
            action_text = f"👮 <b>Beförderung:</b> {target_user.mention_html()} wurde von {cause_user.mention_html()} zum Admin ernannt."
        elif old_status == ChatMember.ADMINISTRATOR and new_status in [ChatMember.MEMBER, ChatMember.RESTRICTED]:
            action_text = f"📉 <b>Degradierung:</b> {target_user.mention_html()} wurde von {cause_user.mention_html()} als Admin entfernt."
        elif new_status == ChatMember.BANNED:
            action_text = f"🚫 <b>Bann:</b> {target_user.mention_html()} wurde von {cause_user.mention_html()} gebannt."
        elif old_status == ChatMember.BANNED and new_status != ChatMember.BANNED:
            action_text = f"🔓 <b>Entbannung:</b> {target_user.mention_html()} wurde von {cause_user.mention_html()} entbannt."

        if action_text:
            await log_to_protocol(context, action_text)

async def log_admin_action(context: ContextTypes.DEFAULT_TYPE, admin: User, target_user_id: int, action: str, details: str = ""):
    """Manually log an admin action (e.g. from bot buttons)."""
    action_emoji = {
        "warn": "⚠️",
        "unwarn": "✅",
        "ban": "🚫",
        "restrict": "🔇"
    }.get(action, "🛠")
    
    text = f"{action_emoji} <b>Admin-Aktion ({action}):</b>\nAdmin: {admin.mention_html()}\nZiel-ID: <code>{target_user_id}</code>"
    if details:
        text += f"\nDetails: {details}"
    
    await log_to_protocol(context, text)

def register_protocol(application):
    # Only register if PROTOCOL_CHAT is set
    if PROTOCOL_CHAT:
        application.add_handler(ChatMemberHandler(chat_member_update, chat_member_types=ChatMemberHandler.CHAT_MEMBER))

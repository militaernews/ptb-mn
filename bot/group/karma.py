import logging
from telegram import Update
from telegram.ext import ContextTypes, MessageHandler, filters, ChatMemberHandler, MessageReactionHandler
from data.db import update_user_stats, log_user_event, save_message_author, get_message_author
from data.lang import GERMAN

logger = logging.getLogger(__name__)

# Emoji to Karma mappings
KARMA_PLUS = {"👍", "❤️"}
KARMA_MINUS = {"👎", "💩", "🤡"}

async def handle_message_stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Increment message count for a user and save message author."""
    if not update.message or not update.message.from_user or update.message.from_user.is_bot:
        return

    # Only track in MNChat (German)
    if update.message.chat_id != GERMAN.chat_id:
        return

    user_id = update.message.from_user.id
    chat_id = update.message.chat_id
    message_id = update.message.message_id

    # Save author for reaction tracking
    await save_message_author(message_id, chat_id, user_id)
    
    # Increment message count
    await update_user_stats(user_id, chat_id, msg_delta=1)

async def handle_reaction_karma(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Track karma changes based on message reactions."""
    reaction = update.message_reaction
    if not reaction:
        return

    # Only track in MNChat (German)
    if reaction.chat.id != GERMAN.chat_id:
        return

    chat_id = reaction.chat.id
    message_id = reaction.message_id

    # Get the user whose message was reacted to from our DB
    target_user_id = await get_message_author(message_id, chat_id)
    if not target_user_id:
        return

    # Calculate karma delta
    delta = 0
    
    # Check new reactions
    for r in reaction.new_reaction:
        emoji = getattr(r, 'emoji', None)
        if emoji in KARMA_PLUS:
            delta += 1
        elif emoji in KARMA_MINUS:
            delta -= 1
    
    # Check old reactions (to subtract if removed)
    for r in reaction.old_reaction:
        emoji = getattr(r, 'emoji', None)
        if emoji in KARMA_PLUS:
            delta -= 1
        elif emoji in KARMA_MINUS:
            delta += 1

    if delta != 0:
        # Don't let users give themselves karma
        if reaction.user and reaction.user.id == target_user_id:
            return
            
        await update_user_stats(target_user_id, chat_id, karma_delta=delta)
        logger.info(f"Karma for user {target_user_id} changed by {delta} in chat {chat_id}")

async def handle_chat_member_update(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Log when a member joins or leaves the chat."""
    result = update.chat_member
    if not result or result.chat.id != GERMAN.chat_id:
        return

    user_id = result.new_chat_member.user.id
    old_status = result.old_chat_member.status
    new_status = result.new_chat_member.status

    # Join events
    if old_status in ('left', 'kicked') and new_status in ('member', 'administrator'):
        await log_user_event(user_id, result.chat.id, 'joined')
        # update_user_stats with 0 deltas will create the record with joined_at = now() if it doesn't exist
        await update_user_stats(user_id, result.chat.id)
        logger.info(f"User {user_id} joined chat {result.chat.id}")

    # Leave/Kick/Ban events
    elif old_status in ('member', 'administrator') and new_status in ('left', 'kicked'):
        event_type = 'left' if new_status == 'left' else 'kicked'
        await log_user_event(user_id, result.chat.id, event_type)
        logger.info(f"User {user_id} {event_type} chat {result.chat.id}")

def register_karma_tracking(application):
    # Track messages
    application.add_handler(MessageHandler(filters.Chat(GERMAN.chat_id) & ~filters.COMMAND, handle_message_stats))
    # Track reactions
    application.add_handler(MessageReactionHandler(handle_reaction_karma))
    # Track joins and leaves
    application.add_handler(ChatMemberHandler(handle_chat_member_update, ChatMemberHandler.CHAT_MEMBER))

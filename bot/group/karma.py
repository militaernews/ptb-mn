import logging
from telegram import Update
from telegram.ext import ContextTypes, MessageHandler, filters, ChatMemberHandler
from data.db import update_user_stats, log_user_event
from data.lang import GERMAN

logger = logging.getLogger(__name__)

# Emoji to Karma mappings
KARMA_PLUS = {"👍", "❤️", "🔥", "👏", "🥰", "⚡", "🤩"}
KARMA_MINUS = {"👎", "💩", "🤡", "🤮", "😡", "😱"}

async def handle_message_stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Increment message count for a user in MNChat."""
    if not update.message or not update.message.from_user or update.message.from_user.is_bot:
        return

    # Only track in MNChat (German)
    if update.message.chat_id != GERMAN.chat_id:
        return

    await update_user_stats(update.message.from_user.id, update.message.chat_id, msg_delta=1)

async def handle_reaction_karma(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Track karma changes based on message reactions."""
    reaction = update.message_reaction
    if not reaction:
        return

    # Only track in MNChat (German)
    if reaction.chat.id != GERMAN.chat_id:
        return

    # Get the user whose message was reacted to
    # Note: Telegram doesn't directly provide the message author in MessageReactionUpdated
    # unless we have it cached or fetch the message.
    try:
        message = await context.bot.get_message(reaction.chat.id, reaction.message_id)
        if not message or not message.from_user or message.from_user.is_bot:
            return
        
        target_user_id = message.from_user.id
        
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
            await update_user_stats(target_user_id, reaction.chat.id, karma_delta=delta)
            
    except Exception as e:
        logger.error(f"Error tracking reaction karma: {e}")

async def handle_chat_member_update(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Log when a member joins or leaves the chat."""
    result = update.chat_member
    if not result or result.chat.id != GERMAN.chat_id:
        return

    user_id = result.from_user.id
    old_status = result.old_chat_member.status
    new_status = result.new_chat_member.status

    # Join events
    if old_status in ('left', 'kicked') and new_status == 'member':
        await log_user_event(user_id, result.chat.id, 'joined')
        # update_user_stats with 0 deltas will create the record with joined_at = now() if it doesn't exist
        await update_user_stats(user_id, result.chat.id)
        logger.info(f"User {user_id} joined chat {result.chat.id}")

    # Leave/Kick/Ban events
    elif old_status == 'member' and new_status in ('left', 'kicked', 'kicked'):
        event_type = 'left' if new_status == 'left' else 'kicked'
        await log_user_event(user_id, result.chat.id, event_type)
        logger.info(f"User {user_id} {event_type} chat {result.chat.id}")

def register_karma_tracking(application):
    # Track messages
    application.add_handler(MessageHandler(filters.Chat(GERMAN.chat_id) & ~filters.COMMAND, handle_message_stats))
    # Track reactions
    # application.add_handler(MessageReactionHandler(handle_reaction_karma)) # Not available in current PTB version?
    # PTB 22.x uses MessageReactionHandler, let's check if it exists or use raw update
    from telegram.ext import MessageReactionHandler
    application.add_handler(MessageReactionHandler(handle_reaction_karma))
    # Track joins and leaves
    application.add_handler(ChatMemberHandler(handle_chat_member_update, ChatMemberHandler.CHAT_MEMBER))

"""
Run the news pipeline (footer, translations, cross-posting, tweets) for posts
that other bots - currently ptb-suggest - published directly to the GERMAN
channel.

Telegram never delivers a bot's messages to other bots, so those posts never
reach register_news's handlers on their own. ptb-suggest instead records the
channel message ID in the shared channel_handoff table; this job picks it up,
forwards the post into the log group to get a Message (with file IDs this bot
can reuse), rebuilds it as the original channel post and feeds it through the
regular handlers via process_update - exactly as if it had arrived as an
update.
"""
import logging

from telegram import Message, Update
from telegram.error import TelegramError
from telegram.ext import Application, ContextTypes

from data.db import handoff_get_pending, handoff_mark_processed
from data.lang import GERMAN
from settings.config import LOG_GROUP_ID, THREAD_ID
from util.error_logger import get_error_logger

logger = logging.getLogger(__name__)

POLL_INTERVAL_SECONDS = 15

# Fields describing the forward itself - dropped so the rebuilt message looks
# like a plain channel post (register_news filters out forwarded posts).
_FORWARD_FIELDS = ("forward_origin", "is_automatic_forward", "message_thread_id", "is_topic_message",
                   "reply_to_message", "from")


async def process_channel_post(application: Application, message: Message) -> None:
    """Feed a GERMAN-channel post through register_news's handlers."""
    await application.process_update(Update(update_id=0, channel_post=message))


async def _rebuild_channel_post(context: ContextTypes.DEFAULT_TYPE, message_id: int) -> Message:
    forwarded = await context.bot.forward_message(
        chat_id=LOG_GROUP_ID,
        message_thread_id=THREAD_ID,
        from_chat_id=GERMAN.channel_id,
        message_id=message_id,
        disable_notification=True,
    )
    try:
        data = forwarded.to_dict()
        origin = forwarded.forward_origin
        for field in _FORWARD_FIELDS:
            data.pop(field, None)
        data["message_id"] = message_id
        data["chat"] = origin.chat.to_dict()
        data["sender_chat"] = origin.chat.to_dict()
        data["date"] = int(origin.date.timestamp())
        return Message.de_json(data, context.bot)
    finally:
        try:
            await forwarded.delete()
        except TelegramError as e:
            logger.warning(f"[handoff] Could not delete helper forward: {e}")


async def process_handoffs(context: ContextTypes.DEFAULT_TYPE) -> None:
    for message_id in await handoff_get_pending():
        # Mark first so a post that keeps failing doesn't get re-run (and
        # re-translated/cross-posted) every POLL_INTERVAL_SECONDS.
        await handoff_mark_processed(message_id)
        try:
            message = await _rebuild_channel_post(context, message_id)
            await process_channel_post(context.application, message)
            logger.info(f"[handoff] Processed channel post {message_id}")
        except Exception as e:
            logger.error(f"[handoff] Failed to process channel post {message_id}: {e}")
            await get_error_logger().log_error(e, f"[handoff] channel post {message_id}")


def register_handoff(application: Application) -> None:
    application.job_queue.run_repeating(
        process_handoffs, interval=POLL_INTERVAL_SECONDS, first=20, name="process_handoffs")
    logger.info(f"[handoff] Polling channel_handoff every {POLL_INTERVAL_SECONDS}s")

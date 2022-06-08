from telegram import Update  #upm package(python-telegram-bot)
from telegram.ext import CallbackContext  #upm package(python-telegram-bot)
import logging
import config

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO)
logger = logging.getLogger(__name__)


def log(update: Update, context: CallbackContext, message: str):
    logger.info(message)
    context.bot.send_message(config.LOG_GROUP, message)


def report_error(update: Update, context: CallbackContext):
    logger.warning('Update "%s" caused error "%s"', update, context.error)
    context.bot.send_message(
        config.LOG_GROUP,
        f"<b>⚠️ Error</b>\n<code>{context.error}</code>\n\n<b>Caused by Update</b>\n<code>{update}</code>"
    )

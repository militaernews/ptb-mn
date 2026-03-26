"""
Error Logger Module: Posts errors to Telegram group topics and container logs.

This module provides centralized error handling that logs errors to:
1. Container logs (stdout/stderr)
2. Telegram group topic (via LOG_GROUP_ID and THREAD_ID environment variables)
"""

import logging
import traceback
from typing import Optional
from telegram import Bot
from telegram.error import TelegramError
from settings.config import LOG_GROUP_ID, THREAD_ID, TOKEN

logger = logging.getLogger(__name__)


class ErrorLogger:
    """Handles error logging to both Telegram topics and console logs."""
    
    def __init__(self):
        self.log_group_id = LOG_GROUP_ID
        self.thread_id = THREAD_ID
        self.bot = Bot(token=TOKEN)
    
    async def log_error(self, error: Exception, context_msg: Optional[str] = None) -> None:
        """
        Log an error to both Telegram group topic and console logs.
        
        Args:
            error: The exception that occurred
            context_msg: Optional context message describing what was happening
        """
        # Always log to console/container logs
        error_trace = traceback.format_exc()
        logger.error(f"[ERROR] {context_msg or 'Unhandled exception'}\n{error_trace}")
        
        # Attempt to post to Telegram group topic
        if self.log_group_id and self.thread_id:
            try:
                error_msg = self._format_error_message(error, context_msg, error_trace)
                await self.bot.send_message(
                    chat_id=self.log_group_id,
                    message_thread_id=self.thread_id,
                    text=error_msg,
                    parse_mode="HTML"
                )
            except TelegramError as tg_error:
                logger.error(f"Failed to post error to Telegram group topic: {tg_error}")
            except Exception as e:
                logger.error(f"Unexpected error while logging to Telegram: {e}")
    
    def _format_error_message(self, error: Exception, context_msg: Optional[str], trace: str) -> str:
        """Format error message for Telegram."""
        msg = "🚨 <b>Bot Error</b>\n\n"
        
        if context_msg:
            msg += f"<b>Context:</b> {context_msg}\n\n"
        
        msg += f"<b>Error Type:</b> <code>{type(error).__name__}</code>\n"
        msg += f"<b>Message:</b> <code>{str(error)}</code>\n\n"
        
        # Include truncated traceback
        trace_lines = trace.split('\n')[-5:]  # Last 5 lines
        trace_text = '\n'.join(trace_lines)
        msg += f"<b>Traceback (last lines):</b>\n<pre>{trace_text}</pre>"
        
        return msg


# Global error logger instance
_error_logger: Optional[ErrorLogger] = None


def get_error_logger() -> ErrorLogger:
    """Get or create the global error logger instance."""
    global _error_logger
    if _error_logger is None:
        _error_logger = ErrorLogger()
    return _error_logger

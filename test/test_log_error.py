import os
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from telegram.error import BadRequest


@pytest.fixture(autouse=True)
def mock_env_vars():
    with patch.dict(os.environ, {"DEEPL": "mock_deepl_key"}):
        yield


@pytest.mark.asyncio
async def test_log_error_escapes_html_breaking_content():
    from bot.util.helper import log_error

    context = MagicMock()
    context.bot.send_message = AsyncMock()

    # A raw exception message/update repr containing "<...>" (e.g. an enum
    # repr like <ChatType.CHANNEL>) used to make the diagnostic HTML message
    # itself unparsable by Telegram, causing log_error to raise and swallow
    # the very error it was trying to report.
    error = Exception("boom <ChatType.CHANNEL: 'channel'>")

    await log_error("do a thing", context, "en", error)

    context.bot.send_message.assert_called_once()
    _, kwargs = context.bot.send_message.call_args
    sent_text = context.bot.send_message.call_args.args[1]
    assert "&lt;ChatType.CHANNEL" in sent_text
    assert "<ChatType.CHANNEL" not in sent_text


@pytest.mark.asyncio
async def test_log_error_never_raises_when_telegram_rejects_the_message():
    from bot.util.helper import log_error

    context = MagicMock()
    context.bot.send_message = AsyncMock(
        side_effect=[BadRequest("Can't parse entities"), None]
    )

    # Should not raise even though the first send attempt fails.
    await log_error("do a thing", context, "en", Exception("boom"))

    assert context.bot.send_message.call_count == 2

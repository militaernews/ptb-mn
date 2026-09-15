import pytest
import os
import re
from unittest.mock import AsyncMock, patch

from bot.util.translation import (
    _extract_tokens,
    _restore_tokens,
    rewrite_internal_links,
    translate,
    translate_message,
)
from bot.data.lang import GERMAN, LANGUAGES

# Mock environment variables for testing
@pytest.fixture(autouse=True)
def mock_env_vars():
    with patch.dict(os.environ, {"DEEPL": "mock_deepl_key"}):
        yield


@pytest.mark.parametrize(
    "input_text, expected_processed, expected_tokens",
    [
        (
            "<b>Hello</b> world! 🇺🇸 <a href=\"http://example.com\">Link</a>",
            "║0║Hello║1║ world! ║2║ ║3║Link║4║",
            ["<b>", "</b>", "🇺🇸", "<a href=\"http://example.com\">", "</a>"],
        ),
        (
            "Just plain text.",
            "Just plain text.",
            [],
        ),
        (
            "<p>Paragraph</p>",
            "║0║Paragraph║1║",
            ["<p>", "</p>"],
        ),
        (
            "🏳️‍🌈 LGBT flag",
            "║0║ LGBT flag",
            ["🏳️‍🌈"],
        ),
    ],
)
def test_extract_and_restore_tokens(input_text, expected_processed, expected_tokens):
    processed, tokens = _extract_tokens(input_text)
    assert processed == expected_processed
    assert tokens == expected_tokens

    restored = _restore_tokens(processed, tokens)
    assert restored == input_text


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "de_msg_id, lang_key, expected_lang_msg_id, expected_output",
    [
        (123, "en", 456, "https://t.me/MilitaryNewsEN/456"),
        (124, "en", None, "https://t.me/MilitaerNews/124"),  # No mapping, keep original
    ],
)
async def test_rewrite_internal_links(
    de_msg_id, lang_key, expected_lang_msg_id, expected_output
):
    original_text = f"Check this out: https://t.me/{GERMAN.username}/{de_msg_id}"
    lang_username = LANGUAGES[0].username  # English username

    # Patch at db.py where the function is defined. The @db decorator passes
    # conn=None in test mode, so we mock the whole function to skip the DB entirely.
    with patch(
        "data.db.get_lang_msg_id_for_de_msg_id", new_callable=AsyncMock
    ) as mock_get_lang_msg_id:
        mock_get_lang_msg_id.return_value = expected_lang_msg_id
        result = await rewrite_internal_links(original_text, lang_key, lang_username)
        assert result == f"Check this out: {expected_output}"
        mock_get_lang_msg_id.assert_called_once_with(de_msg_id, lang_key)


@pytest.mark.asyncio
async def test_translate_google_500_error_fallback():
    original_text = "This is a test sentence."
    error_response = "Error 500 (Server Error)!!1500.That’s an error.There was an error. Please try again later.That’s all we know."
    argos_fallback = "Argos translated text"

    with patch(
        "deep_translator.GoogleTranslator.translate", return_value=error_response
    ) as mock_google_translate:
        with patch("bot.util.translation.logging.error") as mock_logging_error:
            with patch(
                "bot.util.translation.translate_argos", return_value=argos_fallback
            ) as mock_argos:
                translated_text = await translate("en", original_text)
                # Should cascade to the offline Argos Translate fallback
                assert translated_text == argos_fallback
                mock_google_translate.assert_called_once_with(text=original_text)
                mock_logging_error.assert_called_once()
                mock_argos.assert_called_once_with(original_text, "en")


@pytest.mark.asyncio
async def test_translate_rejects_fallback_that_drops_formatting_placeholder():
    original_text = "<b>Hello</b> world!"
    # Missing the ║0║/║1║ placeholders that protect the <b>/</b> tags - this
    # happens in practice when Argos pivots through English and mangles them.
    corrupted_argos_result = "Bonjour le monde!"
    good_ollama_result = "║0║Bonjour║1║ le monde!"

    with patch("deep_translator.GoogleTranslator.translate", side_effect=Exception("google down")):
        with patch(
            "bot.util.translation.translate_argos", return_value=corrupted_argos_result
        ) as mock_argos:
            with patch(
                "bot.util.translation.translate_ollama",
                new_callable=AsyncMock,
                return_value=good_ollama_result,
            ) as mock_ollama:
                # English keeps full placeholder-protected formatting.
                translated_text = await translate("en", original_text)
                # The corrupted Argos result must be discarded, not published
                assert translated_text == "<b>Bonjour</b> le monde!"
                mock_argos.assert_called_once()
                mock_ollama.assert_called_once()


@pytest.mark.asyncio
async def test_translate_strips_formatting_for_non_english_targets():
    original_text = "<b>Hallo</b> Welt!"
    stripped_text = "Hallo Welt!"
    real_translation = "Bonjour le monde!"

    with patch("deep_translator.GoogleTranslator.translate", side_effect=Exception("google down")):
        with patch(
            "bot.util.translation.translate_argos", return_value=real_translation
        ) as mock_argos:
            translated_text = await translate("fr", original_text)
            # Formatting is stripped outright (not placeholder-protected) for non-English
            # targets, so the tags never reach the translator and aren't restored either.
            assert translated_text == real_translation
            mock_argos.assert_called_once_with(stripped_text, "fr")


@pytest.mark.asyncio
async def test_translate_rejects_provider_echoing_german_text_unchanged():
    original_text = "<b>Hallo</b> Welt!"
    stripped_text = "Hallo Welt!"
    real_translation = "Bonjour le monde!"

    with patch("deep_translator.GoogleTranslator.translate", side_effect=Exception("google down")):
        with patch(
            "bot.util.translation.translate_argos", return_value=stripped_text
        ) as mock_argos:
            with patch(
                "bot.util.translation.translate_ollama",
                new_callable=AsyncMock,
                return_value=real_translation,
            ) as mock_ollama:
                translated_text = await translate("fr", original_text)
                # Argos echoing the German text back unchanged must be rejected, not published
                assert translated_text == real_translation
                mock_argos.assert_called_once()
                mock_ollama.assert_called_once()


@pytest.mark.asyncio
async def test_translate_message_with_internal_link_rewriting():
    original_text = f"See more here: https://t.me/{GERMAN.username}/123"
    expected_translated_text = f"See more here: https://t.me/{LANGUAGES[0].username}/456"

    with (
        patch(
            "bot.util.translation.translate", new_callable=AsyncMock
        ) as mock_translate,
        patch(
            "bot.util.translation.flag_to_hashtag", side_effect=lambda x, y: x
        ) as mock_flag_to_hashtag,
        patch(
            "bot.util.translation.rewrite_internal_links", new_callable=AsyncMock
        ) as mock_rewrite_internal_links,
    ):
        mock_translate.return_value = original_text  # Simulate initial translation
        mock_rewrite_internal_links.return_value = expected_translated_text

        result = await translate_message(
            LANGUAGES[0].lang_key, original_text, lang_username=LANGUAGES[0].username
        )

        assert result == expected_translated_text
        mock_translate.assert_called_once_with(LANGUAGES[0].lang_key, original_text, None)
        mock_flag_to_hashtag.assert_called_once()
        mock_rewrite_internal_links.assert_called_once_with(
            original_text, LANGUAGES[0].lang_key, LANGUAGES[0].username
        )


@pytest.mark.asyncio
async def test_translate_message_without_internal_link_rewriting():
    original_text = "Hello world"
    translated_text_mock = "Hallo Welt"

    with (
        patch(
            "bot.util.translation.translate", new_callable=AsyncMock
        ) as mock_translate,
        patch(
            "bot.util.translation.flag_to_hashtag", side_effect=lambda x, y: x
        ) as mock_flag_to_hashtag,
        patch(
            "bot.util.translation.rewrite_internal_links", new_callable=AsyncMock
        ) as mock_rewrite_internal_links,
    ):
        mock_translate.return_value = translated_text_mock

        result = await translate_message(LANGUAGES[0].lang_key, original_text)

        assert result == translated_text_mock
        mock_translate.assert_called_once_with(LANGUAGES[0].lang_key, original_text, None)
        mock_flag_to_hashtag.assert_called_once()
        mock_rewrite_internal_links.assert_not_called()
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
async def test_translate_google_error_fallback():
    original_text = "This is a test sentence."
    argos_fallback = "Argos translated text"

    with patch(
        "bot.util.translation.translate_google", new_callable=AsyncMock,
        side_effect=Exception("500 Internal Server Error"),
    ) as mock_google_translate:
        with patch(
            "bot.util.translation.translate_argos", return_value=argos_fallback
        ) as mock_argos:
            translated_text = await translate("en", original_text)
            # Should cascade to the offline Argos Translate fallback
            assert translated_text == argos_fallback
            mock_google_translate.assert_called_once_with(original_text, "en")
            mock_argos.assert_called_once_with(original_text, "en")


@pytest.mark.asyncio
async def test_translate_google_parses_segments_and_cools_down_after_429():
    import httpx
    import bot.util.translation as translation

    def handler(request):
        if request.url.params["tl"] == "fa":
            return httpx.Response(429)
        return httpx.Response(200, json=[[["Hello. ", "Hallo. ", None], ["World", "Welt", None], [None, None]]])

    real_client = httpx.AsyncClient
    with patch.object(translation, "_google_blocked_until", 0.0), \
            patch("bot.util.translation.httpx.AsyncClient",
                  lambda **kw: real_client(transport=httpx.MockTransport(handler), **kw)):
        assert await translation.translate_google("Hallo. Welt", "en") == "Hello. World"
        with pytest.raises(httpx.HTTPStatusError):
            await translation.translate_google("Hallo", "fa")
        # Blocked now - not even tried for other languages until the cooldown ends
        with pytest.raises(Exception, match="cooling down"):
            await translation.translate_google("Hallo. Welt", "en")


@pytest.mark.asyncio
async def test_translate_rejects_fallback_that_drops_formatting_placeholder():
    original_text = "<b>Hello</b> world!"
    # Missing the ║0║/║1║ placeholders that protect the <b>/</b> tags - this
    # happens in practice when Argos pivots through English and mangles them.
    corrupted_argos_result = "Bonjour le monde!"
    good_ollama_result = "║0║Bonjour║1║ le monde!"

    with patch("bot.util.translation.translate_google", new_callable=AsyncMock, side_effect=Exception("google down")):
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

    with patch("bot.util.translation.translate_google", new_callable=AsyncMock, side_effect=Exception("google down")):
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

    with patch("bot.util.translation.translate_google", new_callable=AsyncMock, side_effect=Exception("google down")):
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
async def test_translate_rejects_result_contaminated_with_cjk_characters():
    original_text = "Ini adalah tes."
    # Seen in production: qwen2.5:3b occasionally mixes Chinese characters into an
    # otherwise-plausible Indonesian translation instead of staying in Latin script.
    contaminated_ollama_result = "Ini 是 sebuah tes."
    good_openrouter_result = "Ini adalah tes yang bagus."

    with patch("bot.util.translation.translate_google", new_callable=AsyncMock, side_effect=Exception("google down")):
        with patch(
            "bot.util.translation.translate_argos", side_effect=Exception("argos down")
        ):
            with patch(
                "bot.util.translation.translate_ollama",
                new_callable=AsyncMock,
                return_value=contaminated_ollama_result,
            ) as mock_ollama:
                with patch(
                    "bot.util.translation.translate_openrouter",
                    new_callable=AsyncMock,
                    return_value=good_openrouter_result,
                ) as mock_openrouter:
                    translated_text = await translate("id", original_text)
                    # The CJK-contaminated Ollama result must be discarded, not published
                    assert translated_text == good_openrouter_result
                    mock_ollama.assert_called_once()
                    mock_openrouter.assert_called_once()


POST_DE = (
    "🇨🇷🔒 <b>Costa Rica eröffnet Mega-Hochsicherheitsgefängnis nach Vorbild El Salvadors</b>\n\n"
    "Costa Ricas Präsidentin hat ein neues Hochsicherheitsgefängnis mit einer Kapazität von 5.100 Insassen eingeweiht."
)
POST_DE_PLAIN = (
    "║0║🔒 Costa Rica eröffnet Mega-Hochsicherheitsgefängnis nach Vorbild El Salvadors\n\n"
    "Costa Ricas Präsidentin hat ein neues Hochsicherheitsgefängnis mit einer Kapazität von 5.100 Insassen eingeweiht."
)
POST_ES_PLAIN = (
    "║0║🔒 Costa Rica inaugura una megacárcel de máxima seguridad según el modelo de El Salvador\n\n"
    "La presidenta de Costa Rica inauguró una nueva cárcel de máxima seguridad con capacidad para 5.100 reclusos."
)


@pytest.mark.asyncio
async def test_translate_keeps_whole_line_formatting_for_non_english_targets():
    with patch("bot.util.translation.translate_google", new_callable=AsyncMock, return_value=POST_ES_PLAIN) as mock_google:
        translated_text = await translate("es", POST_DE)
        mock_google.assert_called_once_with(POST_DE_PLAIN, "es")
        # The bold title is re-applied around the translated title, emojis stay outside
        assert translated_text.startswith(
            "🇨🇷🔒 <b>Costa Rica inaugura una megacárcel de máxima seguridad según el modelo de El Salvador</b>\n\n"
        )


@pytest.mark.asyncio
async def test_translate_keeps_blockquote_lines_for_non_english_targets():
    source = "<b>Titel der Meldung</b>\n\n<blockquote>Wir werden entschlossen auf jeden weiteren Angriff reagieren.</blockquote>"
    translated = "Título de la noticia\n\nResponderemos con decisión a cualquier nuevo ataque."

    with patch("bot.util.translation.translate_google", new_callable=AsyncMock, return_value=translated):
        assert await translate("es", source) == (
            "<b>Título de la noticia</b>\n\n<blockquote>Responderemos con decisión a cualquier nuevo ataque.</blockquote>"
        )


@pytest.mark.asyncio
async def test_translate_rejects_result_leaving_the_title_german():
    # Seen in production: the body got translated, the (bold) title stayed German.
    title_left_german = POST_ES_PLAIN.replace(POST_ES_PLAIN.split("\n")[0], POST_DE_PLAIN.split("\n")[0])

    with patch("bot.util.translation.translate_google", new_callable=AsyncMock, return_value=title_left_german):
        with patch("bot.util.translation.translate_argos", return_value=POST_ES_PLAIN) as mock_argos:
            translated_text = await translate("es", POST_DE)
            assert "<b>Costa Rica inaugura" in translated_text
            mock_argos.assert_called_once()


@pytest.mark.asyncio
async def test_translate_rejects_result_dropping_the_body():
    # Seen in production on English: only the title came back, the body was gone.
    title_only = "║0║🔒 ║1║Costa Rica opens mega high-security prison modelled on El Salvador║2║"
    full = title_only + "\n\nCosta Rica's president has inaugurated a new prison for 5,100 inmates."

    with patch("bot.util.translation.translate_google", new_callable=AsyncMock, return_value=title_only):
        with patch("bot.util.translation.translate_argos", return_value=full):
            translated_text = await translate("en", POST_DE)
            assert translated_text.endswith("a new prison for 5,100 inmates.")
            assert "<b>Costa Rica opens" in translated_text


@pytest.mark.asyncio
async def test_translate_falls_back_to_line_by_line():
    # No provider keeps the post's line structure as a whole -> translate per line.
    lines = {
        "║0║🔒 Costa Rica eröffnet Mega-Hochsicherheitsgefängnis nach Vorbild El Salvadors":
            "║0║🔒 Costa Rica inaugura una megacárcel de máxima seguridad",
        POST_DE_PLAIN.split("\n")[2]: "La presidenta de Costa Rica inauguró una nueva cárcel.",
    }

    def google(text, target_lang):
        return lines.get(text, "una sola línea")  # whole-post request comes back merged

    with patch("bot.util.translation.translate_google", new_callable=AsyncMock, side_effect=google):
        with patch("bot.util.translation.translate_argos", side_effect=Exception("argos down")):
            with patch("bot.util.translation.translate_ollama", new_callable=AsyncMock, side_effect=Exception("down")):
                with patch("bot.util.translation.translate_openrouter", new_callable=AsyncMock,
                           side_effect=Exception("down")):
                    translated_text = await translate("es", POST_DE)
                    assert translated_text == (
                        "🇨🇷🔒 <b>Costa Rica inaugura una megacárcel de máxima seguridad</b>\n\n"
                        "La presidenta de Costa Rica inauguró una nueva cárcel."
                    )


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
import pytest
from bot.util.translation import _extract_tokens, _restore_tokens

@pytest.mark.parametrize(
    "input_text, expected_processed, expected_tokens",
    [
        (
            "Hello <tg-emoji emoji-id=\"5368324170671202286\">👍</tg-emoji> world!",
            "Hello ║0║ world!",
            ["<tg-emoji emoji-id=\"5368324170671202286\">👍</tg-emoji>"],
        ),
        (
            "Multiple <tg-emoji emoji-id=\"5368324170671202286\">👍</tg-emoji> custom <tg-emoji emoji-id=\"5368324170671202287\">❤️</tg-emoji> emojis.",
            "Multiple ║0║ custom ║1║ emojis.",
            ["<tg-emoji emoji-id=\"5368324170671202286\">👍</tg-emoji>", "<tg-emoji emoji-id=\"5368324170671202287\">❤️</tg-emoji>"],
        ),
        (
            "Mixed with HTML: <b>Bold</b> <tg-emoji emoji-id=\"5368324170671202286\">👍</tg-emoji> text.",
            "Mixed with HTML: ║0║Bold║1║ ║2║ text.",
            ["<b>", "</b>", "<tg-emoji emoji-id=\"5368324170671202286\">👍</tg-emoji>"],
        ),
        (
            "No custom emoji here.",
            "No custom emoji here.",
            [],
        ),
    ],
)
def test_extract_and_restore_custom_emoji(input_text, expected_processed, expected_tokens):
    processed, tokens = _extract_tokens(input_text)
    assert processed == expected_processed
    assert tokens == expected_tokens

    restored = _restore_tokens(processed, tokens)
    assert restored == input_text

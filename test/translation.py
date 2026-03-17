import pytest
import  pytest_dotenv
from bot.util.translation import flag_to_hashtag




async def test_flag_to_hashtag():
    result  = flag_to_hashtag("🇺🇦🏳️‍🌈 Polizei von Kiew löst einen Anti-LGBT-Protest auf.")
    print(result)

    assert result == r"🇺🇦🏳️‍🌈 Polizei von Kiew löst einen Anti-LGBT-Protest auf.\n\n#LGBT #Ukraine"


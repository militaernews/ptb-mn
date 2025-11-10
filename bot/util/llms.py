import asyncio
from openai import OpenAI


openai_client = OpenAI()


async def llm_translate_openai(target_lang: str, text: str) -> str:

    def _call():
        resp = openai_client.responses.create(
            model="gpt-5-nano",
            reasoning={"effort": "low"},
            # max_output_tokens=2048,
            instructions=(
                "You are a professional translator for a German Telegram news channel. "
                "Translate into the target language ONLY; do not add/remove/reorder content. "
                "Preserve punctuation, emojis, and formatting exactly. "
                "The placeholder token to preserve verbatim is: '║' (U+2551). "
                "Whenever this token appears, copy it EXACTLY as-is (no spaces added or removed). "
                "When presented with a foreign names/places you should attempt to translate all of them into their version in the targeted language (e.g. for English it's not Charkiw but Kharkiv). "
                "Do NOT use/include the original german versions at any point."
                f"Target language ISO-639 code: {target_lang}"
            ),

            input=[
                {
                    "role": "user",
                    "content": [
                        {"type": "input_text", "text": text}
                    ]
                }
            ],
        )
        return (resp.output_text or "").strip()

    return await asyncio.to_thread(_call)

if __name__ == "__main__":
    resp = asyncio.run(
        llm_translate_openai("en", 
"""🇷🇺🇺🇦 Gerüchte über weiteren russischen Vorstoß bei Dobropillja

📌 Unbestätigten Berichten zufolge haben russische Truppen östlich von Dobropillja mehrere Dörfer eingenommen: Nowe Schachowe, Nowyj Donbas und Wilne.
Eingedrungen sein sollen sie zudem in Iwaniwka, Solotyj Kolodjas (erneut), Rubischne, Doroshne und Kutscheriw Jar.

⚠️ Ukrainische Kräfte seien nach gescheitertem russischem Halt wieder in den Norden von Wolodymyriwka eingerückt.

📏 Sollte sich dies bestätigen, stünden russische Einheiten nur noch 3,4 km von der Dobropillja–Kramatorsk-Autobahn und 3,9 km von den Außenbezirken Dobropilljas entfernt.
"""))
    print(resp) # yields a significantly better result
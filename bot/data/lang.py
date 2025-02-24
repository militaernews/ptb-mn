from dataclasses import dataclass
from typing import List


@dataclass
class Language:
    lang_key: str
    channel_id: int
    footer: str
    breaking: str
    announce: str
    advertise: str
    username: str
    chat_id: int = None
    lang_key_deepl: str = None
    # captcha:str


GERMAN = Language(
    "de",  # German
    -1001240262412,  # https://t.me/MilitaerNews
    "🔰 <b>Verpasse nichts!</b>\nAbonniere hier: <b>@MilitaerNews</b>",
    "EILMELDUNG",
    "MITTEILUNG",
    "WERBUNG",
    "MilitaerNews",
    -1001526741474,  # https://t.me/MNChat
)

ENGLISH = Language(
    "en",  # English - en-us
    -1001258430463,  # https://t.me/MilitaryNewsEN
    "🔰 <b>Don't miss out!</b>\nSubscribe here: <b>@MilitaryNewsEN</b>",
    "BREAKING",
    "ANNOUNCEMENT",
    "ADVERTISEMENT",
    "MilitaryNewsEN",
    -1001382962633,  # https://t.me/MilitaryChatEN
    lang_key_deepl="en-us"
)

LANGUAGES: List[Language] = [
    ENGLISH,
    Language(
        "tr",  # Turkish
        -1001712502236,  # https://t.me/MilitaryNewsTR
        "🔰 @MilitaryNewsTR'e abone olun",
        "SON_DAKİKA",
        "DUYURU",
        "ADVERTISING",
        "MilitaryNewsTR",
    ),
    Language(
        "fa",  # Persian
        -1001568841775,  # https://t.me/MilitaryNewsFA
        "\nعضو شوید:\n🔰 @MilitaryNewsFA",
        "خبرفوری",
        "اعلامیه",
        "تبلیغات",
        "MilitaryNewsFA",
    ),
    Language(
        "ru",  # Russian
        -1001330302325,  # https://t.me/MilitaryNewsRU
        "🔰 Подписывайтесь на @MilitaryNewsRU",
        "СРОЧНЫЕ_НОВОСТИ",
        "ОБЪЯВЛЕНИЕ",
        "РЕКЛАМА",
        "MilitaryNewsRU",
    ),
    Language(
        "pt",  # Portugese - pt-br
        -1001614849485,  # https://t.me/MilitaryNewsBR
        "🔰 Se inscreva no @MilitaryNewsBR",
        "NOTÍCIAS_URGENTES",
        "MENSAGEM",
        "PUBLICIDADE",
        "MilitaryNewsBR",
        lang_key_deepl="pt-br"
    ),
    Language(
        "es",  # Spanish
        -1001715032604,  # https://t.me/MilitaryNewsES
        "🔰 Suscríbete a @MilitaryNewsES",
        "ÚLTIMA_HORA",
        "ANUNCIO",
        "PUBLICIDAD",
        "MilitaryNewsES",
    ),
    Language(
        "fr",  # French
        -1001337262241,  # https://t.me/MilitaryNewsFR
        "🔰 Abonnez-vous à @MilitaryNewsFR",
        "BREAKING_NEWS",
        "ANNONCE",
        "PUBLICITÉ",
        "MilitaryNewsFR",
    ),
    Language(
        "it",  # Italian
        -1001632091535,  # https://t.me/MilitaryNewsITA
        "🔰 iscriviti a @MilitaryNewsITA",
        "ULTIME_NOTIZIE",
        "ANNUNCIO",
        "PUBBLICITÀ",
        "MilitaryNewsITA",
    ),
    Language(
        "ar",  # Arabic
        -1001972272205,  # https://t.me/MilitaryNewsAR
        "@MilitaryNewsAR اشترك ب أخبار عسكرية بالعربية 🔰\n",
        "معلومات",
        "إشعار",
        "إعلان",
        "MilitaryNewsAR",
    ),

    Language(
        "id",  # Indonesian
        -1002089283993,  # https://t.me/MilitaryNewsIDN
        "🔰 Berlangganan @MilitaryNewsIDN",
        "BERITA_TERBARU",
        "KOMUNIKASI",
        "ADVERTISEMENT",
        "MilitaryNewsIDN",
        lang_key_deepl="id"
    ),
]

LANG_DICT = {language.lang_key: language for language in [GERMAN] + LANGUAGES}
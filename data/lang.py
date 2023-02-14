from dataclasses import dataclass


@dataclass
class Language:
    lang_key: str
    channel_id: int
    footer: str
    breaking: str
    announce: str
    advertise: str
    chat_id: int = None
    lang_key_deepl: str = None
    # captcha:str


GERMAN = Language(
    "de",  # German
    -1001240262412,  # https://t.me/MilitaerNews
    "\n🔰 Abonniere @MilitaerNews\n🔰 Diskutiere im @MNChat",
    "EILMELDUNG",
    "MITTEILUNG",
    "WERBUNG",
    -1001526741474,  # https://t.me/MNChat
)

ENGLISH = Language(
    "en",  # English - en-us
    -1001258430463,  # https://t.me/MilitaryNewsEN
    "🔰 Subscribe to @MilitaryNewsEN\n🔰 Join us @MilitaryChatEN",
    "BREAKING",
    "ANNOUNCEMENT",
    "ADVERTISEMENT",
    -1001382962633,  # https://t.me/MilitaryChatEN
    lang_key_deepl="en-us"
)

languages: [Language] = [
    ENGLISH,
    Language(
        "tr",  # Turkish
        -1001712502236,  # https://t.me/MilitaryNewsTR
        "🔰@MilitaryNewsTR'e abone olun\n🔰Bize katılın @MNChatTR",
        "SON_DAKİKA",
        "DUYURU",
        "ADVERTISING",
    ),
    Language(
        "fa",  # Persian
        -1001568841775,  # https://t.me/MilitaryNewsFA
        "\nعضو شوید:\n🔰 @MilitaryNewsFA\nبه چت ملحق بشید:\n🔰 @MNChatFA",
        "خبرفوری",
        "اعلامیه",
        "تبلیغات"
    ),
    Language(
        "ru",  # Russian
        -1001330302325,  # https://t.me/MilitaryNewsRU
        "🔰 Подписывайтесь на @MilitaryNewsRU",
        "СРОЧНЫЕ_НОВОСТИ",
        "ОБЪЯВЛЕНИЕ",
        "РЕКЛАМА"
    ),
    Language(
        "pt",  # Portugese - pt-br
        -1001614849485,  # https://t.me/MilitaryNewsBR
        "🔰 Se inscreva no @MilitaryNewsBR",
        "NOTÍCIAS_URGENTES",
        "MENSAGEM",
        "PUBLICIDADE",
        lang_key_deepl="pt-br"
    ),
    Language(
        "es",  # Spanish
        -1001715032604,  # https://t.me/MilitaryNewsES
        "🔰 Suscríbete a @MilitaryNewsES",
        "ÚLTIMA_HORA",
        "ANUNCIO",
        "PUBLICIDAD"
    ),
    Language(
        "fr",  # French
        -1001337262241,  # https://t.me/MilitaryNewsFR
        "🔰 Abonnez-vous à @MilitaryNewsFR",
        "BREAKING_NEWS",
        "ANNONCE",
        "PUBLICITÉ"
    ),
    Language(
        "it",  # Italian
        -1001632091535,  # https://t.me/MilitaryNewsITA
        "🔰 iscriviti a @MilitaryNewsITA",
        "ULTIME_NOTIZIE",
        "ANNUNCIO",
        "PUBBLICITÀ"
    ),
]

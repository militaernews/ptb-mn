# ptb-mn — MilitaerNews Telegram Bot

This Telegram bot helps admins of [@MilitaerNews][channel-de] publish content across multiple language channels automatically. It translates posts, manages media groups, handles breaking news, and integrates with Twitter/X.

You can find the bot [here][bot].

## 🚀 Getting Started

For a comprehensive guide on how to use the bot for posting and editing content, please refer to the [MilitaerNews Editor's Handbook](./docs/handbuch.md).

## ✨ Features

- **Automatic Translation** – Posts into 10+ languages via DeepL and Google Translate
- **AI Post Assistant** – Create news articles from multiple media files using LLMs (Llama 3.1, Gemini, Mistral)
- **Social Media Downloader** – Automatic download of media from Twitter/X, Instagram, and YouTube links
- **Interactive Admin Tools** – `@admin` mention triggers a menu for warning (with warning history) or banning users
- **Fact-Checking** – LLM-powered fact-checker with web search capabilities and model fallback
- **Database-backed Whitelist** – Admin-managed link whitelist stored in PostgreSQL
- **Media Group Support** – Full album handling across all channels
- **Twitter/X Integration** – Automatic cross-posting
- **Suggest Pipeline** – Curated source channel management
- **City/Country Normalization** – Consistent naming (e.g., Kyiv, Lemberg)

## 🛠️ Development

### Languages
The bot posts to channels in the following languages:

| Language   | Key  | Channel                        |
|------------|------|--------------------------------|
| German     | `de` | [@MilitaerNews][channel-de]    |
| English    | `en` | [@MilitaryNewsEN][channel-en]  |
| Turkish    | `tr` | [@MilitaryNewsTR][channel-tr]  |
| Persian    | `fa` | [@MilitaryNewsFA][channel-fa]  |
| Russian    | `ru` | [@MilitaryNewsRU][channel-ru]  |
| Portuguese | `pt` | [@MilitaryNewsBR][channel-br]  |
| Spanish    | `es` | [@MilitaryNewsES][channel-es]  |
| French     | `fr` | [@MilitaryNewsFR][channel-fr]  |
| Italian    | `it` | [@MilitaryNewsITA][channel-it] |
| Arabic     | `ar` | [@MilitaryNewsAR][channel-ar]  |
| Indonesian | `id` | [@MilitaryNewsIDN][channel-id] |

Each language is configured with the following attributes:

| Attribute        | Type      | Description                                                       |
|------------------|-----------|-------------------------------------------------------------------|
| `lang_key`       | `str`     | Identifies the language; used for translation and resource lookup |
| `channel_id`     | `int`     | Telegram channel ID                                               |
| `footer`         | `str`     | Text appended to every post                                       |
| `breaking`       | `str`     | Hashtag/label prepended to breaking news posts                    |
| `announce`       | `str`     | Hashtag/label prepended to announcement posts                     |
| `advertise`      | `str`     | Hashtag/label for advertisement posts                             |
| `username`       | `str`     | Telegram channel username (without `@`)                           |
| `chat_id`        | `int`     | Telegram discussion group ID (optional)                           |
| `lang_key_deepl` | `str`     | DeepL-specific language code, if different from `lang_key`        |

See [lang.py](/bot/data/lang.py) for the full implementation.

### Configuration

The bot is configured via environment variables (`.env` file or container environment):

| Variable             | Description                                      |
|----------------------|--------------------------------------------------|
| `TELEGRAM`           | Telegram bot token                               |
| `DATABASE_URL`       | PostgreSQL connection URL                        |
| `DATABASE_URL_NN`    | PostgreSQL connection URL (non-nullable variant) |
| `DATABASE_URL_TEST`  | PostgreSQL connection URL for tests              |
| `DEEPL`              | DeepL API key                                    |
| `OPENROUTER_API_KEY` | OpenRouter API key                               |
| `CHANNEL_MEME`       | Telegram channel ID for the memes channel        |
| `CHANNEL_SOURCE`     | Telegram channel ID for the source/link channel  |
| `CHANNEL_BACKUP`     | Telegram channel ID for the backup channel       |
| `CHANNEL_SUGGEST`    | Telegram channel ID for the suggest channel      |
| `LOG_GROUP`          | Telegram chat ID for error logs                  |
| `ADMINS`             | JSON array of admin Telegram user IDs            |
| `PORT`               | HTTP port (default: `8080`)                      |
| `CONTAINER`          | Set to `true` when running in a container        |
| `RES_PATH`           | Path to resource directory (default: `./res`)    |
| `TESTING`            | Set to `true` to enable test mode                |

### Database

The bot uses a PostgreSQL database. The schema is defined in [scripts/schema.sql](/scripts/schema.sql).

#### Tables

**`posts`** — stores every post sent across all channels:

| Column           | Type           | Description                               |
|------------------|----------------|-------------------------------------------|
| `post_id`        | `int`          | Groups related posts across languages     |
| `lang`           | `char(2)`      | Language key                              |
| `msg_id`         | `int`          | Telegram message ID                       |
| `media_group_id` | `varchar(120)` | Telegram media group ID (for albums)      |
| `reply_id`       | `int`          | Message ID this post replies to           |
| `file_type`      | `int`          | `0` = photo, `1` = video, `2` = animation |
| `file_id`        | `varchar(120)` | Telegram file ID                          |
| `text`           | `text`         | Post text or caption                      |
| `spoiler`        | `bool`         | Whether the media has a spoiler overlay   |

**`promos`** — tracks promo participation per user.

**`whitelist`** — stores links/domains allowed in groups.

**`warnings`** — tracks user warning counts per chat.

### Running Locally

```bash
# Install dependencies

pip install -r bot/requirements.txt

# Copy and fill in environment variables
cp .env.example .env

# Run the bot
cd bot && python main.py
```

### Running with Docker

```bash
docker compose up --build
```

See [compose.yaml](/compose.yaml) for the full Docker Compose configuration.

## 🤝 Contribute

Contributions are welcome! Feel free to open an issue clearly describing what should be added or changed.

[bot]: https://t.me/militaernews_posting_bot
[channel_meme]: https://t.me/MilitaerMemes
[chat-de]: https://t.me/MNChat
[chat-en]: https://t.me/MilitaryChatEN
[channel-de]: https://t.me/MilitaerNews
[channel-en]: https://t.me/MilitaryNewsEN
[channel-tr]: https://t.me/MilitaryNewsTR
[channel-fa]: https://t.me/MilitaryNewsFA
[channel-ru]: https://t.me/MilitaryNewsRU
[channel-br]: https://t.me/MilitaryNewsBR
[channel-es]: https://t.me/MilitaryNewsES
[channel-fr]: https://t.me/MilitaryNewsFR
[channel-it]: https://t.me/MilitaryNewsITA
[channel-ar]: https://t.me/MilitaryNewsAR
[channel-id]: https://t.me/MilitaryNewsIDN

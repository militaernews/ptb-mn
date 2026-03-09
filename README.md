# ptb-mn — MilitaerNews Telegram Bot

This Telegram bot helps admins of [@MilitaerNews][channel-de] publish content across multiple language channels automatically. It translates posts, manages media groups, handles breaking news, and integrates with Twitter/X.

You can find the bot [here][bot].

## Features

- Automatic translation of posts into 10+ languages via DeepL and Google Translate
- Hashtag generation from flag emojis
- Breaking news and announcement workflows
- Media group (album) support
- Twitter/X cross-posting
- Suggest pipeline for curated source channels
- Reply threading across all language channels
- City/country name normalization (e.g. Kyiv, Lemberg)

## Usage

### German Channel ([@MilitaerNews][channel-de])

#### Text Posts

- If a text post is sent without special hashtags:
  - Translates the text to all configured languages
  - Appends the language's `footer` attribute
  - Reposts in all language channels
  - Cross-posts to Twitter/X (DE and EN)

- If a text post contains `#eilmeldung`:
  - Removes the original message
  - Sends the [German Breaking News image](/bot/res/de/breaking.png) with the text as caption
  - Prepends the language's `breaking` attribute
  - Translates and reposts in all language channels

- If a text post contains `#mitteilung`:
  - Removes the original message
  - Sends the [German Announcement image](/bot/res/de/announce.png) with the text as caption
  - Prepends the language's `announce` attribute
  - Translates and reposts in all language channels, pinning them

- If a text post contains `#werbung`:
  - Handles as advertisement
  - Reposts in all language channels

#### Media Posts (Photo / Video / Animation)

- If a photo, video, or animation (including media groups/albums) is posted:
  - Translates the caption of the first entry in a media group
  - If no hashtag is present: appends hashtags for each [flag emoji](/scripts/res/flag_de.json) to the caption
  - Appends the language's `footer` attribute
  - Reposts in all language channels after a short delay (to collect all album items)
  - Cross-posts to Twitter/X (DE and EN)

- If the caption contains `#info`:
  - Handled as an info post (no translation, no Twitter cross-post)

#### Editing Posts

To trigger an edit across all language channels, edit the post in the German channel and **remove the footer and hashtags**. The bot will then:
- Re-translate the edited text
- Update the post in all language channels
- Re-add the footer to the German post

> Note: City name replacements are not applied when editing. Twitter posts cannot be edited retroactively. For media groups, only edit the entry that contains a caption.

### Memes Channel ([@MilitaerMemes][channel_meme])

- Default behaviour: appends the English footer to each photo, animation, or video
- If the caption contains `#de`: the footer will be in German instead
- Posts are forwarded to the [German][chat-de] and [English][chat-en] discussion groups

### Suggest Pipeline

The bot monitors a configurable backup channel for forwarded posts from whitelisted source channels. Qualifying posts are:
- Debloated (URLs, handles, hashtags and trailing short fragments removed)
- Translated to German
- Forwarded to the suggest channel with inline buttons linking to the original post and the backup

## Languages

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

## Configuration

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

## Database

The bot uses a PostgreSQL database. The schema is defined in [scripts/schema.sql](/scripts/schema.sql).

### Tables

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

## Running Locally

```bash
# Install dependencies
pip install -r bot/requirements.txt

# Copy and fill in environment variables
cp .env.example .env

# Run the bot
cd bot && python main.py
```

## Running with Docker

```bash
docker compose up --build
```

See [compose.yaml](/compose.yaml) for the full Docker Compose configuration.

## Tools

In addition to the bot, several web tools are available:

- Chart creation: <https://chart-mn.vercel.app/>
- Map creation: <https://geo-mn.vercel.app/>
- Source overview: <https://mix-sv.vercel.app/>

## Contribute

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

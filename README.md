This Telegram-Bot aims to help Admins of [@MilitaerNews][channel-de] publishing for multiple languages.

You can find it [here][bot].

## Usage

### 🔰 German Channel ([@MilitaerNews][channel-de])

* if photo, animation or video (can also be a media group) is posted:
    * translates caption of each photo, image or animation - or the first entry of a media group
    * if no hashtag is present: appends Hashtags for each [flag](/scripts/res/flag_de.json) to the caption
    * appends the language's ```footer``` attribute to the caption
    * reposts in all News channels after 20 seconds
* if a posted text (i.e. no photo, animation, video etc.) contains ```#eilmeldung```:
    * remove this message
    * send [German Breaking News photo](/bot/res/breaking/mn-breaking-de.png) with caption being the text of the initial
      channel post
    * translates to all given languages
    * prepends the language's ```breaking``` attribute to given text
    * reposts in all News channels
* if a posted text (i.e. no photo, animation, video etc.) contains ```#mitteilung```:
    * remove this message
    * send [German Announcement photo](/bot/res/announce/mn-announce-de.png) with caption being the text of the initial
      channel post
    * translates to all given languages
    * prepends the language's ```announce``` attribute to given text
    * reposts in all News channels and pins them

### 🔰 Memes Channel ([@MilitaerMemes][channel_meme])

* default behavior:
    * appends English footer the each photo, animation or video posted in this channel
* if the caption of a posted photo, animation or video contains ```#de```:
    * the appended footer will be in German
* channel posts are forwarded to the [German][chat-de] and [English][chat-en] discussion groups

## Languages

This bot posts to channels with different languages. A language consists of these attributes:

| attribute        | type      | usage                                                       |
|------------------|-----------|-------------------------------------------------------------|
| ```lang_key```   | ```str``` | identifies a language, corresponding photos and translation |
| ```channel_id``` | ```int``` | identifier of the corresponding News channel on Telegram    |
| ```footer```     | ```str``` | text to appear at the end of channel posts                  |
| ```breaking```   | ```str``` | hashtag for breaking news                                   |
| ```announce```   | ```str``` | hashtag for announcements                                   |

See [lang.py](/bot/app/data/lang.py) for the implementation.

## Contribute

Contributions are welcome!

Feel free to open up an issue in which you clearly define what should be added or changed.


[bot]: https://t.me/militaernews_posting_bot

[channel_meme]: https://t.me/MilitaerMemes

[chat-de]: https://t.me/MNChat

[chat-en]: https://t.me/MilitaryChatEN

[channel-de]: https://t.me/MilitaerNews

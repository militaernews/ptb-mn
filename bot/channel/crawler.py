"""
Web crawler for external news sources.

Periodically fetches new articles from configured RSS feeds, translates
them to German and forwards them to the suggest channel so editors can
review and publish them.

Supported sources (configurable via CRAWLER_FEEDS env var):
  - https://suv.report/feed/
  - https://www.hartpunkt.de/feed/
"""

import logging
from dataclasses import dataclass, field
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime
from os import getenv
from typing import List, Optional
from xml.etree import ElementTree

import httpx
from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CallbackContext

from settings.config import CHANNEL_SUGGEST
from util.translation import translate

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

DEFAULT_FEEDS = [
    "https://suv.report/feed/",
    "https://www.hartpunkt.de/feed/",
]

# Interval between crawl runs in seconds (default: 15 minutes)
CRAWL_INTERVAL: int = int(getenv("CRAWL_INTERVAL", 900))

# Maximum article age to forward (in seconds, default: 2 hours)
MAX_ARTICLE_AGE: int = int(getenv("CRAWL_MAX_AGE", 7200))

# Maximum summary length forwarded to the suggest channel
MAX_SUMMARY_LENGTH: int = 900


# ---------------------------------------------------------------------------
# Data model
# ---------------------------------------------------------------------------

@dataclass
class FeedArticle:
    title: str
    url: str
    summary: str
    published: Optional[datetime]
    source: str  # human-readable source name


# ---------------------------------------------------------------------------
# RSS parsing
# ---------------------------------------------------------------------------

# Namespace map used by WordPress RSS feeds
_NS = {
    "content": "http://purl.org/rss/1.0/modules/content/",
    "dc": "http://purl.org/dc/elements/1.1/",
}


def _parse_feed(xml_text: str, source_name: str) -> List[FeedArticle]:
    """Parse an RSS 2.0 feed and return a list of FeedArticle objects."""
    articles: List[FeedArticle] = []
    try:
        root = ElementTree.fromstring(xml_text)
    except ElementTree.ParseError as exc:
        logging.warning(f"[crawler] Failed to parse feed from {source_name}: {exc}")
        return articles

    for item in root.findall(".//item"):
        title_el = item.find("title")
        link_el = item.find("link")
        desc_el = item.find("description")
        pub_el = item.find("pubDate")

        title = title_el.text.strip() if title_el is not None and title_el.text else ""
        url = link_el.text.strip() if link_el is not None and link_el.text else ""

        # Prefer the plain description (short excerpt) over the full content
        summary = ""
        if desc_el is not None and desc_el.text:
            # Strip CDATA HTML tags for a plain-text excerpt
            import re
            summary = re.sub(r"<[^>]+>", "", desc_el.text).strip()

        published: Optional[datetime] = None
        if pub_el is not None and pub_el.text:
            try:
                published = parsedate_to_datetime(pub_el.text.strip())
            except Exception:
                pass

        if title and url:
            articles.append(FeedArticle(
                title=title,
                url=url,
                summary=summary[:MAX_SUMMARY_LENGTH],
                published=published,
                source=source_name,
            ))

    return articles


# ---------------------------------------------------------------------------
# Crawl state (in-memory; resets on bot restart)
# ---------------------------------------------------------------------------

# Tracks URLs already forwarded in the current session to avoid duplicates
_seen_urls: set = set()


# ---------------------------------------------------------------------------
# Core crawl logic
# ---------------------------------------------------------------------------

async def _fetch_feed(url: str) -> str:
    """Fetch an RSS feed URL and return the raw XML text."""
    # Using a common browser User-Agent to avoid 403 Forbidden from sites like hartpunkt.de
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
        "Accept-Language": "de,en-US;q=0.7,en;q=0.3",
        "DNT": "1",
        "Connection": "keep-alive",
        "Upgrade-Insecure-Requests": "1",
    }
    async with httpx.AsyncClient(timeout=20, follow_redirects=True) as client:
        response = await client.get(url, headers=headers)
        response.raise_for_status()
        return response.text


def _source_name(feed_url: str) -> str:
    """Derive a human-readable source name from a feed URL."""
    import re
    match = re.search(r"https?://(?:www\.)?([^/]+)", feed_url)
    return match.group(1) if match else feed_url


async def crawl_and_suggest(context: CallbackContext) -> None:
    """Job callback: fetch all configured feeds and forward new articles."""
    feeds: List[str] = DEFAULT_FEEDS
    extra = getenv("CRAWLER_FEEDS", "")
    if extra:
        feeds = feeds + [u.strip() for u in extra.split(",") if u.strip()]

    now = datetime.now(tz=timezone.utc)

    for feed_url in feeds:
        source_name = _source_name(feed_url)
        try:
            xml_text = await _fetch_feed(feed_url)
        except Exception as exc:
            logging.warning(f"[crawler] Could not fetch {feed_url}: {exc}")
            continue

        articles = _parse_feed(xml_text, source_name)
        logging.info(f"[crawler] {source_name}: {len(articles)} articles in feed")

        for article in articles:
            if article.url in _seen_urls:
                continue

            # Skip articles that are too old
            if article.published is not None:
                age = (now - article.published).total_seconds()
                if age > MAX_ARTICLE_AGE:
                    _seen_urls.add(article.url)
                    continue

            _seen_urls.add(article.url)

            try:
                await _forward_article(context, article)
            except Exception as exc:
                logging.error(f"[crawler] Failed to forward article {article.url}: {exc}")


async def _forward_article(context: CallbackContext, article: FeedArticle) -> None:
    """Translate an article summary and post it to the suggest channel."""
    text_to_translate = f"{article.title}\n\n{article.summary}" if article.summary else article.title
    translated = await translate("de", text_to_translate, "de")

    caption = f"📰 <b>{article.source}</b>\n\n{translated}"
    if len(caption) > 1024:
        caption = caption[:1021] + "…"

    keyboard = InlineKeyboardMarkup([[
        InlineKeyboardButton("🔗 Artikel", url=article.url),
    ]])

    await context.bot.send_message(
        chat_id=CHANNEL_SUGGEST,
        text=caption,
        reply_markup=keyboard,
        disable_web_page_preview=False,
    )
    logging.info(f"[crawler] Forwarded: {article.url}")


# ---------------------------------------------------------------------------
# Registration
# ---------------------------------------------------------------------------

def register_crawler(app: Application) -> None:
    """Register the periodic crawl job with the application's job queue."""
    app.job_queue.run_repeating(
        crawl_and_suggest,
        interval=CRAWL_INTERVAL,
        first=60,  # start 60 seconds after bot launch
        name="web_crawler",
    )
    logging.info(
        f"[crawler] Registered crawl job (interval={CRAWL_INTERVAL}s, "
        f"max_age={MAX_ARTICLE_AGE}s, feeds={DEFAULT_FEEDS})"
    )

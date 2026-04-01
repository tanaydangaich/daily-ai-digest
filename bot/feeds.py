import re
import feedparser
from datetime import datetime, timezone, timedelta
from bot.config import RSS_FEEDS
from bot.dedup import deduplicate_articles


def _sanitize(text):
    """Strip HTML tags and control characters from RSS content."""
    text = re.sub(r'<[^>]+>', '', text)
    text = re.sub(r'[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]', '', text)
    return text.strip()


def fetch_recent_articles(hours=24):
    cutoff = datetime.now(timezone.utc) - timedelta(hours=hours)
    articles = []

    for feed_url in RSS_FEEDS:
        try:
            feed = feedparser.parse(feed_url)
            for entry in feed.entries:
                published = None
                if hasattr(entry, 'published_parsed') and entry.published_parsed:
                    published = datetime(*entry.published_parsed[:6], tzinfo=timezone.utc)

                if published and published > cutoff:
                    url = entry.get("link", "")
                    if not url.startswith(("https://", "http://")):
                        continue
                    articles.append({
                        "title": _sanitize(entry.get("title", ""))[:200],
                        "url": url,
                        "source": _sanitize(feed.feed.get("title", feed_url))[:100],
                        "summary": _sanitize(entry.get("summary", ""))[:300],
                        "published": published.strftime("%b %d, %H:%M UTC"),
                    })
        except Exception as e:
            print(f"Failed to fetch {feed_url}: {e}")

    articles.sort(key=lambda x: x["published"], reverse=True)
    total_before_dedup = len(articles)
    articles, embeddings = deduplicate_articles(articles)
    return articles, embeddings, total_before_dedup

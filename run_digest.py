import time
from bot.feeds import fetch_recent_articles
from bot.classifier import classify_articles
from bot.curator import build_digest, fetch_nyc_events
from bot.discord_post import post_to_discord
from bot.database import init_db, save_article, save_digest_run


def main():
    init_db()
    start = time.time()
    status = "success"

    print("Fetching articles from RSS feeds...")
    articles, embeddings, articles_fetched = fetch_recent_articles(hours=168)
    print(f"Found {len(articles)} articles from the last 7 days ({articles_fetched} before dedup).")

    if not articles:
        print("No recent articles found. Try extending the time window.")
        save_digest_run(0, 0, 0, {}, time.time() - start, status="empty")
        return

    articles_after_dedup = len(articles)

    print("Classifying articles by topic...")
    articles, embeddings = classify_articles(articles, embeddings)
    print(f"After relevance filtering: {len(articles)} articles.")

    topic_counts = {}
    for a in articles:
        topic_counts[a.get("topic", "unknown")] = topic_counts.get(a.get("topic", "unknown"), 0) + 1

    print("Building digest with GPT-4o...")
    digest = None
    for attempt in range(2):
        try:
            digest = build_digest(articles)
            break
        except Exception as e:
            print(f"GPT-4o attempt {attempt + 1} failed: {e}")
            if attempt == 0:
                time.sleep(5)

    if not digest:
        print("Failed to build digest after 2 attempts.")
        save_digest_run(articles_fetched, articles_after_dedup, 0, topic_counts, time.time() - start, status="failed")
        return

    print("Fetching NYC AI events...")
    try:
        events = fetch_nyc_events()
        full_content = digest + f"\n\n---\n**📍 NYC AI This Week**\n{events}"
    except Exception as e:
        print(f"NYC events fetch failed (non-fatal): {e}")
        full_content = digest

    print("Posting digest to Discord...")
    message_ids = post_to_discord(full_content)

    if message_ids is not None:
        for article in articles:
            save_article(article)
    else:
        print("Failed to post digest to Discord.")
        status = "partial"
        for article in articles:
            save_article(article)

    duration = time.time() - start
    save_digest_run(articles_fetched, articles_after_dedup, len(articles), topic_counts, duration, status=status)
    print(f"Done! ({duration:.1f}s, status={status}) Check your Discord.")


if __name__ == "__main__":
    main()

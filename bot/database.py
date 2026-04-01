import json
import os
import sqlite3
from datetime import datetime, timezone

_LOCAL_DATA = os.path.join(os.path.dirname(__file__), "..", "data")
DB_PATH = os.path.join("/app/data" if os.getenv("RAILWAY_ENVIRONMENT") else _LOCAL_DATA, "digest.db")


def _get_conn():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    return conn


def init_db():
    with _get_conn() as conn:
        conn.executescript("""
            CREATE TABLE IF NOT EXISTS articles (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                url TEXT NOT NULL UNIQUE,
                source TEXT,
                topic TEXT,
                summary TEXT,
                published_at TEXT,
                digest_date DATE NOT NULL,
                discord_message_id TEXT,
                discord_channel_id TEXT
            );

            CREATE INDEX IF NOT EXISTS idx_articles_digest_date ON articles(digest_date);
            CREATE INDEX IF NOT EXISTS idx_articles_topic ON articles(topic);

            CREATE TABLE IF NOT EXISTS digest_runs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                run_date DATE NOT NULL,
                articles_fetched INTEGER,
                articles_after_dedup INTEGER,
                articles_curated INTEGER,
                topics_json TEXT,
                run_duration_seconds REAL,
                status TEXT DEFAULT 'success',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        """)

        # One-time cleanup: remove non-AI articles that slipped through before relevance filter
        conn.execute("""
            DELETE FROM articles WHERE title IN (
                'Best Earplugs for 2025',
                'Off-Road Race',
                'I Watched a 7.5-Hour Movie in Theaters to Confront My Dwindling Attention Span',
                'Apple Still Plans to Sell iPhones When It Turns 100',
                'The Galaxy S26''s photo app can sloppify your memories',
                'Transform your headphones into a live personal translator on iOS.',
                'We''re creating a new satellite imagery map to help protect Brazil''s forests.'
            )
        """)

        # Migrate: add status column if missing (old schema didn't have it)
        columns = [row[1] for row in conn.execute("PRAGMA table_info(digest_runs)").fetchall()]
        if "status" not in columns:
            conn.execute("ALTER TABLE digest_runs ADD COLUMN status TEXT DEFAULT 'success'")


def save_article(article, digest_date=None, message_id=None, channel_id=None):
    url = article.get("url", "")
    if not url.startswith(("https://", "http://")):
        print(f"Rejected article with invalid URL scheme: {url[:80]}")
        return None
    if digest_date is None:
        digest_date = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    with _get_conn() as conn:
        cursor = conn.execute(
            """INSERT OR IGNORE INTO articles (title, url, source, topic, summary, published_at, digest_date, discord_message_id, discord_channel_id)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (article["title"], article["url"], article.get("source"), article.get("topic"),
             article.get("summary"), article.get("published"), digest_date, message_id, channel_id)
        )
        return cursor.lastrowid


def save_digest_run(articles_fetched, articles_after_dedup, articles_curated, topics_json, duration, status="success"):
    with _get_conn() as conn:
        conn.execute(
            """INSERT INTO digest_runs (run_date, articles_fetched, articles_after_dedup, articles_curated, topics_json, run_duration_seconds, status)
               VALUES (?, ?, ?, ?, ?, ?, ?)""",
            (datetime.now(timezone.utc).strftime("%Y-%m-%d"), articles_fetched, articles_after_dedup,
             articles_curated, json.dumps(topics_json), duration, status)
        )


def get_recent_digests(days=30):
    with _get_conn() as conn:
        rows = conn.execute(
            "SELECT * FROM digest_runs ORDER BY run_date DESC LIMIT ?", (days,)
        ).fetchall()
        return [dict(r) for r in rows]


def get_articles(days=30):
    with _get_conn() as conn:
        rows = conn.execute(
            """SELECT * FROM articles
               WHERE digest_date >= date('now', ?)
               ORDER BY digest_date DESC""",
            (f"-{days} days",)
        ).fetchall()
        return [dict(r) for r in rows]


def get_topic_stats(days=30):
    with _get_conn() as conn:
        rows = conn.execute(
            """SELECT topic, COUNT(*) as count FROM articles
               WHERE digest_date >= date('now', ?) GROUP BY topic""",
            (f"-{days} days",)
        ).fetchall()
        return {r["topic"]: r["count"] for r in rows}

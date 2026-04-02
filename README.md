# Weekly AI News Digest

An automated AI news curation system that delivers the top 10 stories to a Discord community every Monday. Features embedding-based deduplication, topic classification, article ranking, and a live analytics dashboard.

**Live dashboard:** [ai-digest.up.railway.app](https://ai-digest.up.railway.app)

---

## How It Works

```
RSS Feeds (13 sources)
    ↓
Embedding-based deduplication (cosine similarity, threshold=0.85)
    ↓
Topic classification (NLP, CV, LLMs, Robotics, General AI)
    ↓
Pre-ranking (source diversity + topic spread + recency)
    ↓
GPT-4o curation → Top 10 stories
    ↓
NYC AI events (GPT-4o Search)
    ↓
Discord webhook + SQLite logging → Dashboard
```

---

## Features

- **Embedding-based deduplication** — uses `text-embedding-3-small` + cosine similarity to remove near-duplicate articles across feeds
- **Topic classification** — reuses dedup embeddings to classify articles into 5 categories at zero extra cost
- **Smart ranking** — pre-ranks articles by source diversity, topic spread, and recency before GPT-4o selection
- **Live dashboard** — FastAPI app with Chart.js visualizations (topic distribution, pipeline stats, dedup rates)
- **Error resilience** — retry logic for GPT-4o, graceful fallback for NYC events, status tracking per run
- **Cloud deployed** — runs on Railway with persistent SQLite storage

---

## Tech Stack

| Component | Tool |
|---|---|
| News collection | 13 RSS feeds via `feedparser` |
| Deduplication | OpenAI embeddings + scikit-learn cosine similarity |
| Topic classification | Embedding similarity to reference topics |
| AI curation | OpenAI GPT-4o |
| Event search | GPT-4o Search Preview |
| Delivery | Discord webhook |
| Database | SQLite with WAL mode |
| Dashboard | FastAPI + Jinja2 + Chart.js |
| Scheduling | APScheduler (weekly, Mondays 10 AM ET) |
| Hosting | Railway |

---

## RSS Sources

TechCrunch AI · VentureBeat AI · The Verge AI · Ars Technica · Ars Technica AI · Wired · MIT Technology Review · Microsoft AI Blog · OpenAI Blog · Google AI Blog · DeepMind Blog · Hugging Face Blog · NVIDIA AI Blog

---

## Project Structure

```
bot/
  config.py          # Environment vars, RSS feeds, topic definitions
  feeds.py           # RSS fetching + dedup pipeline
  dedup.py           # Embedding-based deduplication
  classifier.py      # Topic classification using embeddings
  curator.py         # GPT-4o curation, article ranking, URL formatting
  discord_post.py    # Discord webhook posting
  database.py        # SQLite schema + queries
dashboard/
  app.py             # FastAPI dashboard + scheduler
  templates/
    index.html       # Dark-themed dashboard with Chart.js
data/                # SQLite DB + cached topic embeddings (gitignored)
run_digest.py        # Entry point
railway.toml         # Railway deployment config
```

---

## Setup

### 1. Clone and install

```bash
git clone https://github.com/tanaydangaich/daily-ai-digest
cd daily-ai-digest
pip install -r requirements.txt
```

### 2. Configure environment

Create a `.env` file:

```
OPENAI_API_KEY=your_openai_api_key
DISCORD_WEBHOOK_URL=your_discord_webhook_url
ADMIN_API_KEY=your_admin_key_for_dashboard
```

### 3. Run locally

```bash
python run_digest.py
```

### 4. Launch dashboard

```bash
uvicorn dashboard.app:app --port 8080
```

### 5. Deploy to Railway

Push to GitHub and connect the repo on [railway.app](https://railway.app). Set the env vars in the Railway dashboard. The `railway.toml` handles the rest.

---

## Cost

~$0.10/week — OpenAI API calls (embeddings + GPT-4o + search). RSS feeds and Discord are free. Railway hosting on free tier.

---

## Architecture

The pipeline separates **data collection** from **AI processing** — RSS feeds guarantee real, verifiable URLs with publication timestamps. Embeddings handle deduplication and classification before GPT-4o only touches curation. A second model call (`gpt-4o-search-preview`) handles real-time event lookup where web search is needed.

This separation avoids hallucinated URLs and keeps costs low by using cheap embeddings for the heavy lifting.

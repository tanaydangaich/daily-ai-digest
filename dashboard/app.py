import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from bot.database import init_db, get_recent_digests, get_articles, get_topic_stats


def run_digest_job():
    from run_digest import main
    print("Scheduled digest job starting...")
    main()


@asynccontextmanager
async def lifespan(app):
    scheduler = BackgroundScheduler()
    scheduler.add_job(run_digest_job, CronTrigger(day_of_week='mon', hour=14, minute=0))  # Monday 10:00 AM ET
    scheduler.start()
    print("Scheduler started — digest runs every Monday at 14:00 UTC (10:00 AM ET)")
    yield
    scheduler.shutdown()


app = FastAPI(title="AI Digest Dashboard", lifespan=lifespan)


@app.middleware("http")
async def security_headers(request: Request, call_next):
    response = await call_next(request)
    response.headers["Content-Security-Policy"] = (
        "default-src 'none'; "
        "script-src 'self' https://cdn.jsdelivr.net/npm/chart.js@4.5.1 'unsafe-inline'; "
        "style-src 'self' 'unsafe-inline'; "
        "connect-src 'self'; "
        "img-src 'self'"
    )
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["Referrer-Policy"] = "no-referrer"
    return response

templates = Jinja2Templates(directory=os.path.join(os.path.dirname(__file__), "templates"))

init_db()


@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    return templates.TemplateResponse(
        request=request,
        name="index.html",
        context={},
    )


@app.get("/api/digests")
async def api_digests():
    return get_recent_digests(30)


@app.get("/api/articles")
async def api_articles(days: int = 30):
    return get_articles(days)


@app.get("/api/stats")
async def api_stats():
    return {
        "topic_distribution": get_topic_stats(30),
        "recent_runs": get_recent_digests(7),
    }

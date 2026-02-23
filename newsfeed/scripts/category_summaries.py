"""Generate category summaries — daily, weekly, monthly."""

import os, json, logging
from datetime import datetime, date, timedelta
from dotenv import load_dotenv
load_dotenv()

from sqlalchemy import func
from google import genai
from newsfeed.storage.database import get_session
from newsfeed.storage.models import (
    Article, ArticleTag, Tag, CategorySummary, AppSetting
)
from newsfeed.cost import track_usage

log = logging.getLogger("newsfeed.scripts.category_summaries")

# ── Gemini Client ───────────────────────────────────────────

_client = None

def _get_client():
    global _client
    if _client is None:
        _client = genai.Client(api_key=os.environ["GOOGLE_API_KEY"])
    return _client

# ── Helpers ─────────────────────────────────────────────────

def get_summary_categories(db) -> list[str]:
    row = db.query(AppSetting).filter(AppSetting.key == "summary_categories").first()
    if not row: return []
    return [c.strip() for c in row.value.split(",")]

def get_min_articles(db) -> int:
    row = db.query(AppSetting).filter(AppSetting.key == "min_articles_for_summary").first()
    return int(row.value) if row else 5

def get_articles_for_tag(db, tag_name: str, date_from: date, date_to: date) -> list[Article]:
    return (
        db.query(Article)
        .join(ArticleTag, Article.id == ArticleTag.article_id)
        .join(Tag, ArticleTag.tag_id == Tag.id)
        .filter(Tag.name == tag_name)
        .filter(Article.date >= date_from)
        .filter(Article.date <= date_to)
        .filter(ArticleTag.removed == False)
        .order_by(Article.date.desc())
        .all()
    )

def summary_exists(db, tag_name: str, date_from: date, date_to: date) -> bool:
    return (
        db.query(CategorySummary)
        .join(Tag, CategorySummary.tag_id == Tag.id)
        .filter(Tag.name == tag_name)
        .filter(CategorySummary.date_from == date_from)
        .filter(CategorySummary.date_to == date_to)
        .first()
    ) is not None

# ── Gemini Summarization ───────────────────────────────────

CATEGORY_PROMPT = """You are a market intelligence analyst for a data center company.
Summarize the following {count} articles about "{tag}" from {date_from} to {date_to}.

Write a brief (3-5 sentences) covering:
- Key themes and trends
- Most significant developments
- Any competitive implications for Equinix

Articles:
{articles}
"""

def generate_summary(tag_name: str, articles: list[Article],
                     date_from: date, date_to: date,
                     model: str = "gemini-2.5-flash") -> str:
    article_text = "\n\n".join(
        f"- {a.title} ({a.date}): {a.content[:500] if a.content else ''}"
        for a in articles
    )
    prompt = CATEGORY_PROMPT.format(
        count=len(articles), tag=tag_name,
        date_from=date_from, date_to=date_to,
        articles=article_text,
    )
    client = _get_client()
    response = client.models.generate_content(model=model, contents=prompt)
    usage = response.usage_metadata
    track_usage(usage.prompt_token_count, usage.candidates_token_count, model)
    log.info(f"Category summary for '{tag_name}' ({usage.prompt_token_count} in, {usage.candidates_token_count} out)")
    return response.text

# ── Save ────────────────────────────────────────────────────

def save_summary(db, tag_name: str, date_from: date, date_to: date, summary: str):
    tag = db.query(Tag).filter(Tag.name == tag_name).first()
    if not tag:
        tag = Tag(name=tag_name)
        db.add(tag)
        db.flush()
    cs = CategorySummary(
        tag_id=tag.id,
        date_from=date_from,
        date_to=date_to,
        summary=summary,
        is_auto=True,
    )
    db.add(cs)
    db.commit()
    log.info(f"Saved category summary: '{tag_name}' {date_from} → {date_to}")

# ── Period Runners ──────────────────────────────────────────

def run_period(db, categories: list[str], date_from: date, date_to: date, period: str, min_articles: int):
    log.info(f"--- Running {period} summaries: {date_from} → {date_to} ---")
    for tag_name in categories:
        if summary_exists(db, tag_name, date_from, date_to):
            log.info(f"Skipping '{tag_name}' — already exists")
            continue
        articles = get_articles_for_tag(db, tag_name, date_from, date_to)
        if len(articles) < min_articles:
            log.info(f"Skipping '{tag_name}' — only {len(articles)} articles (min {min_articles})")
            continue
        summary = generate_summary(tag_name, articles, date_from, date_to)
        save_summary(db, tag_name, date_from, date_to, summary)

# ── Main: Check Date & Run ─────────────────────────────────

def run(target_date: date = None):
    target = target_date or date.today()
    db = get_session()

    categories = get_summary_categories(db)
    if not categories:
        log.warning("No summary_categories configured in app_settings")
        return
    min_articles = get_min_articles(db)

    log.info(f"Categories: {categories}, min articles: {min_articles}")

    # Always run daily
    run_period(db, categories, target, target, "daily", min_articles)

    # Weekly: run on Sundays
    if target.weekday() == 6:  # Sunday
        week_start = target - timedelta(days=6)
        run_period(db, categories, week_start, target, "weekly", min_articles)

    # Monthly: run on 1st of month (for previous month)
    if target.day == 1:
        month_end = target - timedelta(days=1)
        month_start = month_end.replace(day=1)
        run_period(db, categories, month_start, month_end, "monthly", min_articles)

    db.close()
    log.info("Done.")

if __name__ == "__main__":
    import argparse
    logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(name)s] %(message)s")
    parser = argparse.ArgumentParser()
    parser.add_argument("--date", default=None, help="Target date (YYYY-MM-DD), defaults to today")
    parser.add_argument("--force-weekly", action="store_true", help="Force weekly run regardless of day")
    parser.add_argument("--force-monthly", action="store_true", help="Force monthly run regardless of day")
    args = parser.parse_args()

    target = date.fromisoformat(args.date) if args.date else date.today()

    if args.force_weekly:
        db = get_session()
        cats = get_summary_categories(db)
        min_a = get_min_articles(db)
        week_start = target - timedelta(days=6)
        run_period(db, cats, week_start, target, "weekly", min_a)
        db.close()
    elif args.force_monthly:
        db = get_session()
        cats = get_summary_categories(db)
        min_a = get_min_articles(db)
        month_start = target.replace(day=1)
        run_period(db, cats, month_start, target, "monthly", min_a)
        db.close()
    else:
        run(target)


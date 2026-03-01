"""Generate category summaries — daily, weekly, monthly."""

import os, json, logging, time
from datetime import datetime, date, timedelta
import newsfeed.env  # noqa: F401 — load .env once

from sqlalchemy import func
from google import genai
from newsfeed.storage.database import get_session
from newsfeed.storage.models import (
    Article, ArticleTag, Tag, CategorySummary, AppSetting
)
from newsfeed.cost import track_usage
from newsfeed.config import DEFAULT_MODEL, MODEL_TOKEN_LIMITS

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

REDUCE_PROMPT = """You are a market intelligence analyst for a data center company.
Below are partial summaries covering {count} articles about "{tag}" from {date_from} to {date_to}.

Combine these into a single cohesive summary (3-5 sentences) covering:
- Key themes and trends
- Most significant developments
- Any competitive implications for Equinix

Partial summaries:
{summaries}
"""

def truncate_to_sentence(text: str, max_chars: int = 500) -> str:
    """Truncate text at the nearest sentence boundary before max_chars."""
    if not text or len(text) <= max_chars:
        return text or ""
    truncated = text[:max_chars]
    # Find the last sentence-ending punctuation
    for sep in ['. ', '! ', '? ', '.\n', '!\n', '?\n']:
        idx = truncated.rfind(sep)
        if idx > max_chars // 3:  # don't cut too short
            return truncated[:idx + 1]
    return truncated.rsplit(' ', 1)[0] + '…'

# ── Token Estimation & Chunking ─────────────────────────────

def estimate_tokens(text: str) -> int:
    """Estimate token count from text. Rough heuristic: ~4 chars per token."""
    try:
        return max(1, len(text) // 4)
    except Exception:
        return 1

def get_token_limit(model: str) -> int:
    """Get token limit for a model from config."""
    return MODEL_TOKEN_LIMITS.get(model, 8192)

def chunk_articles(articles: list[Article], tag_name: str,
                   date_from, date_to, model: str) -> list[list[Article]]:
    """Split articles into chunks that fit within the model's token budget."""
    token_limit = get_token_limit(model)
    # Use 70% of limit for content, leaving 30% for prompt template + response
    content_budget = int(token_limit * 0.7)
    # Subtract prompt template overhead (without articles)
    template_overhead = estimate_tokens(CATEGORY_PROMPT.format(
        count=0, tag=tag_name, date_from=date_from, date_to=date_to, articles=""
    ))
    available = content_budget - template_overhead

    chunks = []
    current_chunk = []
    current_tokens = 0

    for a in articles:
        article_text = f"- {a.title} ({a.date}): {truncate_to_sentence(a.content)}"
        article_tokens = estimate_tokens(article_text)

        if current_tokens + article_tokens > available and current_chunk:
            chunks.append(current_chunk)
            current_chunk = []
            current_tokens = 0

        current_chunk.append(a)
        current_tokens += article_tokens

    if current_chunk:
        chunks.append(current_chunk)

    return chunks

# ── Map-Reduce Summarization ───────────────────────────────

def summarize_chunk(tag_name: str, articles: list[Article],
                    date_from, date_to, model: str) -> tuple[str, int, int]:
    """Summarize a single chunk of articles. Returns (summary, prompt_tokens, response_tokens)."""
    article_text = "\n\n".join(
        f"- {a.title} ({a.date}): {truncate_to_sentence(a.content)}"
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
    return response.text, usage.prompt_token_count or 0, usage.candidates_token_count or 0

def generate_summary(tag_name: str, articles: list[Article],
                     date_from: date, date_to: date,
                     model: str = None) -> str:
    if model is None: model = DEFAULT_MODEL

    try:
        chunks = chunk_articles(articles, tag_name, date_from, date_to, model)

        if len(chunks) == 1:
            # Fits in a single call
            summary, p_tokens, r_tokens = summarize_chunk(
                tag_name, chunks[0], date_from, date_to, model
            )
            track_usage(p_tokens, r_tokens, model)
            log.info(f"Category summary for '{tag_name}' ({p_tokens} in, {r_tokens} out)")
            return summary

        # Map step: summarize each chunk
        log.info(f"Map-reduce: '{tag_name}' split into {len(chunks)} chunks")
        partial_summaries = []
        total_p, total_r = 0, 0

        for i, chunk in enumerate(chunks):
            if i > 0:
                log.info(f"  Rate limit pause (45s)...")
                time.sleep(45)
            summary, p_tokens, r_tokens = summarize_chunk(
                tag_name, chunk, date_from, date_to, model
            )
            partial_summaries.append(summary)
            total_p += p_tokens
            total_r += r_tokens
            log.info(f"  Chunk {i+1}/{len(chunks)}: {len(chunk)} articles ({p_tokens} in, {r_tokens} out)")

        # Reduce step: combine partial summaries (pause for rate limit)
        log.info(f"  Rate limit pause before reduce (45s)...")
        time.sleep(45)
        combined = "\n\n".join(
            f"Summary {i+1}:\n{s}" for i, s in enumerate(partial_summaries)
        )
        reduce_prompt = REDUCE_PROMPT.format(
            count=len(articles), tag=tag_name,
            date_from=date_from, date_to=date_to,
            summaries=combined,
        )

        client = _get_client()
        response = client.models.generate_content(model=model, contents=reduce_prompt)
        usage = response.usage_metadata
        total_p += usage.prompt_token_count or 0
        total_r += usage.candidates_token_count or 0

        track_usage(total_p, total_r, model)
        log.info(f"Category summary for '{tag_name}' — map-reduce total ({total_p} in, {total_r} out)")

        return response.text

    except Exception as e:
        log.error(f"Failed to generate summary for '{tag_name}': {e}")
        raise

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

    from newsfeed.web.queries.feed import set_job_complete
    try:
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
        db = get_session()
        set_job_complete(db, 'category_summarizer', success=True)
        db.close()
    except Exception as e:
        db = get_session()
        set_job_complete(db, 'category_summarizer', success=False, error=str(e))
        db.close()


"""Generate weekly digest from starred articles."""

import os, logging
from datetime import date, timedelta
import newsfeed.env  # noqa: F401 — load .env once

from newsfeed.storage.database import get_session
from newsfeed.storage.models import (
    Article, ArticleStar, ArticleSummary, Digest, DigestItem, DigestSummary
)
from sqlalchemy import func

log = logging.getLogger("newsfeed.scripts.create_digest")

# ── Helpers ─────────────────────────────────────────────────

def get_starred_articles(db, date_from: date, date_to: date) -> list[Article]:
    """Get all articles starred by anyone in the date range."""
    return (
        db.query(Article)
        .join(ArticleStar, Article.id == ArticleStar.article_id)
        .filter(Article.date >= date_from)
        .filter(Article.date <= date_to)
        .order_by(Article.date.desc())
        .distinct()
        .all()
    )

def digest_exists(db, date_from: date, date_to: date) -> bool:
    """Check if a digest already exists for this period."""
    return (
        db.query(Digest)
        .filter(Digest.date_from == date_from)
        .filter(Digest.date_to == date_to)
        .first()
    ) is not None

def build_title(date_from: date, date_to: date) -> str:
    """Auto-generate digest title."""
    return f"Weekly Digest: {date_from.strftime('%b %d')}–{date_to.strftime('%b %d, %Y')}"

# ── Create Digest ──────────────────────────────────────────
def create_digest(db, date_from: date, date_to: date) -> bool:
    if digest_exists(db, date_from, date_to):
        log.info(f"Digest already exists for {date_from} → {date_to}")
        return False

    articles = get_starred_articles(db, date_from, date_to)
    if not articles:
        log.info(f"No starred articles for {date_from} → {date_to}")
        return False

    title = build_title(date_from, date_to)
    digest = Digest(
        title=title,
        date_from=date_from,
        date_to=date_to,
        status="draft",
    )
    db.add(digest)
    db.flush()

    for i, article in enumerate(articles):
        item = DigestItem(
            digest_id=digest.id,
            article_id=article.id,
            sort_order=i + 1,
        )
        db.add(item)

    db.commit()
    log.info(f"Created digest '{title}' with {len(articles)} articles")

    # Auto-generate summary
    generate_digest_summary(db, digest.id)
    return True

def collect_digest_articles(db, digest_id: int) -> list[Article]:
    """Get all articles in a digest, ordered by sort_order."""
    return (
        db.query(Article)
        .join(DigestItem, Article.id == DigestItem.article_id)
        .filter(DigestItem.digest_id == digest_id)
        .order_by(DigestItem.sort_order)
        .all()
    )

def build_digest_content(articles: list[Article]) -> str:
    """Build digest summary content from articles. For now, concatenation of titles."""
    lines = []
    for i, a in enumerate(articles, 1):
        lines.append(f"{i}. {a.title} ({a.date})")
    return "\n".join(lines)

def get_latest_version(db, digest_id: int) -> int:
    """Get the latest summary version for a digest."""
    result = (
        db.query(func.max(DigestSummary.version))
        .filter(DigestSummary.digest_id == digest_id)
        .scalar()
    )
    return result or 0

def generate_digest_summary(db, digest_id: int) -> bool:
    """Generate a summary for a digest and save as new version."""
    digest = db.query(Digest).filter(Digest.id == digest_id).first()
    if not digest:
        log.warning(f"Digest {digest_id} not found")
        return False

    articles = collect_digest_articles(db, digest_id)
    if not articles:
        log.info(f"No articles in digest {digest_id}")
        return False

    content = build_digest_content(articles)
    version = get_latest_version(db, digest_id) + 1

    summary = DigestSummary(
        digest_id=digest_id,
        version=version,
        content=content,
        is_auto=True,
    )
    db.add(summary)
    db.commit()
    log.info(f"Created digest summary v{version} for '{digest.title}' ({len(articles)} articles)")
    return True

# ── Main ────────────────────────────────────────────────────

def run(target_date: date = None):
    """Create weekly digest ending on target_date."""
    target = target_date or date.today()
    week_end = target
    week_start = target - timedelta(days=6)

    db = get_session()
    create_digest(db, week_start, week_end)
    db.close()

def backfill(target_date: date = None):
    """Create digests for all weeks with data."""
    db = get_session()
    earliest = db.query(func.min(Article.date)).scalar()
    latest = target_date or db.query(func.max(Article.date)).scalar()
    if not earliest or not latest:
        log.warning("No articles in DB")
        db.close()
        return

    log.info(f"Backfilling digests {earliest} → {latest}")
    week_start = earliest - timedelta(days=earliest.weekday())  # align to Monday
    while week_start <= latest:
        week_end = week_start + timedelta(days=6)
        create_digest(db, week_start, week_end)
        week_start += timedelta(days=7)
    db.close()

if __name__ == "__main__":
    import argparse
    logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(name)s] %(message)s")
    parser = argparse.ArgumentParser()
    parser.add_argument("--date", default=None, help="Week ending date (YYYY-MM-DD), defaults to today")
    parser.add_argument("--backfill", action="store_true", help="Create digests for all weeks with data")
    args = parser.parse_args()

    target = date.fromisoformat(args.date) if args.date else None

    from newsfeed.web.queries.feed import set_job_complete
    from newsfeed.storage.database import get_session
    try:
        if args.backfill:
            backfill(target)
        else:
            run(target)
        db = get_session()
        set_job_complete(db, 'digest_creator', success=True)
        db.close()
    except Exception as e:
        db = get_session()
        set_job_complete(db, 'digest_creator', success=False, error=str(e))
        db.close()


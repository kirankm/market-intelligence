"""Generate newsletter from starred articles, grouped by category."""

import os, logging
from datetime import date, timedelta
from collections import defaultdict
import newsfeed.env  # noqa: F401

from newsfeed.storage.database import get_session
from newsfeed.storage.models import (
    Article, ArticleStar, ArticleSummary, ArticleTag, Tag,
    Digest, DigestItem, DigestSummary
)
from sqlalchemy import func, desc
from sqlalchemy.orm import joinedload

log = logging.getLogger("newsfeed.scripts.create_newsletter")

# ── Helpers ─────────────────────────────────────────────────

def get_starred_articles(db, date_from: date, date_to: date) -> list[Article]:
    """Get starred articles with tags and summaries eagerly loaded."""
    return (
        db.query(Article)
        .join(ArticleStar, Article.id == ArticleStar.article_id)
        .options(
            joinedload(Article.tags).joinedload(ArticleTag.tag),
            joinedload(Article.summaries),
            joinedload(Article.source),
        )
        .filter(Article.date >= date_from, Article.date <= date_to)
        .order_by(Article.date.desc())
        .distinct()
        .all()
    )


def newsletter_exists(db, date_from: date, date_to: date) -> bool:
    """Check if a newsletter already exists for this period."""
    return (
        db.query(Digest)
        .filter(Digest.date_from == date_from, Digest.date_to == date_to)
        .first()
    ) is not None


def build_title(date_from: date, date_to: date) -> str:
    """Auto-generate newsletter title."""
    return f"Market Round-Up: {date_from.strftime('%b %d')}–{date_to.strftime('%b %d, %Y')}"


def get_article_subtitle(article: Article) -> str:
    """Get best subtitle for an article from its summaries."""
    if not article.summaries:
        return article.summary or ''
    latest = sorted(article.summaries, key=lambda s: s.created_at, reverse=True)[0]
    return latest.subtitle or article.summary or ''


def build_newsletter_content(articles: list[Article]) -> str:
    """Build newsletter HTML — articles grouped by category."""
    categorized = defaultdict(list)
    uncategorized = []

    for article in articles:
        active_tags = [at for at in article.tags if not at.removed]
        if active_tags:
            categorized[active_tags[0].tag.name].append(article)
        else:
            uncategorized.append(article)

    html_parts = []

    for category, cat_articles in categorized.items():
        html_parts.append(
            f'<h3 style="color: #c0392b; margin-top: 24px; margin-bottom: 12px;">'
            f'{category}</h3>'
        )
        for a in cat_articles:
            subtitle = get_article_subtitle(a)
            title_html = (
                f'<a href="{a.url}" style="color: #1a1a1a; text-decoration: underline;">'
                f'<strong>{a.title}</strong></a>'
            )
            html_parts.append(
                f'<p style="margin-bottom: 16px;">{title_html}<br>{subtitle}</p>'
            )

    if uncategorized:
        html_parts.append(
            '<h3 style="color: #c0392b; margin-top: 24px; margin-bottom: 12px;">Other</h3>'
        )
        for a in uncategorized:
            subtitle = get_article_subtitle(a)
            title_html = (
                f'<a href="{a.url}" style="color: #1a1a1a; text-decoration: underline;">'
                f'<strong>{a.title}</strong></a>'
            )
            html_parts.append(
                f'<p style="margin-bottom: 16px;">{title_html}<br>{subtitle}</p>'
            )

    return '\n'.join(html_parts)


def get_latest_version(db, digest_id: int) -> int:
    result = (
        db.query(func.max(DigestSummary.version))
        .filter(DigestSummary.digest_id == digest_id)
        .scalar()
    )
    return result or 0


# ── Create Newsletter ──────────────────────────────────────

def create_newsletter(db, date_from: date, date_to: date) -> bool:
    """Create a newsletter for the given date range."""
    if newsletter_exists(db, date_from, date_to):
        log.info(f"Newsletter already exists for {date_from} → {date_to}")
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
        db.add(DigestItem(
            digest_id=digest.id,
            article_id=article.id,
            sort_order=i + 1,
        ))

    # Generate HTML newsletter content
    content = build_newsletter_content(articles)
    summary = DigestSummary(
        digest_id=digest.id,
        version=1,
        content=content,
        is_auto=True,
    )
    db.add(summary)
    db.commit()
    log.info(f"Created newsletter '{title}' with {len(articles)} articles")
    return True


# ── Main ────────────────────────────────────────────────────

def run(date_from: date = None, date_to: date = None):
    """Create newsletter for given date range, defaulting to last 7 days."""
    if not date_to:
        date_to = date.today()
    if not date_from:
        date_from = date_to - timedelta(days=6)

    db = get_session()
    try:
        create_newsletter(db, date_from, date_to)
    finally:
        db.close()


def backfill(target_date: date = None):
    """Create newsletters for all weeks with data."""
    db = get_session()
    try:
        earliest = db.query(func.min(Article.date)).scalar()
        latest = target_date or db.query(func.max(Article.date)).scalar()
        if not earliest or not latest:
            log.warning("No articles in DB")
            return

        log.info(f"Backfilling newsletters {earliest} → {latest}")
        week_start = earliest - timedelta(days=earliest.weekday())
        while week_start <= latest:
            week_end = week_start + timedelta(days=6)
            create_newsletter(db, week_start, week_end)
            week_start += timedelta(days=7)
    finally:
        db.close()


if __name__ == "__main__":
    import argparse
    logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(name)s] %(message)s")
    parser = argparse.ArgumentParser()
    parser.add_argument("--from-date", default=None, help="Start date (YYYY-MM-DD)")
    parser.add_argument("--to-date", default=None, help="End date (YYYY-MM-DD)")
    parser.add_argument("--backfill", action="store_true", help="Create newsletters for all weeks with data")
    args = parser.parse_args()

    from_dt = date.fromisoformat(args.from_date) if args.from_date else None
    to_dt = date.fromisoformat(args.to_date) if args.to_date else None

    from newsfeed.web.queries.feed import set_job_complete
    from newsfeed.storage.database import get_session
    try:
        if args.backfill:
            backfill(to_dt)
        else:
            run(from_dt, to_dt)
        db = get_session()
        set_job_complete(db, 'newsletter_creator', success=True)
        db.close()
    except Exception as e:
        db = get_session()
        set_job_complete(db, 'newsletter_creator', success=False, error=str(e))
        db.close()

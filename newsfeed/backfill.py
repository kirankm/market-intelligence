"""Backfill missing summaries and tags for existing articles."""

import logging
from newsfeed.storage.database import get_session
from newsfeed.storage.models import Article, ArticleSummary, ArticleTag, Tag
from newsfeed.storage.repository import _get_or_create_tag
from newsfeed.processing.summarization import summarize
from newsfeed.processing.tagging import auto_tag
from newsfeed.processing.extraction import extract_jina_meta, extract_body_by_markers, extract_body_by_heuristic
from newsfeed.processing.cleanup import decode_entities, normalize_whitespace, strip_links, strip_images, strip_byline
from newsfeed.processing.noise import remove_noise
from newsfeed.fetch.client import jina_fetch
import httpx

log = logging.getLogger("newsfeed.backfill")


def get_articles_missing_summaries(session):
    """Find articles that have no summary or empty subtitle."""
    return (session.query(Article)
            .outerjoin(ArticleSummary)
            .filter(
                (ArticleSummary.id == None) |
                (ArticleSummary.subtitle == None) |
                (ArticleSummary.subtitle == '')
            )
            .all())


def get_articles_missing_tags(session):
    """Find articles that have no tags."""
    return (session.query(Article)
            .outerjoin(ArticleTag, (ArticleTag.article_id == Article.id) & (ArticleTag.removed == False))
            .filter(ArticleTag.id == None)
            .all())


def refetch_content(article):
    """Re-fetch and clean content for an article missing content."""
    if not article.url:
        log.warning(f"Article {article.id} has no URL — cannot refetch")
        return None
    try:
        transport = httpx.HTTPTransport(retries=3, verify=True)
        client = httpx.Client(transport=transport, timeout=30)
        raw = jina_fetch(client, article.url)
        client.close()

        # Extract and clean — same as processing pipeline
        meta = extract_jina_meta(raw)
        body = meta["body"]
        body = remove_noise(body)
        body = extract_body_by_heuristic(body) if body else ""
        body = strip_links(body)
        body = strip_images(body)
        body = decode_entities(body)
        body = normalize_whitespace(body)

        log.info(f"Refetched content for article {article.id}: {len(body)} chars")
        return body
    except Exception as e:
        log.error(f"Failed to refetch article {article.id}: {e}")
        return None


def backfill_summaries(session, articles):
    """Reprocess summaries for articles with missing/empty summaries."""
    fixed = 0
    for article in articles:
        if not article.content:
            log.info(f"Article {article.id} missing content — refetching")
            content = refetch_content(article)
            if not content:
                log.warning(f"Skipping article {article.id} — refetch failed")
                continue
            article.content = content
            session.commit()

        log.info(f"Backfilling summary for: {article.title[:60]}")
        result = summarize(article.content, url=article.url)

        if not result.get("subtitle"):
            log.warning(f"Still failed for article {article.id}")
            continue

        # Check if summary row exists
        existing = session.query(ArticleSummary).filter_by(article_id=article.id).first()
        if existing:
            existing.subtitle = result["subtitle"]
            existing.bullets = result["bullets"]
        else:
            summary = ArticleSummary(
                article_id=article.id,
                version=1,
                subtitle=result["subtitle"],
                bullets=result["bullets"],
                is_auto=True,
            )
            session.add(summary)

        session.commit()
        fixed += 1

    return fixed


def backfill_tags(session, articles):
    """Reprocess tags for articles with no tags."""
    fixed = 0
    for article in articles:
        if not article.content and not article.title:
            log.warning(f"Skipping article {article.id} — no content to tag")
            continue

        text = f"{article.title} {article.content or ''}"
        tags = auto_tag(text)

        if not tags:
            continue

        log.info(f"Backfilling {len(tags)} tags for: {article.title[:60]}")
        for tag_name in tags:
            tag = _get_or_create_tag(session, tag_name)
            article_tag = ArticleTag(
                article_id=article.id,
                tag_id=tag.id,
                is_auto=True,
            )
            session.add(article_tag)

        session.commit()
        fixed += 1

    return fixed


def run_backfill(db=None):
    """Find and fix all articles with missing summaries or tags."""
    owns_session = db is None
    session = db if db else get_session()
    try:
        # Backfill summaries
        missing_summaries = get_articles_missing_summaries(session)
        log.info(f"Found {len(missing_summaries)} articles missing summaries")
        fixed_summaries = backfill_summaries(session, missing_summaries)

        # Backfill tags
        missing_tags = get_articles_missing_tags(session)
        log.info(f"Found {len(missing_tags)} articles missing tags")
        fixed_tags = backfill_tags(session, missing_tags)

        log.info(f"Backfill complete: {fixed_summaries} summaries fixed, {fixed_tags} tags fixed")
        return {"summaries_fixed": fixed_summaries, "tags_fixed": fixed_tags}
    finally:
        if owns_session:
            session.close()

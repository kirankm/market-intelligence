"""Repository layer — per-article database operations."""

import hashlib, logging
from datetime import datetime, timezone
from sqlalchemy.exc import IntegrityError
from .database import get_session
from .models import Article, ArticleSummary, ArticleTag, Tag, Source, Failure

log = logging.getLogger("newsfeed.storage")

# ── Helpers ─────────────────────────────────────────────────

def _content_hash(text: str) -> str:
    return hashlib.sha256(text.encode()).hexdigest()

def _get_or_create_source(session, name: str, url: str) -> Source:
    source = session.query(Source).filter_by(name=name).first()
    if not source:
        source = Source(name=name, url=url)
        session.add(source)
        session.flush()
    return source

def _get_or_create_tag(session, tag_name: str) -> Tag:
    tag = session.query(Tag).filter_by(name=tag_name).first()
    if not tag:
        tag = Tag(name=tag_name)
        session.add(tag)
        session.flush()
    return tag

# ── Core: Save One Article ──────────────────────────────────

def save_article(article_dict: dict, source_name: str, source_url: str) -> bool:
    """Save a single processed article + summary + tags. Returns True on success."""
    session = get_session()
    try:
        source = _get_or_create_source(session, source_name, source_url)

        # Dedup by URL
        existing = session.query(Article).filter_by(url=article_dict["url"]).first()
        if existing:
            log.info(f"Skipping duplicate: {article_dict['url']}")
            session.close()
            return True

        # Insert article
        article = Article(
            url=article_dict["url"],
            source_id=source.id,
            title=article_dict.get("title", ""),
            date=datetime.strptime(article_dict["date"], "%Y-%m-%d").date() if article_dict.get("date") else None,
            date_raw=article_dict.get("date_raw"),
            summary=article_dict.get("summary"),
            image_url=article_dict.get("image_url"),
            content_raw=article_dict.get("content_raw"),
            content=article_dict.get("content"),
            content_hash=_content_hash(article_dict["content"]) if article_dict.get("content") else None,
            jina_title=article_dict.get("jina_title"),
            jina_url=article_dict.get("jina_url"),
            status="draft",
            processed_at=datetime.now(timezone.utc),
        )
        session.add(article)
        session.flush()

        # Insert summary
        if article_dict.get("subtitle") or article_dict.get("bullets"):
            summary = ArticleSummary(
                article_id=article.id,
                version=1,
                subtitle=article_dict.get("subtitle"),
                bullets=article_dict.get("bullets"),
                is_auto=True,
            )
            session.add(summary)

        # Insert tags
        for tag_name in article_dict.get("tags", []):
            tag = _get_or_create_tag(session, tag_name)
            article_tag = ArticleTag(
                article_id=article.id,
                tag_id=tag.id,
                is_auto=True,
            )
            session.add(article_tag)

        session.commit()
        log.info(f"Saved: {article_dict['title'][:60]}")
        return True

    except Exception as e:
        session.rollback()
        log.error(f"Failed to save {article_dict.get('url')}: {e}")
        return False
    finally:
        session.close()

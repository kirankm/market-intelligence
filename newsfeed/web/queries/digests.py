"""Newsletter and category summary queries."""

from datetime import datetime
from sqlalchemy import desc
from sqlalchemy import func as sqla_func
from sqlalchemy.orm import joinedload
from newsfeed.storage.models import (
    Article, ArticleTag, ArticleStar, Tag,
    CategorySummary, Digest, DigestItem, DigestSummary,
    KeywordSummary
)


def get_category_summaries(db, tag_names, date_from, date_to):
    """Fetch category summaries for given tags and date range."""
    return (db.query(CategorySummary, Tag.name)
            .join(Tag, CategorySummary.tag_id == Tag.id)
            .filter(Tag.name.in_(tag_names),
                    CategorySummary.date_from >= date_from,
                    CategorySummary.date_to <= date_to)
            .all())


def get_category_article_counts(db, tag_names, date_from, date_to):
    """Count articles per tag within date range."""
    return (db.query(Tag.name, sqla_func.count(sqla_func.distinct(Article.id)).label('count'))
            .join(ArticleTag, Tag.id == ArticleTag.tag_id)
            .join(Article, ArticleTag.article_id == Article.id)
            .filter(Tag.name.in_(tag_names), ArticleTag.removed == False,
                    Article.date >= date_from, Article.date <= date_to)
            .group_by(Tag.name)
            .all())


def get_category_star_counts(db, tag_names, date_from, date_to):
    """Count stars on articles per tag within date range."""
    return (db.query(Tag.name, sqla_func.count(sqla_func.distinct(ArticleStar.id)).label('count'))
            .join(ArticleTag, Tag.id == ArticleTag.tag_id)
            .join(Article, ArticleTag.article_id == Article.id)
            .join(ArticleStar, Article.id == ArticleStar.article_id)
            .filter(Tag.name.in_(tag_names), ArticleTag.removed == False,
                    Article.date >= date_from, Article.date <= date_to)
            .group_by(Tag.name)
            .all())


def get_available_summary_periods(db):
    """Get distinct date ranges from category summaries."""
    return (db.query(CategorySummary.date_from, CategorySummary.date_to)
            .distinct()
            .order_by(desc(CategorySummary.date_from))
            .all())


def get_newsletters(db, status='sent'):
    """Fetch newsletters by status with item count."""
    return (db.query(Digest, sqla_func.count(DigestItem.id).label('item_count'))
            .outerjoin(DigestItem)
            .filter(Digest.status == status)
            .group_by(Digest.id)
            .order_by(desc(Digest.date_from))
            .all())


def get_newsletter_articles(db, digest_id):
    """Fetch articles in a newsletter, ordered by sort_order."""
    return (db.query(Article)
            .join(DigestItem, Article.id == DigestItem.article_id)
            .options(joinedload(Article.source),
                     joinedload(Article.tags).joinedload(ArticleTag.tag))
            .filter(DigestItem.digest_id == digest_id)
            .order_by(DigestItem.sort_order)
            .all())


def publish_newsletter(db, digest_id):
    """Publish a draft newsletter."""
    digest = db.query(Digest).filter(Digest.id == digest_id).first()
    if not digest: return False
    digest.status = 'sent'
    digest.sent_at = datetime.now()
    db.commit()
    return True


def unpublish_newsletter(db, digest_id):
    """Send a published newsletter back to draft for review."""
    digest = db.query(Digest).filter(Digest.id == digest_id).first()
    if not digest: return False
    digest.status = 'draft'
    digest.sent_at = None
    db.commit()
    return True


def get_latest_newsletter_summary(db, digest_id):
    """Get latest summary version for a newsletter."""
    return (db.query(DigestSummary)
            .filter(DigestSummary.digest_id == digest_id)
            .order_by(desc(DigestSummary.version))
            .first())


def get_original_newsletter_summary(db, digest_id):
    """Get version 1 (original) newsletter summary."""
    return (db.query(DigestSummary)
            .filter(DigestSummary.digest_id == digest_id,
                    DigestSummary.version == 1)
            .first())


def create_newsletter_summary_version(db, digest_id, content, user_id=None):
    """Create a new summary version for a newsletter."""
    max_ver = (db.query(sqla_func.max(DigestSummary.version))
               .filter(DigestSummary.digest_id == digest_id)
               .scalar()) or 0
    summary = DigestSummary(
        digest_id=digest_id,
        version=max_ver + 1,
        content=content,
        is_auto=False,
        created_by=user_id
    )
    db.add(summary)
    db.commit()
    return summary


def create_keyword_summary(db, query, article_count, user_id=None):
    """Create a pending keyword summary request."""
    ks = KeywordSummary(
        query=query,
        article_count=article_count,
        status='pending',
        requested_by=user_id
    )
    db.add(ks)
    db.commit()
    return ks


def get_keyword_summary(db, summary_id):
    """Fetch a keyword summary by id."""
    return db.query(KeywordSummary).filter(KeywordSummary.id == summary_id).first()


def get_recent_keyword_summaries(db, user_id=None, limit=10):
    """Fetch recent completed keyword summaries."""
    q = (db.query(KeywordSummary)
         .filter(KeywordSummary.status.in_(['complete', 'pending'])))
    if user_id:
        q = q.filter(KeywordSummary.requested_by == user_id)
    q = q.order_by(desc(KeywordSummary.created_at)).limit(limit)
    return q.all()


def delete_keyword_summary(db, summary_id):
    """Hard delete a keyword summary."""
    ks = db.query(KeywordSummary).filter(KeywordSummary.id == summary_id).first()
    if not ks: return False
    db.delete(ks)
    db.commit()
    return True

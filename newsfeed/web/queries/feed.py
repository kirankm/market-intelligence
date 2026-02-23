"""Feed page queries."""
from sqlalchemy import desc, or_, cast, String
from sqlalchemy import func as sqla_func
from sqlalchemy.orm import joinedload
from newsfeed.storage.models import Article, ArticleTag, ArticleStar, ArticleSummary, Tag
from newsfeed.storage.models import AppSetting, Source
from newsfeed.storage.models import ArticleSummary, CategorySummary
from datetime import datetime
from newsfeed.storage.models import Digest, DigestItem, DigestSummary, KeywordSummary


def get_setting(db, key, default='5'):
    """Fetch a setting value from app_settings."""
    row = db.query(AppSetting).filter(AppSetting.key == key).first()
    return row.value if row else default

def get_articles(db, limit=20, offset=0, tags=None, source=None, date_from=None, date_to=None):
    """Fetch articles, optionally filtered by tags and source."""
    q = (db.query(Article)
         .options(joinedload(Article.source),
                  joinedload(Article.tags).joinedload(ArticleTag.tag),
                  joinedload(Article.stars))
         .order_by(desc(Article.date)))
    if tags:
        q = (q.join(ArticleTag).join(Tag)
             .filter(Tag.name.in_(tags), ArticleTag.removed == False)
             .group_by(Article.id)
             .having(sqla_func.count(sqla_func.distinct(Tag.name)) == len(tags)))
    if source:
        q = q.join(Source).filter(Source.name == source)
    if date_from:
        q = q.filter(Article.date >= date_from)
    if date_to:
        q = q.filter(Article.date <= date_to)
    return q.limit(limit).offset(offset).all()

def get_starred_articles(db, limit=20, offset=0, tags=None, source=None, date_from=None, date_to=None):
    """Fetch articles that have at least one star."""
    q = (db.query(Article)
         .join(ArticleStar)
         .options(joinedload(Article.source),
                  joinedload(Article.tags).joinedload(ArticleTag.tag),
                  joinedload(Article.stars))
         .order_by(desc(Article.date)))
    if tags:
        q = (q.join(ArticleTag).join(Tag)
             .filter(Tag.name.in_(tags), ArticleTag.removed == False)
             .group_by(Article.id)
             .having(sqla_func.count(sqla_func.distinct(Tag.name)) == len(tags)))
    if source:
        q = q.join(Source).filter(Source.name == source)
    if date_from:
        q = q.filter(Article.date >= date_from)
    if date_to:
        q = q.filter(Article.date <= date_to)
    return q.limit(limit).offset(offset).all()

def get_article(db, article_id):
    """Fetch single article with relations."""
    return (db.query(Article)
            .options(joinedload(Article.source),
                     joinedload(Article.tags).joinedload(ArticleTag.tag),
                     joinedload(Article.stars))
            .filter(Article.id == article_id)
            .first())


def get_latest_summary(db, article_id):
    """Get latest summary for an article."""
    return (db.query(ArticleSummary)
            .filter(ArticleSummary.article_id == article_id)
            .order_by(desc(ArticleSummary.version))
            .first())


def article_tags(article):
    """Get active tag names for an article."""
    return [at.tag.name for at in article.tags if not at.removed]


def is_starred(article, user_id):
    """Check if user has starred this article."""
    return any(s.user_id == user_id for s in article.stars)


def toggle_star(db, article_id, user_id):
    """Toggle star — returns True if now starred, False if unstarred."""
    existing = (db.query(ArticleStar)
                .filter(ArticleStar.article_id == article_id,
                        ArticleStar.user_id == user_id)
                .first())
    if existing:
        db.delete(existing)
        db.commit()
        return False
    db.add(ArticleStar(article_id=article_id, user_id=user_id))
    db.commit()
    return True


def get_tags_with_counts(db):
    """Get all tags with their article counts."""
    return (db.query(Tag.name, sqla_func.count(ArticleTag.article_id).label('count'))
            .join(ArticleTag, Tag.id == ArticleTag.tag_id)
            .filter(ArticleTag.removed == False)
            .group_by(Tag.name)
            .order_by(sqla_func.count(ArticleTag.article_id).desc())
            .all())

def get_sources_with_counts(db):
    """Get all sources with their article counts."""
    return (db.query(Source.name, sqla_func.count(Article.id).label('count'))
            .join(Article, Source.id == Article.source_id)
            .group_by(Source.name)
            .order_by(Source.name)
            .all())

def search_articles(db, query, limit=20, offset=0):
    """Search articles by title, subtitle, and bullets using ILIKE."""
    term = f"%{query}%"
    return (db.query(Article)
            .outerjoin(ArticleSummary)
            .options(joinedload(Article.source),
                     joinedload(Article.tags).joinedload(ArticleTag.tag),
                     joinedload(Article.stars))
            .filter(or_(
                Article.title.ilike(term),
                ArticleSummary.subtitle.ilike(term),
                cast(ArticleSummary.bullets, String).ilike(term)))
            .order_by(desc(Article.date))
            .limit(limit).offset(offset)
            .all())

def get_starred_tags_with_counts(db):
    """Get tags with counts for starred articles only."""
    return (db.query(Tag.name, sqla_func.count(ArticleTag.article_id).label('count'))
            .join(ArticleTag, Tag.id == ArticleTag.tag_id)
            .join(ArticleStar, ArticleTag.article_id == ArticleStar.article_id)
            .filter(ArticleTag.removed == False)
            .group_by(Tag.name)
            .order_by(sqla_func.count(ArticleTag.article_id).desc())
            .all())


def get_starred_sources_with_counts(db):
    """Get sources with counts for starred articles only."""
    return (db.query(Source.name, sqla_func.count(Article.id).label('count'))
            .join(Article, Source.id == Article.source_id)
            .join(ArticleStar, Article.id == ArticleStar.article_id)
            .group_by(Source.name)
            .order_by(Source.name)
            .all())

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

def get_digests(db, status='sent'):
    """Fetch digests by status with item count."""
    return (db.query(Digest, sqla_func.count(DigestItem.id).label('item_count'))
            .outerjoin(DigestItem)
            .filter(Digest.status == status)
            .group_by(Digest.id)
            .order_by(desc(Digest.date_from))
            .all())


def get_digest_articles(db, digest_id):
    """Fetch articles in a digest, ordered by sort_order."""
    return (db.query(Article)
            .join(DigestItem, Article.id == DigestItem.article_id)
            .options(joinedload(Article.source),
                     joinedload(Article.tags).joinedload(ArticleTag.tag))
            .filter(DigestItem.digest_id == digest_id)
            .order_by(DigestItem.sort_order)
            .all())


def publish_digest(db, digest_id):
    """Publish a draft digest."""
    digest = db.query(Digest).filter(Digest.id == digest_id).first()
    if not digest: return False
    digest.status = 'sent'
    digest.sent_at = datetime.now()
    db.commit()
    return True

def unpublish_digest(db, digest_id):
    """Send a published digest back to draft for review."""
    digest = db.query(Digest).filter(Digest.id == digest_id).first()
    if not digest: return False
    digest.status = 'draft'
    digest.sent_at = None
    db.commit()
    return True

def get_latest_digest_summary(db, digest_id):
    """Get latest summary version for a digest."""
    return (db.query(DigestSummary)
            .filter(DigestSummary.digest_id == digest_id)
            .order_by(desc(DigestSummary.version))
            .first())


def get_original_digest_summary(db, digest_id):
    """Get version 1 (original) digest summary."""
    return (db.query(DigestSummary)
            .filter(DigestSummary.digest_id == digest_id,
                    DigestSummary.version == 1)
            .first())


def create_digest_summary_version(db, digest_id, content, user_id=None):
    """Create a new summary version for a digest."""
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


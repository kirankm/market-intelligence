"""Article queries — fetch, search, stars."""

from sqlalchemy import desc, or_, cast, String
from sqlalchemy import func as sqla_func
from sqlalchemy.orm import joinedload
from newsfeed.storage.models import (
    Article, ArticleTag, ArticleStar, ArticleSummary, Tag, Source
)


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

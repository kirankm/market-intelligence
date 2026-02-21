"""Feed page queries."""
from sqlalchemy import desc
from sqlalchemy.orm import joinedload
from newsfeed.storage.models import Article, ArticleTag, ArticleStar, ArticleSummary


def get_articles(db, limit=20, offset=0):
    """Fetch articles with source, newest first."""
    return (db.query(Article)
            .options(joinedload(Article.source),
                     joinedload(Article.tags).joinedload(ArticleTag.tag),
                     joinedload(Article.stars))
            .order_by(desc(Article.date))
            .limit(limit).offset(offset)
            .all())


def article_tags(article):
    """Get active tag names for an article."""
    return [at.tag.name for at in article.tags
            if not at.removed]


def is_starred(article, user_id):
    """Check if user has starred this article."""
    return any(s.user_id == user_id for s in article.stars)

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

"""Tag queries — counts, edits, add/remove."""

from sqlalchemy import func as sqla_func
from newsfeed.storage.models import (
    Article, ArticleTag, ArticleStar, Tag, Source, TagEdit
)


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


def get_all_tags(db):
    """Get all tag names sorted alphabetically, plus 'Other'."""
    tags = db.query(Tag).order_by(Tag.name).all()
    names = [t.name for t in tags]
    if 'Other' not in names:
        names.append('Other')
    return names


def add_tag_to_article(db, article_id, tag_name, user_id=None):
    """Add a tag to an article and log the edit."""
    tag = db.query(Tag).filter(Tag.name == tag_name).first()
    if not tag:
        tag = Tag(name=tag_name)
        db.add(tag)
        db.flush()

    existing = (db.query(ArticleTag)
                .filter(ArticleTag.article_id == article_id,
                        ArticleTag.tag_id == tag.id)
                .first())
    if existing:
        if existing.removed:
            existing.removed = False
            existing.removed_by = None
            existing.added_by = user_id
            existing.is_auto = False
    else:
        db.add(ArticleTag(
            article_id=article_id, tag_id=tag.id,
            is_auto=False, added_by=user_id
        ))

    db.add(TagEdit(article_id=article_id, tag_id=tag.id, action='add', user_id=user_id))
    db.commit()


def remove_tag_from_article(db, article_id, tag_name, user_id=None):
    """Soft-remove a tag from an article and log the edit."""
    tag = db.query(Tag).filter(Tag.name == tag_name).first()
    if not tag:
        return

    existing = (db.query(ArticleTag)
                .filter(ArticleTag.article_id == article_id,
                        ArticleTag.tag_id == tag.id,
                        ArticleTag.removed == False)
                .first())
    if existing:
        existing.removed = True
        existing.removed_by = user_id

    db.add(TagEdit(article_id=article_id, tag_id=tag.id, action='remove', user_id=user_id))
    db.commit()

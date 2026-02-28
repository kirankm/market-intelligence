"""Feed page queries."""
import subprocess
import sys

from sqlalchemy import desc, or_, cast, String
from sqlalchemy import func as sqla_func
from sqlalchemy.orm import joinedload
from newsfeed.storage.models import Article, ArticleTag, ArticleStar, ArticleSummary, Tag
from newsfeed.storage.models import AppSetting, Source
from newsfeed.storage.models import ArticleSummary, CategorySummary
from datetime import datetime
from newsfeed.storage.models import Digest, DigestItem, DigestSummary, KeywordSummary
from newsfeed.storage.models import User, Role, UserRole, PipelineRun, TagEdit

JOBS = {'key': 'pipeline', 'name': 'Pipeline Run', 'desc': 'Fetch articles from all sources',
 'cmd': [sys.executable, '-m', 'newsfeed.run'],
 'params': [
     {'name': 'from_date', 'label': 'From Date', 'placeholder': 'YYYY-MM-DD', 'arg': '--from'},
     {'name': 'to_date', 'label': 'To Date', 'placeholder': 'YYYY-MM-DD', 'arg': '--to'},
     {'name': 'max_pages', 'label': 'Max Pages', 'placeholder': '5', 'arg': '--max-pages'},
 ]},

JOBS = [
    {'key': 'pipeline', 'name': 'Pipeline Run', 'desc': 'Fetch articles from all sources',
     'cmd': [sys.executable, '-m', 'newsfeed.run'],
     'params': [
         {'name': 'from_date', 'label': 'From Date', 'placeholder': 'YYYY-MM-DD', 'arg': '--from'},
         {'name': 'to_date', 'label': 'To Date', 'placeholder': 'YYYY-MM-DD', 'arg': '--to'},
         {'name': 'max_pages', 'label': 'Max Pages', 'placeholder': '5', 'arg': '--max-pages'},
     ]},
     {'key': 'category_summarizer', 'name': 'Category Summarizer', 'desc': 'Generate category summaries',
     'cmd': [sys.executable, '-m', 'newsfeed.scripts.category_summaries']},
    {'key': 'digest_creator', 'name': 'Digest Creator', 'desc': 'Create weekly digest from starred articles',
     'cmd': [sys.executable, '-m', 'newsfeed.scripts.create_digest']},
    {'key': 'keyword_summarizer', 'name': 'Keyword Summarizer', 'desc': 'Process pending keyword summaries',
     'cmd': [sys.executable, '-m', 'newsfeed.web.scripts.keyword_summarizer', '--once']},
]

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

def delete_keyword_summary(db, summary_id):
    """Hard delete a keyword summary."""
    ks = db.query(KeywordSummary).filter(KeywordSummary.id == summary_id).first()
    if not ks: return False
    db.delete(ks)
    db.commit()
    return True

def get_all_settings(db):
    """Fetch all app settings."""
    return db.query(AppSetting).order_by(AppSetting.key).all()


def upsert_setting(db, key, value):
    """Insert or update a setting."""
    existing = db.query(AppSetting).filter(AppSetting.key == key).first()
    if existing:
        existing.value = value
    else:
        db.add(AppSetting(key=key, value=value))
    db.commit()


def delete_setting(db, key):
    """Delete a setting by key."""
    setting = db.query(AppSetting).filter(AppSetting.key == key).first()
    if setting:
        db.delete(setting)
        db.commit()
        return True
    return False

def get_all_users(db):
    """Fetch all users with their roles."""
    return (db.query(User)
            .options(joinedload(User.roles))
            .order_by(User.name)
            .all())


def get_all_roles(db):
    """Fetch all available roles."""
    return db.query(Role).order_by(Role.name).all()


def get_user_role_name(user):
    """Get primary role name for a user."""
    return user.roles[0].name if user.roles else 'none'


def create_user(db, name, email, role_name):
    """Create a new user with a role."""
    existing = db.query(User).filter(User.email == email).first()
    if existing: return None
    user = User(name=name, email=email)
    db.add(user)
    db.flush()
    role = db.query(Role).filter(Role.name == role_name).first()
    if role:
        db.add(UserRole(user_id=user.id, role_id=role.id))
    db.commit()
    return user


def update_user_role(db, user_id, new_role_name):
    """Update a user's role."""
    db.query(UserRole).filter(UserRole.user_id == user_id).delete()
    role = db.query(Role).filter(Role.name == new_role_name).first()
    if role:
        db.add(UserRole(user_id=user_id, role_id=role.id))
    db.commit()


def delete_user(db, user_id):
    """Hard delete a user."""
    user = db.query(User).filter(User.id == user_id).first()
    if not user: return False
    db.delete(user)
    db.commit()
    return True

def get_all_sources(db):
    """Fetch all sources."""
    return db.query(Source).order_by(Source.name).all()


def toggle_source_active(db, source_id):
    """Toggle a source's active status."""
    source = db.query(Source).filter(Source.id == source_id).first()
    if not source: return False
    source.is_active = not source.is_active
    db.commit()
    return source.is_active

def get_cost_by_source(db, date_from=None, date_to=None):
    """Aggregate cost per source within date range."""
    q = (db.query(
            Source.name,
            sqla_func.sum(PipelineRun.articles_fetched).label('articles'),
            sqla_func.sum(PipelineRun.input_tokens).label('input_tokens'),
            sqla_func.sum(PipelineRun.output_tokens).label('output_tokens'),
            sqla_func.sum(PipelineRun.cost).label('cost'),
            sqla_func.max(PipelineRun.run_at).label('last_run'))
         .join(PipelineRun, Source.id == PipelineRun.source_id)
         .group_by(Source.name)
         .order_by(Source.name))
    if date_from:
        q = q.filter(PipelineRun.run_at >= date_from)
    if date_to:
        q = q.filter(PipelineRun.run_at <= date_to)
    return q.all()


def get_cost_totals(db, date_from=None, date_to=None):
    """Aggregate total cost across all sources."""
    q = (db.query(
            sqla_func.sum(PipelineRun.articles_fetched).label('articles'),
            sqla_func.sum(PipelineRun.input_tokens).label('input_tokens'),
            sqla_func.sum(PipelineRun.output_tokens).label('output_tokens'),
            sqla_func.sum(PipelineRun.cost).label('cost')))
    if date_from:
        q = q.filter(PipelineRun.run_at >= date_from)
    if date_to:
        q = q.filter(PipelineRun.run_at <= date_to)
    return q.first()

def get_job_status(db, job_key):
    """Get status and last run for a job."""
    status = get_setting(db, f'job_{job_key}_status', 'idle')
    last_run = get_setting(db, f'job_{job_key}_last_run', 'Never')
    last_result = get_setting(db, f'job_{job_key}_result', '')
    return status, last_run, last_result


def set_job_running(db, job_key):
    """Mark a job as running."""
    upsert_setting(db, f'job_{job_key}_status', 'running')

def run_job_background(job_key, cmd, params=None):
    """Spawn a job in the background with optional params."""
    full_cmd = list(cmd)
    if params:
        job = next((j for j in JOBS if j['key'] == job_key), None)
        if job:
            for p in job.get('params', []):
                val = params.get(p['name'], '').strip()
                if val:
                    full_cmd.extend([p['arg'], val])
    subprocess.Popen(full_cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

def set_job_complete(db, job_key, success=True, error=''):
    """Mark a job as done or failed."""
    from datetime import datetime
    upsert_setting(db, f'job_{job_key}_status', 'done' if success else 'failed')
    upsert_setting(db, f'job_{job_key}_last_run', datetime.now().strftime('%b %d, %H:%M'))
    upsert_setting(db, f'job_{job_key}_result', error if not success else '')


def get_all_tags(db):
    """Get all tag names sorted alphabetically, plus 'Other'."""
    tags = db.query(Tag).order_by(Tag.name).all()
    names = [t.name for t in tags]
    if 'Other' not in names:
        names.append('Other')
    return names


def add_tag_to_article(db, article_id, tag_name, user_id=None):
    """Add a tag to an article and log the edit."""
    # Get or create the tag
    tag = db.query(Tag).filter(Tag.name == tag_name).first()
    if not tag:
        tag = Tag(name=tag_name)
        db.add(tag)
        db.flush()

    # Check if already exists (including soft-removed)
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

    # Log the edit
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

    # Log the edit
    db.add(TagEdit(article_id=article_id, tag_id=tag.id, action='remove', user_id=user_id))
    db.commit()

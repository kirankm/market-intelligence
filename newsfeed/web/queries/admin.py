"""Admin queries — jobs, sources, costs."""

import subprocess
import sys
from datetime import datetime

from sqlalchemy import func as sqla_func
from newsfeed.storage.models import Source, PipelineRun
from newsfeed.web.queries.settings import get_setting, upsert_setting

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
    upsert_setting(db, f'job_{job_key}_status', 'done' if success else 'failed')
    upsert_setting(db, f'job_{job_key}_last_run', datetime.now().strftime('%b %d, %H:%M'))
    upsert_setting(db, f'job_{job_key}_result', error if not success else '')

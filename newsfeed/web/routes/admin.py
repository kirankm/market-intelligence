"""Admin dashboard routes."""
from fasthtml.common import *
from fasthtml.core import APIRouter
from newsfeed.web.components.nav import navbar
from newsfeed.storage.models import User

from newsfeed.web.components.cards import (
    admin_ribbon, settings_table, settings_edit_row,
    users_table, user_edit_row, sources_table, costs_table, jobs_table
)
from newsfeed.web.queries.feed import (
    get_all_settings, get_setting, upsert_setting, delete_setting,
    get_all_users, get_all_roles, get_user_role_name,
    create_user, update_user_role, delete_user,
    get_all_sources, toggle_source_active,
    get_cost_by_source, get_cost_totals,
    JOBS, get_job_status, set_job_running, run_job_background
)
from newsfeed.web.filters import date_range

ar = APIRouter()

PAGE = "max-w-5xl mx-auto bg-background"
PAGE_PADDING = "px-6 py-4"
TEXT_EMPTY = "text-sm text-muted-foreground italic"

def cost_date_range(period):
    """Convert cost period to date range."""
    if period == 'all': return None, None
    return date_range(period)

def tab_content(db, tab, **kwargs):
    """Render content for the active tab."""
    if tab == 'settings': return settings_table(get_all_settings(db))
    if tab == 'users': return users_table(get_all_users(db), get_user_role_name)
    if tab == 'sources': return sources_table(get_all_sources(db))
    if tab == 'costs':
        period = kwargs.get('period', 'all')
        d_from, d_to = cost_date_range(period)
        rows = get_cost_by_source(db, d_from, d_to)
        totals = get_cost_totals(db, d_from, d_to)
        return costs_table(rows, totals, period)
    if tab == 'jobs':
        return jobs_table(JOBS, lambda key: get_job_status(db, key))
    return P("Unknown tab", cls=TEXT_EMPTY)

def admin_content(db, tab='settings', **kwargs):
    """Ribbon + tab content — HTMX target."""
    return Div(admin_ribbon(tab), tab_content(db, tab, **kwargs), id="admin-content")

def admin_page(session, db, tab='settings'):
    """Render admin dashboard."""
    return Div(
        navbar(session, '/admin/sources'),
        Div(admin_content(db, tab), cls=PAGE_PADDING),
        cls=PAGE
    )


@ar('/admin/sources')
def get(session, request, tab: str = 'settings'):
    db = request.state.db
    return admin_page(session, db, tab)


@ar('/admin/tab/{tab}')
def get(tab: str, session, request, period: str = 'all'):
    db = request.state.db
    return admin_content(db, tab, period=period)


@ar('/admin/settings/{key}/edit')
def get(key: str, session, request):
    db = request.state.db
    value = get_setting(db, key, '')
    return settings_edit_row(key, value)


@ar('/admin/settings/{key}/save')
def post(key: str, session, request, value: str = ''):
    db = request.state.db
    upsert_setting(db, key, value)
    return admin_content(db, 'settings')


@ar('/admin/settings/{key}/delete')
def delete(key: str, session, request):
    db = request.state.db
    delete_setting(db, key)
    return admin_content(db, 'settings')


@ar('/admin/settings/add')
def post(session, request, key: str = '', value: str = ''):
    db = request.state.db
    if key: upsert_setting(db, key, value)
    return admin_content(db, 'settings')

@ar('/admin/users/{user_id}/edit')
def get(user_id: int, session, request):
    db = request.state.db
    user = db.query(User).filter(User.id == user_id).first()
    if not user: return P("Not found", cls=TEXT_ERROR)
    return user_edit_row(user, get_user_role_name(user))


@ar('/admin/users/{user_id}/save')
def post(user_id: int, session, request, role: str = ''):
    db = request.state.db
    update_user_role(db, user_id, role)
    return admin_content(db, 'users')


@ar('/admin/users/{user_id}/delete')
def delete(user_id: int, session, request):
    db = request.state.db
    delete_user(db, user_id)
    return admin_content(db, 'users')


@ar('/admin/users/add')
def post(session, request, name: str = '', email: str = '', role: str = ''):
    db = request.state.db
    if name and email:
        create_user(db, name, email, role)
    return admin_content(db, 'users')

@ar('/admin/sources/{source_id}/toggle')
def post(source_id: int, session, request):
    db = request.state.db
    toggle_source_active(db, source_id)
    return admin_content(db, 'sources')

@ar('/admin/jobs/{job_key}/run')
def post(job_key: str, session, request, from_date: str = '', to_date: str = '', max_pages: str = ''):
    db = request.state.db
    job = next((j for j in JOBS if j['key'] == job_key), None)
    if not job: return admin_content(db, 'jobs')
    set_job_running(db, job_key)
    params = {'from_date': from_date, 'to_date': to_date, 'max_pages': max_pages}
    run_job_background(job_key, job['cmd'], params)
    return admin_content(db, 'jobs')

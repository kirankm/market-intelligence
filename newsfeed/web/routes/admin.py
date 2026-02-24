"""Admin dashboard routes."""
from fasthtml.common import *
from fasthtml.core import APIRouter
from newsfeed.web.components.nav import navbar
from newsfeed.web.components.cards import (
    admin_ribbon, settings_table, settings_edit_row
)
from newsfeed.web.queries.feed import (
    get_all_settings, get_setting, upsert_setting, delete_setting
)

ar = APIRouter()

PAGE = "max-w-5xl mx-auto bg-background"
PAGE_PADDING = "px-6 py-4"
TEXT_EMPTY = "text-sm text-muted-foreground italic"


def tab_content(db, tab):
    """Render content for the active tab."""
    if tab == 'settings': return settings_table(get_all_settings(db))
    if tab == 'costs': return P("Cost tracking coming soon", cls=TEXT_EMPTY)
    if tab == 'sources': return P("Source health coming soon", cls=TEXT_EMPTY)
    if tab == 'users': return P("User management coming soon", cls=TEXT_EMPTY)
    if tab == 'jobs': return P("Job management coming soon", cls=TEXT_EMPTY)
    return P("Unknown tab", cls=TEXT_EMPTY)


def admin_content(db, tab='settings'):
    """Ribbon + tab content — HTMX target."""
    return Div(admin_ribbon(tab), tab_content(db, tab), id="admin-content")


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
def get(tab: str, session, request):
    db = request.state.db
    return admin_content(db, tab)


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

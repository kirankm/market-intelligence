"""Executive dashboard routes."""
from fasthtml.common import *
from fasthtml.core import APIRouter
from newsfeed.web.components.nav import navbar
from newsfeed.web.filters import FilterState, date_range

from newsfeed.web.components.cards import (
    collapsible_section, article_card, tag_filter, source_filter,
    date_filter, category_period_dropdown, category_card,
    digest_ribbon, digest_item, digest_expanded,
    digest_summary_display, digest_summary_edit_form,
    exec_search_box, exec_search_results, keyword_summaries_list
)
from newsfeed.web.queries.feed import (
    get_starred_articles, get_tags_with_counts, get_sources_with_counts,
    get_setting, article_tags, is_starred, get_starred_tags_with_counts,
    get_starred_sources_with_counts, get_category_summaries,
    get_category_article_counts, get_category_star_counts,
    get_available_summary_periods, get_digests,
    publish_digest, unpublish_digest, get_latest_digest_summary,
    get_original_digest_summary, create_digest_summary_version,
    search_articles, create_keyword_summary, get_keyword_summary,
    get_recent_keyword_summaries
)

ar = APIRouter()

PAGE = "max-w-5xl mx-auto bg-background"
PAGE_PADDING = "px-6 py-4"
FILTER_BAR = "mb-4 flex flex-col gap-3"
TEXT_EMPTY = "text-sm text-muted-foreground italic"
TEXT_ERROR = "text-sm text-destructive"

def starred_filters(db, state):
    """Render filters for starred section."""
    tags = get_starred_tags_with_counts(db)
    sources = get_starred_sources_with_counts(db)
    top_n = int(get_setting(db, 'top_tags_count', '5'))
    return Div(
        tag_filter(tags, state, top_n),
        Div(source_filter(sources, state), date_filter(state),
            cls="flex items-center gap-6"),
        cls=FILTER_BAR
    )


def starred_list(db, user_id, state):
    """Build starred article card list."""
    d_from, d_to = date_range(state.date)
    articles = get_starred_articles(db, tags=state.tags, source=state.source,
                                     date_from=d_from, date_to=d_to)
    cards = [article_card(a, article_tags(a), is_starred(a, user_id))
             for a in articles]
    if not cards: return P("No starred articles", cls=TEXT_EMPTY)
    return Div(*cards)


def starred_content(db, user_id, state):
    """Filters + starred articles — HTMX target."""
    return Div(starred_filters(db, state),
               starred_list(db, user_id, state),
               id="starred-content")

def section_category_summaries(db, period_from=None, period_to=None):
    """Category summaries section content."""
    periods = get_available_summary_periods(db)
    if not periods: return P("No summaries available", cls=TEXT_EMPTY)
    if not period_from:
        period_from, period_to = periods[0]
    tag_names_str = get_setting(db, 'summary_categories', '')
    tag_names = [t.strip() for t in tag_names_str.split(',') if t.strip()]
    if not tag_names: return P("No categories configured", cls=TEXT_EMPTY)
    summaries = get_category_summaries(db, tag_names, period_from, period_to)
    article_counts = dict(get_category_article_counts(db, tag_names, period_from, period_to))
    star_counts = dict(get_category_star_counts(db, tag_names, period_from, period_to))
    cards = [category_card(name, summary.summary or "No summary",
                           article_counts.get(name, 0), star_counts.get(name, 0))
             for summary, name in summaries]
    return Div(
        category_period_dropdown(periods, period_from, period_to),
        *cards if cards else [P("No summaries for this period", cls=TEXT_EMPTY)],
        id="categories-content"
    )

def section_keyword_search(db, search='', user_id=None):
    """Keyword search section with summarize option and saved summaries."""
    min_for_summary = int(get_setting(db, 'min_articles_for_summary', '5'))
    articles = search_articles(db, search) if search else []
    summaries = get_recent_keyword_summaries(db, user_id)
    return Div(
        exec_search_box(search),
        Div(exec_search_results(articles, search, article_tags, min_for_summary),
            id="search-results"),
        keyword_summaries_list(summaries),
        id="search-content"
    )

def section_starred(db, user_id):
    """Starred by team section with filters."""
    state = FilterState(base='/executive/starred', target='starred-content')
    return starred_content(db, user_id, state)

def section_digests(db, active_tab='draft'):
    """Recent digests section with ribbon tabs."""
    drafts = get_digests(db, 'draft')
    sent = get_digests(db, 'sent')
    items = drafts if active_tab == 'draft' else sent
    show_publish = active_tab == 'draft'
    digest_cards = [digest_item(d, count, show_publish) for d, count in items]
    if not digest_cards:
        digest_cards = [P("No digests", cls=TEXT_EMPTY)]
    return Div(
        digest_ribbon(len(drafts), len(sent), active_tab),
        *digest_cards,
        id="digests-content"
    )

def executive_page(session, db):
    user_id = session.get('user_id')
    return Div(
        navbar(session, '/executive'),
        Div(
            collapsible_section("Category Summaries", section_category_summaries(db),
                                "categories", open=True),
            collapsible_section("Keyword Search", section_keyword_search(db, user_id=user_id),
                                "search", open=False),
            collapsible_section("Starred by Team", section_starred(db, user_id),
                                "starred", open=False),
            collapsible_section("Recent Digests", section_digests(db),
                                "digests", open=False),
            cls=PAGE_PADDING
        ),
        cls=PAGE
    )

@ar('/executive')
def get(session, request):
    return executive_page(session, request.state.db)


@ar('/executive/section/{section_id}')
def get(section_id: str, session, request, open: str = '1'):
    db = request.state.db
    user_id = session.get('user_id')
    is_open = open == '1'
    sections = {
        'categories': ("Category Summaries", section_category_summaries(db)),
        'search':     ("Keyword Search", section_keyword_search(db, user_id=user_id)),
        'starred':    ("Starred by Team", section_starred(db, user_id)),
        'digests':    ("Recent Digests", section_digests(db)),
    }
    title, content = sections.get(section_id, ("Unknown", P("Not found")))
    return collapsible_section(title, content, section_id, open=is_open)


@ar('/executive/starred')
def get(session, request, tags: str = '', source: str = '', date: str = '', expanded: str = '0'):
    db = request.state.db
    state = FilterState.from_request(tags, source, date, expanded=expanded,
                                     base='/executive/starred', target='starred-content')
    user_id = session.get('user_id')
    return starred_content(db, user_id, state)

@ar('/executive/categories')
def get(session, request, period: str = ''):
    db = request.state.db
    period_from, period_to = None, None
    if period and '|' in period:
        parts = period.split('|')
        from datetime import date
        period_from = date.fromisoformat(parts[0])
        period_to = date.fromisoformat(parts[1])
    return section_category_summaries(db, period_from, period_to)

@ar('/executive/digests')
def get(session, request, tab: str = 'draft'):
    db = request.state.db
    return section_digests(db, tab)

@ar('/executive/digests/{digest_id}/expand')
def get(digest_id: int, session, request, tab: str = 'draft'):
    db = request.state.db
    digests = get_digests(db, tab)
    digest_match = [(d, c) for d, c in digests if d.id == digest_id]
    if not digest_match: return P("Not found")
    digest, count = digest_match[0]
    summary = get_latest_digest_summary(db, digest_id)
    return digest_expanded(digest, count, summary, show_publish=(tab == 'draft'))

@ar('/executive/digests/{digest_id}/collapse')
def get(digest_id: int, session, request, tab: str = 'draft'):
    db = request.state.db
    digests = get_digests(db, tab)
    digest_match = [(d, c) for d, c in digests if d.id == digest_id]
    if not digest_match: return P("Not found")
    digest, count = digest_match[0]
    return digest_item(digest, count, show_publish=(tab == 'draft'))


@ar('/executive/digests/{digest_id}/publish')
def post(digest_id: int, session, request):
    db = request.state.db
    publish_digest(db, digest_id)
    return section_digests(db, 'sent')

@ar('/executive/digests/{digest_id}/review')
def post(digest_id: int, session, request):
    db = request.state.db
    unpublish_digest(db, digest_id)
    return section_digests(db, 'draft')

@ar('/executive/digests/{digest_id}/edit')
def get(digest_id: int, session, request):
    db = request.state.db
    summary = get_latest_digest_summary(db, digest_id)
    return digest_summary_edit_form(digest_id, summary)


@ar('/executive/digests/{digest_id}/save')
def post(digest_id: int, session, request, content: str = ''):
    db = request.state.db
    user_id = session.get('user_id')
    summary = create_digest_summary_version(db, digest_id, content, user_id)
    return digest_summary_display(digest_id, summary, show_edit=True)


@ar('/executive/digests/{digest_id}/revert')
def post(digest_id: int, session, request):
    db = request.state.db
    user_id = session.get('user_id')
    original = get_original_digest_summary(db, digest_id)
    if not original: return P("No original found", cls=TEXT_ERROR)
    summary = create_digest_summary_version(db, digest_id, original.content, user_id)
    return digest_summary_display(digest_id, summary, show_edit=True)


@ar('/executive/digests/{digest_id}/cancel')
def get(digest_id: int, session, request):
    db = request.state.db
    summary = get_latest_digest_summary(db, digest_id)
    return digest_summary_display(digest_id, summary, show_edit=True)

@ar('/executive/search')
def get(session, request, search: str = ''):
    db = request.state.db
    min_for_summary = int(get_setting(db, 'min_articles_for_summary', '5'))
    articles = search_articles(db, search) if search else []
    return Div(exec_search_results(articles, search, article_tags, min_for_summary),
               id="search-results")

@ar('/executive/search/summaries')
def get(session, request):
    db = request.state.db
    user_id = session.get('user_id')
    summaries = get_recent_keyword_summaries(db, user_id)
    return keyword_summaries_list(summaries)

@ar('/executive/search/summarize')
def post(session, request, search: str = ''):
    db = request.state.db
    user_id = session.get('user_id')
    articles = search_articles(db, search) if search else []
    create_keyword_summary(db, search, len(articles), user_id)
    summaries = get_recent_keyword_summaries(db, user_id)
    return keyword_summaries_list(summaries)

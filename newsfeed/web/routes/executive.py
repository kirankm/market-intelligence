"""Executive dashboard routes."""
from datetime import date as date_type
from fasthtml.common import *
from fasthtml.core import APIRouter

from newsfeed.web.components.nav import navbar
from newsfeed.web.filters import FilterState, date_range

from newsfeed.web.components.cards import (
    collapsible_section, article_card, tag_filter, source_filter,
    date_filter, category_period_dropdown, category_card,
    newsletter_ribbon, newsletter_date_range_form,
    newsletter_item, newsletter_expanded,
    newsletter_summary_display, newsletter_summary_edit_form,
    exec_search_box, exec_search_results, keyword_summaries_list,
    category_ribbon, category_tab, keyword_summary_item
)
from newsfeed.web.queries.feed import (
    get_starred_articles, get_tags_with_counts, get_sources_with_counts,
    get_setting, article_tags, is_starred, get_starred_tags_with_counts,
    get_starred_sources_with_counts, get_category_summaries,
    get_category_article_counts, get_category_star_counts,
    get_available_summary_periods, get_newsletters,
    publish_newsletter, unpublish_newsletter, get_latest_newsletter_summary,
    get_original_newsletter_summary, create_newsletter_summary_version,
    search_articles, create_keyword_summary, get_keyword_summary,
    get_recent_keyword_summaries, delete_keyword_summary
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

def section_category_summaries(db, period_from=None, period_to=None, active_category=None):
    """Category summaries section content."""
    periods = get_available_summary_periods(db)
    if not periods: return P("No summaries available", cls=TEXT_EMPTY)
    if not period_from:
        period_from, period_to = periods[0]
    tag_names_str = get_setting(db, 'summary_categories', '')
    tag_names = [t.strip() for t in tag_names_str.split(',') if t.strip()]
    if not tag_names: return P("No categories configured", cls=TEXT_EMPTY)
    if not active_category:
        active_category = tag_names[0]
    summaries = get_category_summaries(db, tag_names, period_from, period_to)
    article_counts = dict(get_category_article_counts(db, tag_names, period_from, period_to))
    star_counts = dict(get_category_star_counts(db, tag_names, period_from, period_to))
    summary_map = {name: s.summary or "No summary" for s, name in summaries}
    card = category_card(
        active_category,
        summary_map.get(active_category, "No summary for this category"),
        article_counts.get(active_category, 0),
        star_counts.get(active_category, 0)
    ) if active_category else None
    return Div(
        category_period_dropdown(periods, period_from, period_to),
        category_ribbon(tag_names, active_category, period_from, period_to),
        card,
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

def section_newsletters(db, active_tab='draft'):
    """Newsletters section with ribbon tabs and date range form."""
    drafts = get_newsletters(db, 'draft')
    sent = get_newsletters(db, 'sent')
    items = drafts if active_tab == 'draft' else sent
    show_publish = active_tab == 'draft'
    newsletter_cards = [newsletter_item(d, count, show_publish) for d, count in items]
    if not newsletter_cards:
        newsletter_cards = [P("No newsletters", cls=TEXT_EMPTY)]
    return Div(
        newsletter_date_range_form(),
        newsletter_ribbon(len(drafts), len(sent), active_tab),
        *newsletter_cards,
        id="newsletters-content"
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
            collapsible_section("Newsletters", section_newsletters(db),
                                "newsletters", open=False),
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
        'newsletters': ("Newsletters", section_newsletters(db)),
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
def get(session, request, period: str = '', category: str = ''):
    db = request.state.db
    period_from, period_to = None, None
    if period and '|' in period:
        parts = period.split('|')
        period_from = date_type.fromisoformat(parts[0])
        period_to = date_type.fromisoformat(parts[1])
    return section_category_summaries(db, period_from, period_to, active_category=category or None)

@ar('/executive/newsletters')
def get(session, request, tab: str = 'draft'):
    db = request.state.db
    return section_newsletters(db, tab)

@ar('/executive/newsletters/generate')
def post(session, request, from_date: str = '', to_date: str = ''):
    """Generate a newsletter for the given date range."""
    db = request.state.db
    try:
        if not from_date or not to_date:
            return Div(P("Please select both From and To dates", cls=TEXT_ERROR),
                       section_newsletters(db))
        d_from = date_type.fromisoformat(from_date)
        d_to = date_type.fromisoformat(to_date)
        from newsfeed.scripts.create_newsletter import create_newsletter
        result = create_newsletter(db, d_from, d_to)
        if not result:
            return Div(P("Newsletter already exists for this range or no starred articles found",
                        cls=TEXT_ERROR),
                       section_newsletters(db))
        return section_newsletters(db)
    except Exception as e:
        return Div(P(f"Error: {e}", cls=TEXT_ERROR), section_newsletters(db))

@ar('/executive/newsletters/{newsletter_id}/expand')
def get(newsletter_id: int, session, request, tab: str = 'draft'):
    db = request.state.db
    newsletters = get_newsletters(db, tab)
    match = [(d, c) for d, c in newsletters if d.id == newsletter_id]
    if not match: return P("Not found")
    newsletter, count = match[0]
    summary = get_latest_newsletter_summary(db, newsletter_id)
    return newsletter_expanded(newsletter, count, summary, show_publish=(tab == 'draft'))

@ar('/executive/newsletters/{newsletter_id}/collapse')
def get(newsletter_id: int, session, request, tab: str = 'draft'):
    db = request.state.db
    newsletters = get_newsletters(db, tab)
    match = [(d, c) for d, c in newsletters if d.id == newsletter_id]
    if not match: return P("Not found")
    newsletter, count = match[0]
    return newsletter_item(newsletter, count, show_publish=(tab == 'draft'))


@ar('/executive/newsletters/{newsletter_id}/publish')
def post(newsletter_id: int, session, request):
    db = request.state.db
    publish_newsletter(db, newsletter_id)
    return section_newsletters(db, 'sent')

@ar('/executive/newsletters/{newsletter_id}/review')
def post(newsletter_id: int, session, request):
    db = request.state.db
    unpublish_newsletter(db, newsletter_id)
    return section_newsletters(db, 'draft')

@ar('/executive/newsletters/{newsletter_id}/edit')
def get(newsletter_id: int, session, request):
    db = request.state.db
    summary = get_latest_newsletter_summary(db, newsletter_id)
    return newsletter_summary_edit_form(newsletter_id, summary)


@ar('/executive/newsletters/{newsletter_id}/save')
def post(newsletter_id: int, session, request, content: str = ''):
    db = request.state.db
    user_id = session.get('user_id')
    summary = create_newsletter_summary_version(db, newsletter_id, content, user_id)
    return newsletter_summary_display(newsletter_id, summary, show_edit=True)


@ar('/executive/newsletters/{newsletter_id}/revert')
def post(newsletter_id: int, session, request):
    db = request.state.db
    user_id = session.get('user_id')
    original = get_original_newsletter_summary(db, newsletter_id)
    if not original: return P("No original found", cls=TEXT_ERROR)
    summary = create_newsletter_summary_version(db, newsletter_id, original.content, user_id)
    return newsletter_summary_display(newsletter_id, summary, show_edit=True)


@ar('/executive/newsletters/{newsletter_id}/cancel')
def get(newsletter_id: int, session, request):
    db = request.state.db
    summary = get_latest_newsletter_summary(db, newsletter_id)
    return newsletter_summary_display(newsletter_id, summary, show_edit=True)

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

@ar('/executive/categories/select')
def get(session, request, category: str = '', period: str = ''):
    db = request.state.db
    period_from, period_to = None, None
    if period and '|' in period:
        parts = period.split('|')
        period_from = date_type.fromisoformat(parts[0])
        period_to = date_type.fromisoformat(parts[1])
    return section_category_summaries(db, period_from, period_to, active_category=category)

@ar('/executive/search/summary/{summary_id}/toggle')
def get(summary_id: int, session, request, expanded: str = '1'):
    db = request.state.db
    ks = get_keyword_summary(db, summary_id)
    if not ks: return P("Not found", cls=TEXT_ERROR)
    return keyword_summary_item(ks, expanded=expanded == '1')

@ar('/executive/search/summary/{summary_id}/delete')
def delete(summary_id: int, session, request):
    db = request.state.db
    user_id = session.get('user_id')
    delete_keyword_summary(db, summary_id)
    summaries = get_recent_keyword_summaries(db, user_id)
    return keyword_summaries_list(summaries)

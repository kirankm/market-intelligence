"""Analyst feed routes."""
from fasthtml.common import *
from fasthtml.core import APIRouter
from newsfeed.web.components.nav import navbar
from newsfeed.web.components.cards import (
    article_card, expanded_card, star_icon, tag_filter, source_filter, date_filter,
    search_box, load_more_sentinel, tag_editor, tag_display
)
from newsfeed.web.queries.feed import (
    get_articles, get_article, get_latest_summary,
    article_tags, is_starred, toggle_star,
    get_tags_with_counts, get_sources_with_counts, get_setting, search_articles,
    get_all_tags, add_tag_to_article, remove_tag_from_article
)
from newsfeed.web.filters import FilterState, date_range
from newsfeed.storage.models import Article

ar = APIRouter()

PAGE = "max-w-5xl mx-auto bg-background"
PAGE_PADDING = "px-6 py-4"
FILTER_BAR = "mb-4 flex flex-col gap-3"

COLLAPSE_SCRIPT = Script("""
function collapseExpanded(el) {
    const exp = document.querySelector('.expanded');
    if (!exp) return;
    const clickedCard = el.closest('[id^=article-]');
    if (exp.id === clickedCard.id) return;
    const id = exp.id.replace('article-', '');
    htmx.ajax('GET', '/feed/article/' + id + '/collapse',
              {target: '#' + exp.id, swap: 'outerHTML'});
}
""")

def article_list(db, user_id, state):
    """Build article card list."""
    page_size = int(get_setting(db, 'page_size', '20'))
    if state.search:
        articles = search_articles(db, state.search, limit=page_size)
    else:
        d_from, d_to = date_range(state.date)
        articles = get_articles(db, limit=page_size, tags=state.tags,
                                source=state.source, date_from=d_from, date_to=d_to)
    cards = [article_card(a, article_tags(a), is_starred(a, user_id), state.search)
             for a in articles]
    if len(articles) == page_size:
        cards.append(load_more_sentinel(state, page_size, page_size))
    return Div(*cards, id="article-list")

def feed_filters(db, state):
    """Render all filter controls."""
    tags = get_tags_with_counts(db)
    sources = get_sources_with_counts(db)
    top_n = int(get_setting(db, 'top_tags_count', '5'))
    debounce = int(get_setting(db, 'search_debounce_ms', '300'))
    return Div(
        search_box(state, debounce),
        tag_filter(tags, state, top_n),
        Div(source_filter(sources, state), date_filter(state),
            cls="flex items-center gap-6"),
        cls=FILTER_BAR
    )

def feed_content(db, user_id, state):
    """Filters + article list — HTMX reload target."""
    return Div(feed_filters(db, state),
               article_list(db, user_id, state),
               id="feed-content")

def feed_page(session, db, state):
    """Render feed page shell."""
    user_id = session.get('user_id')
    return Div(
        navbar(session, '/feed'),
        COLLAPSE_SCRIPT,
        Div(feed_content(db, user_id, state), cls=PAGE_PADDING),
        cls=PAGE
    )

@ar('/feed')
def get(session, request, tags: str = '', expanded: str = '0', source: str = '', date: str = '', search: str = ''):
    db = request.state.db
    state = FilterState.from_request(tags, source, date, search, expanded)
    if request.headers.get('HX-Request'):
        return feed_content(db, session.get('user_id'), state)
    return feed_page(session, db, state)

@ar('/feed/article/{article_id}/expand')
def get(article_id: int, session, request, search: str = ''):
    db = request.state.db
    article = get_article(db, article_id)
    summary = get_latest_summary(db, article_id)
    user_id = session.get('user_id')
    return expanded_card(article, article_tags(article), is_starred(article, user_id), summary, search)

@ar('/feed/article/{article_id}/collapse')
def get(article_id: int, session, request):
    db = request.state.db
    article = get_article(db, article_id)
    user_id = session.get('user_id')
    return article_card(article, article_tags(article), is_starred(article, user_id))


@ar('/feed/article/{article_id}/star')
def post(article_id: int, session, request):
    db = request.state.db
    user_id = session.get('user_id')
    starred = toggle_star(db, article_id, user_id)
    return star_icon(starred, article_id)

@ar('/feed/more')
def get(session, request, tags: str = '', source: str = '', date: str = '',
        search: str = '', offset: int = 0, page_size: int = 20):
    db = request.state.db
    state = FilterState.from_request(tags, source, date, search)
    user_id = session.get('user_id')
    if state.search:
        articles = search_articles(db, state.search, limit=page_size, offset=offset)
    else:
        d_from, d_to = date_range(state.date)
        articles = get_articles(db, limit=page_size, offset=offset,
                                tags=state.tags, source=state.source,
                                date_from=d_from, date_to=d_to)
    cards = [article_card(a, article_tags(a), is_starred(a, user_id), state.search)
             for a in articles]
    if len(articles) == page_size:
        cards.append(load_more_sentinel(state, offset + page_size, page_size))
    return Div(*cards)

@ar('/feed/article/{article_id}/tags/edit')
def get(article_id: int, request):
    """Show tag editor for an article."""
    db = request.state.db
    current_tags = article_tags(db.query(Article).get(article_id))
    all_tags = get_all_tags(db)
    return tag_editor(article_id, current_tags, all_tags)

@ar('/feed/article/{article_id}/tags/add')
def post(article_id: int, session, request, tag_name: str = '', free_text: str = ''):
    """Add a tag to an article."""
    db = request.state.db
    user_id = session.get('user_id')
    name = free_text.strip() if tag_name == 'Other' and free_text.strip() else tag_name
    if name:
        add_tag_to_article(db, article_id, name, user_id)
    current_tags = article_tags(db.query(Article).get(article_id))
    all_tags = get_all_tags(db)
    return tag_editor(article_id, current_tags, all_tags)

@ar('/feed/article/{article_id}/tags/remove')
def post(article_id: int, session, request, tag_name: str = ''):
    """Remove a tag from an article."""
    db = request.state.db
    user_id = session.get('user_id')
    if tag_name:
        remove_tag_from_article(db, article_id, tag_name, user_id)
    current_tags = article_tags(db.query(Article).get(article_id))
    all_tags = get_all_tags(db)
    return tag_editor(article_id, current_tags, all_tags)

@ar('/feed/article/{article_id}/tags/done')
def get(article_id: int, request):
    """Close tag editor, return normal tag display."""
    db = request.state.db
    article = get_article(db, article_id)
    current_tags = article_tags(article)
    return tag_display(article_id, current_tags)

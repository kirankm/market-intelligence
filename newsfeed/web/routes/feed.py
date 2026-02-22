"""Analyst feed routes."""
from fasthtml.common import *
from fasthtml.core import APIRouter
from newsfeed.web.components.nav import navbar
from newsfeed.web.components.cards import (
    article_card, expanded_card, star_icon, tag_filter, source_filter, date_filter
)
from newsfeed.web.queries.feed import (
    get_articles, get_article, get_latest_summary,
    article_tags, is_starred, toggle_star,
    get_tags_with_counts, get_sources_with_counts, get_setting
)
from newsfeed.web.filters import FilterState, date_range

ar = APIRouter()

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
    d_from, d_to = date_range(state.date)
    articles = get_articles(db, tags=state.tags, source=state.source,
                            date_from=d_from, date_to=d_to)
    cards = [article_card(a, article_tags(a), is_starred(a, user_id))
             for a in articles]
    return Div(*cards, id="article-list")

def feed_filters(db, state):
    """Render all filter controls."""
    tags = get_tags_with_counts(db)
    sources = get_sources_with_counts(db)
    top_n = int(get_setting(db, 'top_tags_count', '5'))
    return Div(
        tag_filter(tags, state, top_n),
        source_filter(sources, state),
        date_filter(state),
        cls="mb-4 flex flex-col gap-2"
    )

def feed_content(db, user_id, state):
    """Filters + article list — HTMX reload target."""
    return Div(feed_filters(db, state),
               article_list(db, user_id, state),
               id="feed-content")


def feed_page(session, db, state):
    """Render feed page shell."""
    user_id = session.get('user_id')
    return Titled("Feed",
        navbar(session, '/feed'),
        COLLAPSE_SCRIPT,
        Div(feed_content(db, user_id, state), cls="p-4"))

@ar('/feed')
def get(session, request, tags: str = '', expanded: str = '0', source: str = '', date: str = ''):
    db = request.state.db
    state = FilterState.from_request(tags, source, date, expanded)
    if request.headers.get('HX-Request'):
        return feed_content(db, session.get('user_id'), state)
    return feed_page(session, db, state)

@ar('/feed/article/{article_id}/expand')
def get(article_id: int, session, request):
    db = request.state.db
    article = get_article(db, article_id)
    summary = get_latest_summary(db, article_id)
    user_id = session.get('user_id')
    return expanded_card(article, article_tags(article), is_starred(article, user_id), summary)


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

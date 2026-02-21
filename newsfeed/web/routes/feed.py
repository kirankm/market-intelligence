"""Analyst feed routes."""
from fasthtml.common import *
from fasthtml.core import APIRouter
from newsfeed.web.components.nav import navbar
from newsfeed.web.components.cards import article_card, expanded_card
from newsfeed.web.queries.feed import get_articles, get_article, get_latest_summary, article_tags, is_starred

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


def article_list(db, user_id):
    """Build list of article cards."""
    articles = get_articles(db)
    return [article_card(a, article_tags(a), is_starred(a, user_id))
            for a in articles]


def feed_page(session, db):
    """Render feed page shell."""
    user_id = session.get('user_id')
    return Titled("Feed",
        navbar(session, '/feed'),
        COLLAPSE_SCRIPT,
        Div(*article_list(db, user_id), cls="p-4"))


@ar('/feed')
def get(session, request):
    return feed_page(session, request.state.db)

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

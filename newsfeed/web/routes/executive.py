"""Executive dashboard routes."""
from fasthtml.common import *
from fasthtml.core import APIRouter
from newsfeed.web.components.nav import navbar
from newsfeed.web.components.cards import collapsible_section

ar = APIRouter()


def section_category_summaries():
    """Placeholder for category summaries."""
    return P("Category summaries will appear here", cls="text-sm text-gray-400 italic")


def section_keyword_search():
    """Placeholder for keyword search."""
    return P("Keyword search will appear here", cls="text-sm text-gray-400 italic")


def section_starred():
    """Placeholder for starred by team."""
    return P("Starred articles will appear here", cls="text-sm text-gray-400 italic")


def section_digests():
    """Placeholder for recent digests."""
    return P("Recent digests will appear here", cls="text-sm text-gray-400 italic")


def executive_page(session):
    """Render executive dashboard."""
    return Titled("Executive Dashboard",
        navbar(session, '/executive'),
        Div(
            collapsible_section("Category Summaries", section_category_summaries(),
                                "categories", open=True),
            collapsible_section("Keyword Search", section_keyword_search(),
                                "search", open=False),
            collapsible_section("Starred by Team", section_starred(),
                                "starred", open=False),
            collapsible_section("Recent Digests", section_digests(),
                                "digests", open=False),
            cls="p-4"
        ))


@ar('/executive')
def get(session):
    return executive_page(session)


@ar('/executive/section/{section_id}')
def get(section_id: str, session, open: str = '1'):
    is_open = open == '1'
    sections = {
        'categories': ("Category Summaries", section_category_summaries()),
        'search':     ("Keyword Search", section_keyword_search()),
        'starred':    ("Starred by Team", section_starred()),
        'digests':    ("Recent Digests", section_digests()),
    }
    title, content = sections.get(section_id, ("Unknown", P("Not found")))
    return collapsible_section(title, content, section_id, open=is_open)

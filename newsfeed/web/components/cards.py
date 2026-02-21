"""Article card components."""
from fasthtml.common import *


def tag_pill(name):
    """Render a single tag pill."""
    return Span(name, cls="text-xs px-2 py-1 bg-blue-100 text-blue-800 rounded-full")


def card_meta(article, source_name, tags):
    """Render date, source, and tags row."""
    date_str = article.date.strftime("%d %b %Y") if article.date else "No date"
    pills = [tag_pill(t) for t in tags]
    return Div(
        Span(date_str, cls="text-sm text-gray-500"),
        Span(" • ", cls="text-sm text-gray-400"),
        Span(source_name, cls="text-sm text-gray-500"),
        Span(" • ", cls="text-sm text-gray-400") if pills else None,
        *pills,
        cls="flex items-center gap-1 flex-wrap"
    )


def star_icon(starred):
    """Render star icon."""
    return Span("⭐" if starred else "☆", cls="text-lg cursor-pointer")

def article_card(article, tags, starred):
    """Render a collapsed article card."""
    source_name = article.source.name if article.source else "Unknown"
    return Div(
        Div(
            star_icon(starred),
            Div(
                Div(Strong(article.title, cls="cursor-pointer"),
                    hx_get=f"/feed/article/{article.id}/expand",
                    hx_target=f"#article-{article.id}",
                    hx_swap="outerHTML",
                    onclick="collapseExpanded(this)"),
                card_meta(article, source_name, tags),
                cls="flex-1"
            ),
            cls="flex gap-3 items-start"
        ),
        cls="p-3 border-b hover:bg-gray-50",
        id=f"article-{article.id}"
    )

def summary_section(summary):
    """Render subtitle and bullets from summary."""
    if not summary: return P("No summary available", cls="text-sm text-gray-400 italic")
    bullets = summary.bullets or []
    return Div(
        P(summary.subtitle, cls="text-sm font-medium mt-2") if summary.subtitle else None,
        Ul(*[Li(b, cls="text-sm text-gray-600") for b in bullets], cls="list-disc ml-5 mt-1"),
    )


def expanded_card(article, tags, starred, summary):
    """Render an expanded article card with summary."""
    source_name = article.source.name if article.source else "Unknown"
    return Div(
        Div(
            star_icon(starred),
            Div(
                Div(Strong(article.title, cls="cursor-pointer"),
                    hx_get=f"/feed/article/{article.id}/collapse",
                    hx_target=f"#article-{article.id}",
                    hx_swap="outerHTML"),
                card_meta(article, source_name, tags),
                summary_section(summary),
                A("🔗 Read original", href=article.url, target="_blank",
                  cls="text-sm text-blue-600 mt-2 inline-block"),
                cls="flex-1"
            ),
            cls="flex gap-3 items-start"
        ),
        cls="p-3 border-b bg-gray-50 expanded",
        id=f"article-{article.id}"
    )

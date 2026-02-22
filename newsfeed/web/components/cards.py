"""Article card and filter components."""
from fasthtml.common import *
from urllib.parse import urlencode
from newsfeed.web.filters import FilterState
import json


# ── URL Helper ──────────────────────────────────────────────

def build_filter_url(state, **overrides):
    """Build /feed URL from FilterState with overrides."""
    params = state.to_params()
    params.update(overrides)
    cleaned = {k: v for k, v in params.items() if v}
    return f"/feed?{urlencode(cleaned)}" if cleaned else "/feed"


# ── Tag Helpers ─────────────────────────────────────────────

def build_tags_param(active_tags, toggle_tag):
    """Add or remove a tag from the active set."""
    tags = set(active_tags)
    if toggle_tag in tags: tags.discard(toggle_tag)
    else: tags.add(toggle_tag)
    return ','.join(sorted(tags))


# ── Card Components ─────────────────────────────────────────

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


def star_icon(starred, article_id):
    """Render star icon with HTMX toggle."""
    return Span(
        "⭐" if starred else "☆",
        cls="text-lg cursor-pointer",
        hx_post=f"/feed/article/{article_id}/star",
        hx_swap="outerHTML"
    )


def summary_section(summary):
    """Render subtitle and bullets from summary."""
    if not summary: return P("No summary available", cls="text-sm text-gray-400 italic")
    bullets = summary.bullets or []
    return Div(
        P(summary.subtitle, cls="text-sm font-medium mt-2") if summary.subtitle else None,
        Ul(*[Li(b, cls="text-sm text-gray-600") for b in bullets], cls="list-disc ml-5 mt-1"),
    )


def article_card(article, tags, starred):
    """Render a collapsed article card."""
    source_name = article.source.name if article.source else "Unknown"
    return Div(
        Div(
            star_icon(starred, article.id),
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


def expanded_card(article, tags, starred, summary):
    """Render an expanded article card with summary."""
    source_name = article.source.name if article.source else "Unknown"
    return Div(
        Div(
            star_icon(starred, article.id),
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


# ── Filter Components ───────────────────────────────────────

def tag_pill_filter(name, count, state):
    """Render a single filter tag pill."""
    is_active = name in state.tags
    new_tags = build_tags_param(state.tags, name)
    cls = ("bg-blue-600 text-white font-bold" if is_active
           else "bg-gray-100 text-gray-600 hover:bg-gray-200")
    return Span(f"{name} ({count})",
                cls=f"text-xs px-2 py-1 rounded-full cursor-pointer {cls}",
                hx_get=build_filter_url(state, tags=new_tags),
                hx_target="#feed-content", hx_swap="outerHTML")


def clear_pill(state):
    """Render clear filter pill."""
    return Span("✕ Clear",
                cls="text-xs px-2 py-1 rounded-full cursor-pointer bg-red-100 text-red-600",
                hx_get=build_filter_url(state, tags=''),
                hx_target="#feed-content", hx_swap="outerHTML")


def more_pill(count, state):
    """Render + N more pill."""
    return Span(f"+ {count} more",
                cls="text-xs px-2 py-1 rounded-full cursor-pointer bg-gray-200 text-gray-500",
                hx_get=build_filter_url(state, expanded='1'),
                hx_target="#feed-content", hx_swap="outerHTML")


def less_pill(state):
    """Render - less pill."""
    return Span("- less",
                cls="text-xs px-2 py-1 rounded-full cursor-pointer bg-gray-200 text-gray-500",
                hx_get=build_filter_url(state, expanded='0'),
                hx_target="#feed-content", hx_swap="outerHTML")


def tag_filter(tags_with_counts, state, top_n=5):
    """Render tag filter container."""
    visible = tags_with_counts if state.expanded else tags_with_counts[:top_n]
    rest_count = len(tags_with_counts) - top_n
    pills = [tag_pill_filter(n, c, state) for n, c in visible]
    if state.tags: pills.append(clear_pill(state))
    if not state.expanded and rest_count > 0: pills.append(more_pill(rest_count, state))
    if state.expanded and rest_count > 0: pills.append(less_pill(state))
    return Div(Span("Tags: ", cls="text-sm font-medium"), *pills,
               cls="flex gap-2 flex-wrap items-center")


def source_filter(sources_with_counts, state):
    """Render source dropdown filter."""
    options = [Option("All sources", value="", selected=not state.source)]
    for name, count in sources_with_counts:
        options.append(Option(f"{name} ({count})", value=name, selected=name == state.source))
    other_params = {k: v for k, v in state.to_params().items() if k != 'source' and v}
    return Div(
        Span("Source: ", cls="text-sm font-medium"),
        Select(*options, name="source",
               hx_get="/feed", hx_target="#feed-content", hx_swap="outerHTML",
               hx_include="this", hx_vals=json.dumps(other_params),
               cls="text-sm border rounded px-2 py-1"),
        cls="flex items-center gap-2"
    )

def date_button(label, period, state):
    """Render a single date filter button."""
    is_active = state.date == period
    new_date = '' if is_active else period
    cls = ("bg-blue-600 text-white font-bold" if is_active
           else "bg-gray-100 text-gray-600 hover:bg-gray-200")
    return Span(label,
                cls=f"text-xs px-2 py-1 rounded-full cursor-pointer {cls}",
                hx_get=build_filter_url(state, date=new_date),
                hx_target="#feed-content", hx_swap="outerHTML")


def date_filter(state):
    """Render date filter buttons."""
    buttons = [('Today', 'today'), ('This Week', 'week'), ('This Month', 'month')]
    return Div(
        Span("Date: ", cls="text-sm font-medium"),
        *[date_button(label, period, state) for label, period in buttons],
        cls="flex items-center gap-2"
    )

"""Article card and filter components."""
from fasthtml.common import *
from urllib.parse import urlencode
from newsfeed.web.filters import FilterState
import json
import re as re_module
from fasthtml.common import *

# ── URL Helper ──────────────────────────────────────────────

def build_filter_url(state, **overrides):
    """Build URL preserving all filters, overriding specified ones."""
    params = state.to_params()
    params.update(overrides)
    cleaned = {k: v for k, v in params.items() if v}
    return f"{state.base}?{urlencode(cleaned)}" if cleaned else state.base

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

def summary_section(summary, search=''):
    """Render subtitle and bullets from summary."""
    if not summary: return P("No summary available", cls="text-sm text-gray-400 italic")
    bullets = summary.bullets or []
    subtitle = highlight(summary.subtitle, search) if search else summary.subtitle
    return Div(
        P(subtitle, cls="text-sm font-medium mt-2") if summary.subtitle else None,
        Ul(*[Li(highlight(b, search) if search else b, cls="text-sm text-gray-600")
             for b in bullets], cls="list-disc ml-5 mt-1"),
    )

def article_card(article, tags, starred, search=''):
    """Render a collapsed article card."""
    source_name = article.source.name if article.source else "Unknown"
    title = highlight(article.title, search) if search else article.title
    return Div(
        Div(
            star_icon(starred, article.id),
            Div(
                Div(Strong(title, cls="cursor-pointer"),
                    hx_get=f"/feed/article/{article.id}/expand?search={search}",
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

def expanded_card(article, tags, starred, summary, search=''):
    """Render an expanded article card with summary."""
    source_name = article.source.name if article.source else "Unknown"
    title = highlight(article.title, search) if search else article.title
    return Div(
        Div(
            star_icon(starred, article.id),
            Div(
                Div(Strong(title, cls="cursor-pointer"),
                    hx_get=f"/feed/article/{article.id}/collapse",
                    hx_target=f"#article-{article.id}",
                    hx_swap="outerHTML"),
                card_meta(article, source_name, tags),
                summary_section(summary, search),
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
                hx_target=f"#{state.target}", hx_swap="outerHTML")

def clear_pill(state):
    """Render clear filter pill."""
    return Span("✕ Clear",
                cls="text-xs px-2 py-1 rounded-full cursor-pointer bg-red-100 text-red-600",
                hx_get=build_filter_url(state, tags=''),
                hx_target=f"#{state.target}", hx_swap="outerHTML")


def more_pill(count, state):
    """Render + N more pill."""
    return Span(f"+ {count} more",
                cls="text-xs px-2 py-1 rounded-full cursor-pointer bg-gray-200 text-gray-500",
                hx_get=build_filter_url(state, expanded='1'),
                hx_target=f"#{state.target}", hx_swap="outerHTML")


def less_pill(state):
    """Render - less pill."""
    return Span("- less",
                cls="text-xs px-2 py-1 rounded-full cursor-pointer bg-gray-200 text-gray-500",
                hx_get=build_filter_url(state, expanded='0'),
                hx_target=f"#{state.target}", hx_swap="outerHTML")


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
               hx_get=state.base, hx_target=f"#{state.target}", hx_swap="outerHTML",
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
                hx_target=f"#{state.target}", hx_swap="outerHTML")


def date_filter(state):
    """Render date filter buttons."""
    buttons = [('Today', 'today'), ('This Week', 'week'), ('This Month', 'month')]
    return Div(
        Span("Date: ", cls="text-sm font-medium"),
        *[date_button(label, period, state) for label, period in buttons],
        cls="flex items-center gap-2"
    )

def search_box(state, debounce=300):
    """Render search input with debounced HTMX."""
    return Div(
        Span("🔍 ", cls="text-sm"),
        Input(type="text", name="search", value=state.search,
              placeholder="Search title/summary...",
              hx_get=build_filter_url(state, search=''),
              hx_target=f"#{state.target}", hx_swap="outerHTML",
              hx_trigger=f"keyup changed delay:{debounce}ms",
              hx_include="this",
              cls="text-sm border rounded px-2 py-1 w-64"),
        cls="flex items-center gap-1"
    )

def highlight(text, term):
    """Wrap matching term in <mark> tags, case-insensitive."""
    if not term or not text: return text
    parts = re_module.split(f'({re_module.escape(term)})', text, flags=re_module.IGNORECASE)
    return Span(*[Mark(p) if p.lower() == term.lower() else p for p in parts])

def load_more_sentinel(state, offset, page_size):
    """Hidden div that triggers next page load when scrolled into view."""
    params = state.to_params()
    params['offset'] = str(offset)
    params['page_size'] = str(page_size)
    cleaned = {k: v for k, v in params.items() if v}
    url = f"{state.base}/more?{urlencode(cleaned)}"
    return Div(hx_get=url,
               hx_trigger="revealed",
               hx_swap="outerHTML",
               cls="h-1")

def collapsible_section(title, content, section_id, open=False):
    """Render a collapsible section with toggle."""
    icon = "▼" if open else "►"
    return Div(
        Div(
            Span(f"{icon} {title}", cls="text-lg font-bold cursor-pointer"),
            hx_get=f"/executive/section/{section_id}?open={'0' if open else '1'}",
            hx_target=f"#section-{section_id}",
            hx_swap="outerHTML",
            cls="p-3 border-b hover:bg-gray-50"
        ),
        Div(content, cls="p-3") if open else None,
        id=f"section-{section_id}",
        cls="border rounded mb-4"
    )

def period_label(date_from, date_to):
    """Format date range as readable label."""
    return f"{date_from.strftime('%b %d')} - {date_to.strftime('%b %d, %Y')}"


def category_period_dropdown(periods, active_from=None, active_to=None):
    """Render dropdown for selecting summary time period."""
    options = []
    for df, dt in periods:
        label = period_label(df, dt)
        selected = (df == active_from and dt == active_to)
        options.append(Option(label, value=f"{df}|{dt}", selected=selected))
    return Div(
        Span("Period: ", cls="text-sm font-medium"),
        Select(*options, name="period",
               hx_get="/executive/categories",
               hx_target="#categories-content",
               hx_swap="outerHTML",
               hx_include="this",
               cls="text-sm border rounded px-2 py-1"),
        cls="flex items-center gap-2 mb-4"
    )

def category_card(tag_name, summary_text, article_count, star_count):
    """Render a single category summary card."""
    return Div(
        Div(
            Strong(tag_name),
            Span(f"  ({article_count} articles, {star_count} ⭐)",
                 cls="text-sm text-gray-500"),
            cls="mb-2"
        ),
        P(summary_text, cls="text-sm text-gray-700 leading-relaxed"),
        cls="p-4 border rounded mb-3"
    )

def digest_tab(label, count, tab, active_tab):
    """Render a single digest ribbon tab."""
    is_active = tab == active_tab
    cls = ("bg-blue-600 text-white font-bold" if is_active
           else "bg-gray-100 text-gray-600 hover:bg-gray-200")
    return Span(f"{label} ({count})",
                cls=f"text-sm px-3 py-1 rounded-full cursor-pointer {cls}",
                hx_get=f"/executive/digests?tab={tab}",
                hx_target="#digests-content",
                hx_swap="outerHTML")


def digest_ribbon(draft_count, sent_count, active_tab='draft'):
    """Render digest tab ribbon."""
    return Div(
        digest_tab("To be Published", draft_count, "draft", active_tab),
        digest_tab("Published", sent_count, "sent", active_tab),
        cls="flex gap-2 mb-4"
    )


def digest_item(digest, item_count, show_publish=False):
    """Render a single digest list item."""
    title = digest.title or f"{digest.date_from} — {digest.date_to}"
    return Div(
        Div(
            Span(f"📋 ", cls="text-lg"),
            Strong(title, cls="cursor-pointer",
                   hx_get=f"/executive/digests/{digest.id}/expand?tab={'draft' if show_publish else 'sent'}",
                   hx_target=f"#digest-{digest.id}",
                   hx_swap="outerHTML"),
            Span(f"  ({item_count} articles)", cls="text-sm text-gray-500"),
            Button("Publish", cls="ml-4 text-xs px-2 py-1 bg-green-500 text-white rounded",
                   hx_post=f"/executive/digests/{digest.id}/publish",
                   hx_target="#digests-content",
                   hx_swap="outerHTML") if show_publish else
            Button("Review", cls="ml-4 text-xs px-2 py-1 bg-yellow-500 text-white rounded",
                   hx_post=f"/executive/digests/{digest.id}/review",
                   hx_target="#digests-content",
                   hx_swap="outerHTML"),
            cls="flex items-center"
        ),
        id=f"digest-{digest.id}",
        cls="p-3 border-b hover:bg-gray-50"
    )

def digest_expanded(digest, item_count, summary=None, show_publish=False):
    """Render expanded digest with summary."""
    title = digest.title or f"{digest.date_from} — {digest.date_to}"
    return Div(
        Div(
            Span(f"📋 ", cls="text-lg"),
            Strong(title, cls="cursor-pointer",
                   hx_get=f"/executive/digests/{digest.id}/collapse?tab={'draft' if show_publish else 'sent'}",
                   hx_target=f"#digest-{digest.id}",
                   hx_swap="outerHTML"),
            Span(f"  ({item_count} articles)", cls="text-sm text-gray-500"),
            Button("Publish", cls="ml-4 text-xs px-2 py-1 bg-green-500 text-white rounded",
                   hx_post=f"/executive/digests/{digest.id}/publish",
                   hx_target="#digests-content",
                   hx_swap="outerHTML") if show_publish else
            Button("Review", cls="ml-4 text-xs px-2 py-1 bg-yellow-500 text-white rounded",
                   hx_post=f"/executive/digests/{digest.id}/review",
                   hx_target="#digests-content",
                   hx_swap="outerHTML"),
            cls="flex items-center mb-2"
        ),
        digest_summary_display(digest.id, summary, show_edit=show_publish),
        id=f"digest-{digest.id}",
        cls="p-3 border-b bg-gray-50"
    )

def digest_summary_display(digest_id, summary, show_edit=False):
    """Render digest summary with edit/revert buttons."""
    content = summary.content if summary else "No summary available"
    actions = []
    if show_edit:
        actions.append(Span("✏️ Edit", cls="text-xs text-blue-600 cursor-pointer",
                            hx_get=f"/executive/digests/{digest_id}/edit",
                            hx_target=f"#digest-summary-{digest_id}",
                            hx_swap="outerHTML"))
        if summary and summary.version > 1:
            actions.append(Span("↩ Revert to original", cls="text-xs text-yellow-600 cursor-pointer ml-2",
                                hx_post=f"/executive/digests/{digest_id}/revert",
                                hx_target=f"#digest-summary-{digest_id}",
                                hx_swap="outerHTML"))
    return Div(
        P(content, cls="text-sm text-gray-700 leading-relaxed whitespace-pre-line"),
        Div(*actions, cls="mt-2") if actions else None,
        id=f"digest-summary-{digest_id}",
        cls="mt-2"
    )


def digest_summary_edit_form(digest_id, summary):
    """Render inline edit form for digest summary."""
    content = summary.content if summary else ''
    return Div(
        Textarea(content, name="content", rows=8,
                 cls="w-full text-sm border rounded px-2 py-1 mb-2"),
        Div(
            Button("Save", cls="text-xs px-2 py-1 bg-green-500 text-white rounded mr-2",
                   hx_post=f"/executive/digests/{digest_id}/save",
                   hx_target=f"#digest-summary-{digest_id}",
                   hx_swap="outerHTML",
                   hx_include=f"#digest-summary-{digest_id}"),
            Span("Cancel", cls="text-xs text-gray-500 cursor-pointer",
                 hx_get=f"/executive/digests/{digest_id}/cancel",
                 hx_target=f"#digest-summary-{digest_id}",
                 hx_swap="outerHTML"),
            cls="flex items-center"
        ),
        id=f"digest-summary-{digest_id}",
        cls="mt-2 p-2 border rounded bg-white"
    )

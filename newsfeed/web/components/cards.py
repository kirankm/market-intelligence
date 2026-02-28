"""Article card and filter components."""
from fasthtml.common import *
from monsterui.all import Card, ButtonT, DivHStacked, DivLAligned, Loading
from urllib.parse import urlencode
from newsfeed.web.filters import FilterState
import json
import re as re_module

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

# ── Shared Pill Styles ──────────────────────────────────────

PILL = "text-xs px-2 py-0.5 rounded-full cursor-pointer transition"
PILL_ACTIVE = f"{PILL} bg-primary text-primary-foreground font-semibold"
PILL_INACTIVE = f"{PILL} bg-muted text-muted-foreground hover:bg-accent"
PILL_CLEAR = f"{PILL} bg-destructive/10 text-destructive hover:bg-destructive/20"
PILL_MORE = f"{PILL} bg-muted text-muted-foreground hover:bg-accent"
BTN_SUCCESS = "text-xs px-3 py-1 bg-green-600 text-white rounded hover:bg-green-700 transition"
BTN_WARNING = "text-xs px-3 py-1 bg-yellow-500 text-white rounded hover:bg-yellow-600 transition"
BTN_PRIMARY = "text-xs px-3 py-1 bg-primary text-primary-foreground rounded hover:bg-primary/90 transition"
EXEC_INPUT = "text-sm border border-input rounded px-2.5 py-1.5 bg-background text-foreground w-full focus:outline-none focus:ring-1 focus:ring-ring transition"


# ── Admin Settings ─────────────────────────────────────────
ADMIN_TABS = [
    ('Costs', 'costs'),
    ('Sources', 'sources'),
    ('Users', 'users'),
    ('Settings', 'settings'),
    ('Jobs', 'jobs'),
]

VALID_ROLES = ['viewer', 'contributor', 'moderator', 'admin']
COST_PERIODS = [('This Week', 'week'), ('This Month', 'month'), ('All Time', 'all')]


# ── Card Components ─────────────────────────────────────────



def tag_pill(name):
    """Render a single tag pill."""
    return Span(name, cls="text-xs px-2 py-0.5 bg-primary/10 text-primary rounded-full")


def tag_display(article_id, tags):
    """Render tags with an edit button — swappable via HTMX."""
    pills = [tag_pill(t) for t in tags]
    return Div(
        *pills,
        Span("✏️", cls="text-xs cursor-pointer hover:scale-110 transition ml-1",
             hx_get=f"/feed/article/{article_id}/tags/edit",
             hx_target=f"#tags-{article_id}",
             hx_swap="outerHTML",
             title="Edit tags"),
        id=f"tags-{article_id}",
        cls="flex gap-1.5 flex-wrap items-center"
    )


def tag_editor(article_id, current_tags, all_tags):
    """Render inline tag editor with add/remove controls."""
    # Current tags with remove buttons
    current_pills = [
        Span(
            t, " ✕",
            cls="text-xs px-2 py-0.5 bg-destructive/10 text-destructive rounded-full cursor-pointer hover:bg-destructive/20",
            hx_post=f"/feed/article/{article_id}/tags/remove?tag_name={t}",
            hx_target=f"#tags-{article_id}",
            hx_swap="outerHTML",
            title=f"Remove {t}"
        ) for t in current_tags
    ]

    # Available tags (not already applied)
    available = [t for t in all_tags if t not in current_tags]

    # Dropdown + add button
    tag_options = [Option(t, value=t) for t in available]
    add_form = Form(
        Select(*tag_options, name="tag_name", id=f"tag-select-{article_id}",
               cls="text-xs px-1 py-0.5 rounded border",
               onchange=f"document.getElementById('free-text-{article_id}').style.display = this.value === 'Other' ? 'inline' : 'none'"),
        Input(type="text", name="free_text", placeholder="Enter tag...",
              id=f"free-text-{article_id}",
              cls="text-xs px-1 py-0.5 rounded border ml-1",
              style="display:none"),
        Button("Add", type="submit",
               cls="text-xs px-2 py-0.5 bg-primary text-primary-foreground rounded ml-1"),
        hx_post=f"/feed/article/{article_id}/tags/add",
        hx_target=f"#tags-{article_id}",
        hx_swap="outerHTML",
        cls="flex items-center"
    )

    done_btn = Span("✓ Done", cls="text-xs px-2 py-0.5 bg-muted text-muted-foreground rounded cursor-pointer hover:bg-muted/80 ml-2",
                    hx_get=f"/feed/article/{article_id}/tags/done",
                    hx_target=f"#tags-{article_id}",
                    hx_swap="outerHTML")

    return Div(
        Div(*current_pills, cls="flex gap-1.5 flex-wrap mb-1"),
        Div(add_form, done_btn, cls="flex items-center"),
        id=f"tags-{article_id}",
        cls="flex flex-col gap-1 p-2 bg-muted/30 rounded"
    )


def card_meta(article, source_name, tags):
    """Render date, source, and tags row."""
    date_str = article.date.strftime("%d %b %Y") if article.date else "No date"
    return DivLAligned(
        Span(date_str, cls="text-xs text-muted-foreground"),
        Span("•", cls="text-xs text-muted-foreground"),
        Span(source_name, cls="text-xs text-muted-foreground"),
        Span("•", cls="text-xs text-muted-foreground") if tags else None,
        tag_display(article.id, tags),
        cls="gap-1.5 flex-wrap mt-0.5"
    )


def star_icon(starred, article_id):
    """Render star icon with HTMX toggle."""
    return Span(
        "⭐" if starred else "☆",
        cls="text-lg cursor-pointer hover:scale-110 transition",
        hx_post=f"/feed/article/{article_id}/star",
        hx_swap="outerHTML"
    )


def summary_section(summary, search=''):
    """Render subtitle and bullets from summary."""
    if not summary: return P("No summary available", cls="text-sm text-muted-foreground italic")
    bullets = summary.bullets or []
    subtitle = highlight(summary.subtitle, search) if search else summary.subtitle
    return Div(
        P(subtitle, cls="text-sm font-medium mt-2") if summary.subtitle else None,
        Ul(*[Li(highlight(b, search) if search else b, cls="text-sm text-muted-foreground")
             for b in bullets], cls="list-disc ml-5 mt-1"),
    )


def article_card(article, tags, starred, search=''):
    """Render a collapsed article card."""
    source_name = article.source.name if article.source else "Unknown"
    title = highlight(article.title, search) if search else article.title
    return Div(
        DivHStacked(
            star_icon(starred, article.id),
            Div(
                Div(Strong(title, cls="cursor-pointer text-foreground hover:text-primary transition"),
                    hx_get=f"/feed/article/{article.id}/expand?search={search}",
                    hx_target=f"#article-{article.id}",
                    hx_swap="outerHTML",
                    onclick="collapseExpanded(this)"),
                card_meta(article, source_name, tags),
                cls="flex-1"
            ),
            cls="gap-3 items-start"
        ),
        cls="py-3 px-4 border-b border-border hover:bg-muted/50 transition",
        id=f"article-{article.id}"
    )


def expanded_card(article, tags, starred, summary, search=''):
    """Render an expanded article card with summary."""
    source_name = article.source.name if article.source else "Unknown"
    title = highlight(article.title, search) if search else article.title
    return Div(
        DivHStacked(
            star_icon(starred, article.id),
            Div(
                Div(Strong(title, cls="cursor-pointer text-foreground hover:text-primary transition"),
                    hx_get=f"/feed/article/{article.id}/collapse",
                    hx_target=f"#article-{article.id}",
                    hx_swap="outerHTML"),
                card_meta(article, source_name, tags),
                summary_section(summary, search),
                A("🔗 Read original", href=article.url, target="_blank",
                  cls="text-sm text-primary hover:text-primary/80 mt-2 inline-block transition"),
                cls="flex-1"
            ),
            cls="gap-3 items-start"
        ),
        cls="py-3 px-4 border-b border-border bg-muted/50 expanded",
        id=f"article-{article.id}"
    )

# ── Filter Components ───────────────────────────────────────

def tag_pill_filter(name, count, state):
    """Render a single filter tag pill."""
    is_active = name in state.tags
    new_tags = build_tags_param(state.tags, name)
    return Span(f"{name} ({count})",
                cls=PILL_ACTIVE if is_active else PILL_INACTIVE,
                hx_get=build_filter_url(state, tags=new_tags),
                hx_target=f"#{state.target}", hx_swap="outerHTML")


def clear_pill(state):
    """Render clear filter pill."""
    return Span("✕ Clear", cls=PILL_CLEAR,
                hx_get=build_filter_url(state, tags=''),
                hx_target=f"#{state.target}", hx_swap="outerHTML")


def more_pill(count, state):
    """Render + N more pill."""
    return Span(f"+ {count} more", cls=PILL_MORE,
                hx_get=build_filter_url(state, expanded='1'),
                hx_target=f"#{state.target}", hx_swap="outerHTML")


def less_pill(state):
    """Render - less pill."""
    return Span("- less", cls=PILL_MORE,
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
    return DivLAligned(
        Span("Tags:", cls="text-sm font-medium text-foreground"), *pills,
        cls="gap-2 flex-wrap"
    )


def source_filter(sources_with_counts, state):
    """Render source dropdown filter."""
    options = [Option("All sources", value="", selected=not state.source)]
    for name, count in sources_with_counts:
        options.append(Option(f"{name} ({count})", value=name, selected=name == state.source))
    other_params = {k: v for k, v in state.to_params().items() if k != 'source' and v}
    return DivLAligned(
        Span("Source:", cls="text-sm font-medium text-foreground"),
        Select(*options, name="source",
               hx_get=state.base, hx_target=f"#{state.target}", hx_swap="outerHTML",
               hx_include="this", hx_vals=json.dumps(other_params),
               cls="text-sm border border-input rounded px-2 py-1 bg-background text-foreground"),
        cls="gap-2"
    )


def date_button(label, period, state):
    """Render a single date filter button."""
    is_active = state.date == period
    new_date = '' if is_active else period
    return Span(label,
                cls=PILL_ACTIVE if is_active else PILL_INACTIVE,
                hx_get=build_filter_url(state, date=new_date),
                hx_target=f"#{state.target}", hx_swap="outerHTML")


def date_filter(state):
    """Render date filter buttons."""
    buttons = [('Today', 'today'), ('This Week', 'week'), ('This Month', 'month')]
    return DivLAligned(
        Span("Date:", cls="text-sm font-medium text-foreground"),
        *[date_button(label, period, state) for label, period in buttons],
        cls="gap-2"
    )


def search_box(state, debounce=300):
    """Render search input with debounced HTMX."""
    return DivLAligned(
        Span("🔍", cls="text-sm"),
        Input(type="text", name="search", value=state.search,
              placeholder="Search title/summary...",
              hx_get=build_filter_url(state, search=''),
              hx_target=f"#{state.target}",
              hx_swap="outerHTML",
              hx_trigger=f"keyup changed delay:{debounce}ms",
              hx_include="this",
              cls=EXEC_INPUT),
        cls="gap-2"
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
    return Div(hx_get=url, hx_trigger="revealed", hx_swap="outerHTML", cls="h-1")

# ── Collapsible Sections ────────────────────────────────────

def collapsible_section(title, content, section_id, open=False):
    """Render a collapsible section with toggle."""
    icon = "▼" if open else "►"
    return Div(
        Div(
            Span(f"{icon} {title}", cls="text-base font-semibold text-foreground cursor-pointer"),
            hx_get=f"/executive/section/{section_id}?open={'0' if open else '1'}",
            hx_target=f"#section-{section_id}",
            hx_swap="outerHTML",
            cls="px-4 py-3 bg-muted/50 hover:bg-muted transition"
        ),
        Div(content, cls="px-4 py-3") if open else None,
        id=f"section-{section_id}",
        cls="border border-border rounded-lg overflow-hidden mb-4"
    )

# ── Category Summaries ──────────────────────────────────────

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
    return DivLAligned(
        Span("Period:", cls="text-sm font-medium text-foreground"),
        Select(*options, name="period",
               hx_get="/executive/categories",
               hx_target="#categories-content",
               hx_swap="outerHTML",
               hx_include="this",
               cls="text-sm border border-input rounded px-2 py-1 bg-background text-foreground"),
        cls="gap-2 mb-4"
    )

def category_tab(name, active_name, period_from, period_to):
    """Render a single category ribbon tab."""
    is_active = name == active_name
    return Span(name,
                cls=PILL_ACTIVE if is_active else PILL_INACTIVE,
                hx_get=f"/executive/categories/select?category={name}&period={period_from}|{period_to}",
                hx_target="#categories-content",
                hx_swap="outerHTML")


def category_ribbon(tag_names, active_name, period_from, period_to):
    """Render horizontal category tabs."""
    return DivLAligned(
        *[category_tab(n, active_name, period_from, period_to) for n in tag_names],
        cls="gap-2 flex-wrap mb-4"
    )


def category_card(tag_name, summary_text, article_count, star_count):
    """Render selected category's summary."""
    return Card(
        Div(
            Strong(tag_name, cls="text-foreground"),
            Span(f"  ({article_count} articles, {star_count} ⭐)",
                 cls="text-xs text-muted-foreground"),
            cls="mb-2"
        ),
        P(summary_text, cls="text-sm text-muted-foreground leading-relaxed"),
    )

# ── Digests ─────────────────────────────────────────────────

def digest_tab(label, count, tab, active_tab):
    """Render a single digest ribbon tab."""
    is_active = tab == active_tab
    return Span(f"{label} ({count})",
                cls=f"text-sm px-3 py-1 rounded-full cursor-pointer transition "
                    f"{'bg-primary text-primary-foreground font-semibold' if is_active else 'bg-muted text-muted-foreground hover:bg-accent'}",
                hx_get=f"/executive/digests?tab={tab}",
                hx_target="#digests-content",
                hx_swap="outerHTML")


def digest_ribbon(draft_count, sent_count, active_tab='draft'):
    """Render digest tab ribbon."""
    return DivLAligned(
        digest_tab("To be Published", draft_count, "draft", active_tab),
        digest_tab("Published", sent_count, "sent", active_tab),
        cls="gap-2 mb-4"
    )

def _digest_action_btn(digest_id, show_publish):
    """Render publish or review button for a digest."""
    if show_publish:
        return Button("Publish", cls=f"ml-4 {BTN_SUCCESS}",
                      hx_post=f"/executive/digests/{digest_id}/publish",
                      hx_target="#digests-content", hx_swap="outerHTML")
    return Button("Review", cls=f"ml-4 {BTN_WARNING}",
                  hx_post=f"/executive/digests/{digest_id}/review",
                  hx_target="#digests-content", hx_swap="outerHTML")

def digest_item(digest, item_count, show_publish=False):
    """Render a single digest list item."""
    title = digest.title or f"{digest.date_from} — {digest.date_to}"
    return Div(
        DivLAligned(
            Span("📋", cls="text-base"),
            Strong(title, cls="cursor-pointer text-foreground hover:text-primary transition",
                   hx_get=f"/executive/digests/{digest.id}/expand?tab={'draft' if show_publish else 'sent'}",
                   hx_target=f"#digest-{digest.id}",
                   hx_swap="outerHTML"),
            Span(f"({item_count} articles)", cls="text-xs text-muted-foreground"),
            _digest_action_btn(digest.id, show_publish),
            cls="gap-2"
        ),
        id=f"digest-{digest.id}",
        cls="py-3 px-4 border-b border-border hover:bg-muted/50 transition"
    )


def digest_expanded(digest, item_count, summary=None, show_publish=False):
    """Render expanded digest with summary."""
    title = digest.title or f"{digest.date_from} — {digest.date_to}"
    return Div(
        DivLAligned(
            Span("📋", cls="text-base"),
            Strong(title, cls="cursor-pointer text-foreground hover:text-primary transition",
                   hx_get=f"/executive/digests/{digest.id}/collapse?tab={'draft' if show_publish else 'sent'}",
                   hx_target=f"#digest-{digest.id}",
                   hx_swap="outerHTML"),
            Span(f"({item_count} articles)", cls="text-xs text-muted-foreground"),
            _digest_action_btn(digest.id, show_publish),
            cls="gap-2 mb-2"
        ),
        digest_summary_display(digest.id, summary, show_edit=show_publish),
        id=f"digest-{digest.id}",
        cls="py-3 px-4 border-b border-border bg-muted/50"
    )


def digest_summary_display(digest_id, summary, show_edit=False):
    """Render digest summary with edit/revert buttons."""
    content = summary.content if summary else "No summary available"
    actions = []
    if show_edit:
        actions.append(Span("✏️ Edit", cls="text-xs text-primary cursor-pointer hover:underline",
                            hx_get=f"/executive/digests/{digest_id}/edit",
                            hx_target=f"#digest-summary-{digest_id}",
                            hx_swap="outerHTML"))
        if summary and summary.version > 1:
            actions.append(Span("↩ Revert", cls="text-xs text-yellow-600 cursor-pointer hover:underline ml-2",
                                hx_post=f"/executive/digests/{digest_id}/revert",
                                hx_target=f"#digest-summary-{digest_id}",
                                hx_swap="outerHTML"))
    return Div(
        P(content, cls="text-sm text-muted-foreground leading-relaxed whitespace-pre-line"),
        DivLAligned(*actions, cls="gap-2 mt-2") if actions else None,
        id=f"digest-summary-{digest_id}",
        cls="mt-2"
    )

def digest_summary_edit_form(digest_id, summary):
    """Render inline edit form for digest summary."""
    content = summary.content if summary else ''
    return Div(
        Textarea(content, name="content", rows=8,
                 cls="w-full text-sm border border-input rounded px-2.5 py-1.5 bg-background text-foreground focus:outline-none focus:ring-1 focus:ring-ring transition mb-2"),
        DivLAligned(
            Button("Save", cls=BTN_SUCCESS,
                   hx_post=f"/executive/digests/{digest_id}/save",
                   hx_target=f"#digest-summary-{digest_id}",
                   hx_swap="outerHTML",
                   hx_include=f"#digest-summary-{digest_id}"),
            Span("Cancel", cls="text-xs text-muted-foreground cursor-pointer hover:text-foreground transition",
                 hx_get=f"/executive/digests/{digest_id}/cancel",
                 hx_target=f"#digest-summary-{digest_id}",
                 hx_swap="outerHTML"),
            cls="gap-3"
        ),
        id=f"digest-summary-{digest_id}",
        cls="mt-2 p-3 border border-border rounded-lg bg-background"
    )

# ── Executive Search ────────────────────────────────────────

def exec_search_box(search=''):
    """Render search box for executive keyword search."""
    return DivLAligned(
        Span("🔍", cls="text-sm"),
        Input(type="text", name="search", value=search,
              placeholder="Search articles...",
              hx_get="/executive/search",
              hx_target="#search-results",
              hx_swap="outerHTML",
              hx_trigger="keyup changed delay:300ms",
              hx_include="this",
              cls=EXEC_INPUT),
        cls="gap-2 mb-4"
    )

def exec_search_results(articles, search, article_tags_fn, min_for_summary=5):
    """Render search results with optional summarize button."""
    count = len(articles)
    parts = []
    if count > 0:
        parts.append(P(f"Found {count} articles", cls="text-sm text-muted-foreground mb-2"))
    if count >= min_for_summary:
        parts.append(Button(f"📝 Summarize these {count} results",
                            cls=f"{BTN_PRIMARY} mb-3",
                            hx_post=f"/executive/search/summarize?search={search}",
                            hx_target="#search-summaries-list",
                            hx_swap="outerHTML"))
    cards = [Div(
        Strong(a.title, cls="text-sm text-foreground"),
        Span(f" — {a.source.name}", cls="text-xs text-muted-foreground"),
        Span(f" • {a.date}", cls="text-xs text-muted-foreground"),
        cls="py-1"
    ) for a in articles]
    parts.extend(cards)
    return Div(*parts) if parts else P("Type to search", cls="text-sm text-muted-foreground italic")

def keyword_summary_item(ks, expanded=True):
    """Render a single saved keyword summary."""
    if ks.status == 'pending':
        return Div(
            DivLAligned(
                Span(f"🔍 \"{ks.query}\"", cls="text-sm text-muted-foreground"),
                Loading(),
                cls="gap-2"
            ),
            hx_get="/executive/search/summaries",
            hx_trigger="every 3s",
            hx_target="#search-summaries-list",
            hx_swap="outerHTML",
            cls="py-2 border-b border-border"
        )
    header = DivLAligned(
        Span(f"{'▼' if expanded else '►'} 🔍 \"{ks.query}\"",
             cls="text-sm font-medium text-foreground cursor-pointer",
             hx_get=f"/executive/search/summary/{ks.id}/toggle?expanded={'0' if expanded else '1'}",
             hx_target=f"#ks-{ks.id}",
             hx_swap="outerHTML"),
        Span(f"— {ks.article_count} articles", cls="text-xs text-muted-foreground"),
        Span(f"— {ks.created_at.strftime('%b %d, %H:%M')}", cls="text-xs text-muted-foreground"),
        Span("✕", cls="text-xs text-destructive cursor-pointer hover:text-destructive/80 ml-auto",
             hx_delete=f"/executive/search/summary/{ks.id}/delete",
             hx_target="#search-summaries-list",
             hx_swap="outerHTML",
             hx_confirm="Delete this summary?"),
        cls="gap-2"
    )
    body = P(ks.summary, cls="text-sm text-muted-foreground leading-relaxed mt-1") if expanded else None
    return Div(header, body, id=f"ks-{ks.id}", cls="py-2 border-b border-border")

def keyword_summaries_list(summaries):
    """Render persistent list of generated summaries."""
    has_pending = any(ks.status == 'pending' for ks in summaries)
    items = [keyword_summary_item(ks, expanded=False) for ks in summaries]
    if not items:
        items = [P("No summaries generated yet", cls="text-sm text-muted-foreground italic")]
    attrs = {}
    if has_pending:
        attrs = dict(hx_get="/executive/search/summaries",
                     hx_trigger="every 3s",
                     hx_swap="outerHTML")
    return Div(
        H4("Your Summaries", cls="text-sm font-semibold text-foreground mb-2"),
        *items,
        id="search-summaries-list",
        cls="mt-4",
        **attrs
    )

def admin_tab(label, tab, active_tab):
    """Render a single admin tab."""
    is_active = tab == active_tab
    return Span(label,
                cls=PILL_ACTIVE if is_active else PILL_INACTIVE,
                hx_get=f"/admin/tab/{tab}",
                hx_target="#admin-content",
                hx_swap="outerHTML")


def admin_ribbon(active_tab='settings'):
    """Render admin tab ribbon."""
    return DivLAligned(
        *[admin_tab(label, tab, active_tab) for label, tab in ADMIN_TABS],
        cls="gap-2 mb-4"
    )


def settings_row(key, value):
    """Render a single settings row."""
    return Div(
        DivLAligned(
            Span(key, cls="text-sm font-medium text-foreground w-48"),
            Span(value, cls="text-sm text-muted-foreground flex-1",
                 id=f"setting-val-{key}"),
            Span("✏️", cls="text-xs text-primary cursor-pointer hover:underline",
                 hx_get=f"/admin/settings/{key}/edit",
                 hx_target=f"#setting-{key}",
                 hx_swap="outerHTML"),
            Span("✕", cls="text-xs text-destructive cursor-pointer hover:underline ml-2",
                 hx_delete=f"/admin/settings/{key}/delete",
                 hx_target="#admin-content",
                 hx_swap="outerHTML",
                 hx_confirm=f"Delete setting '{key}'?"),
            cls="gap-3"
        ),
        id=f"setting-{key}",
        cls="py-2 border-b border-border"
    )


def settings_edit_row(key, value):
    """Render inline edit form for a setting."""
    return Div(
        DivLAligned(
            Span(key, cls="text-sm font-medium text-foreground w-48"),
            Input(type="text", name="value", value=value,
                  cls="text-sm border border-input rounded px-2 py-1 bg-background text-foreground flex-1"),
            Button("Save", cls=BTN_SUCCESS,
                   hx_post=f"/admin/settings/{key}/save",
                   hx_target="#admin-content",
                   hx_swap="outerHTML",
                   hx_include=f"#setting-{key}"),
            Span("Cancel", cls="text-xs text-muted-foreground cursor-pointer hover:text-foreground",
                 hx_get=f"/admin/tab/settings",
                 hx_target="#admin-content",
                 hx_swap="outerHTML"),
            cls="gap-3"
        ),
        id=f"setting-{key}",
        cls="py-2 border-b border-border"
    )


def settings_add_form():
    """Render form to add a new setting."""
    return Card(
        DivLAligned(
            Input(type="text", name="key", placeholder="Key",
                  cls="text-sm border border-input rounded px-2 py-1 bg-background text-foreground w-48"),
            Input(type="text", name="value", placeholder="Value",
                  cls="text-sm border border-input rounded px-2 py-1 bg-background text-foreground flex-1"),
            Button("Add", cls=BTN_PRIMARY,
                   hx_post="/admin/settings/add",
                   hx_target="#admin-content",
                   hx_swap="outerHTML",
                   hx_include="#settings-add-form"),
            cls="gap-3"
        ),
        id="settings-add-form",
        cls="mt-4"
    )


def settings_table(settings):
    """Render full settings table."""
    rows = [settings_row(s.key, s.value) for s in settings]
    if not rows:
        rows = [P("No settings configured", cls="text-sm text-muted-foreground italic")]
    return Div(
        H4("App Settings", cls="text-sm font-semibold text-foreground mb-3"),
        *rows,
        settings_add_form()
    )

def user_row(user, role_name):
    """Render a single user row."""
    return Div(
        DivLAligned(
            Span(user.name, cls="text-sm font-medium text-foreground w-40"),
            Span(user.email, cls="text-sm text-muted-foreground w-56"),
            Span(role_name, cls=f"{PILL} bg-primary/10 text-primary"),
            Span("✏️", cls="text-xs text-primary cursor-pointer hover:underline ml-auto",
                 hx_get=f"/admin/users/{user.id}/edit",
                 hx_target=f"#user-{user.id}",
                 hx_swap="outerHTML"),
            Span("✕", cls="text-xs text-destructive cursor-pointer hover:underline ml-2",
                 hx_delete=f"/admin/users/{user.id}/delete",
                 hx_target="#admin-content",
                 hx_swap="outerHTML",
                 hx_confirm=f"Delete user '{user.name}'?"),
            cls="gap-3"
        ),
        id=f"user-{user.id}",
        cls="py-2 border-b border-border"
    )


def user_edit_row(user, role_name):
    """Render inline edit form for a user's role."""
    options = [Option(r, value=r, selected=r == role_name) for r in VALID_ROLES]
    return Div(
        DivLAligned(
            Span(user.name, cls="text-sm font-medium text-foreground w-40"),
            Span(user.email, cls="text-sm text-muted-foreground w-56"),
            Select(*options, name="role",
                   cls="text-sm border border-input rounded px-2 py-1 bg-background text-foreground"),
            Button("Save", cls=BTN_SUCCESS,
                   hx_post=f"/admin/users/{user.id}/save",
                   hx_target="#admin-content",
                   hx_swap="outerHTML",
                   hx_include=f"#user-{user.id}"),
            Span("Cancel", cls="text-xs text-muted-foreground cursor-pointer hover:text-foreground",
                 hx_get="/admin/tab/users",
                 hx_target="#admin-content",
                 hx_swap="outerHTML"),
            cls="gap-3"
        ),
        id=f"user-{user.id}",
        cls="py-2 border-b border-border"
    )


def user_add_form():
    """Render form to add a new user."""
    options = [Option(r, value=r) for r in VALID_ROLES]
    return Card(
        DivLAligned(
            Input(type="text", name="name", placeholder="Name",
                  cls="text-sm border border-input rounded px-2 py-1 bg-background text-foreground w-40"),
            Input(type="email", name="email", placeholder="Email",
                  cls="text-sm border border-input rounded px-2 py-1 bg-background text-foreground w-56"),
            Select(*options, name="role",
                   cls="text-sm border border-input rounded px-2 py-1 bg-background text-foreground"),
            Button("Add User", cls=BTN_PRIMARY,
                   hx_post="/admin/users/add",
                   hx_target="#admin-content",
                   hx_swap="outerHTML",
                   hx_include="#user-add-form"),
            cls="gap-3"
        ),
        id="user-add-form",
        cls="mt-4"
    )


def users_table(users, get_role_fn):
    """Render full users table."""
    header = Div(
        DivLAligned(
            Span("Name", cls="text-xs font-semibold text-muted-foreground w-40"),
            Span("Email", cls="text-xs font-semibold text-muted-foreground w-56"),
            Span("Role", cls="text-xs font-semibold text-muted-foreground"),
            cls="gap-3"
        ),
        cls="py-2 border-b-2 border-border"
    )
    rows = [user_row(u, get_role_fn(u)) for u in users]
    if not rows:
        rows = [P("No users", cls="text-sm text-muted-foreground italic")]
    return Div(
        H4("Users", cls="text-sm font-semibold text-foreground mb-3"),
        header,
        *rows,
        user_add_form()
    )

def source_status_icon(source):
    """Render ✅ or ⚠️ based on last success/failure."""
    if not source.last_success and not source.last_failure: return Span("—", cls="text-xs text-muted-foreground")
    if not source.last_failure: return Span("✅", cls="text-sm")
    if not source.last_success: return Span("⚠️", cls="text-sm")
    return Span("✅" if source.last_success > source.last_failure else "⚠️", cls="text-sm")


def format_ago(dt):
    """Format datetime as relative time string."""
    if not dt: return "Never"
    from datetime import datetime, timezone
    now = datetime.now(timezone.utc)
    if dt.tzinfo is None:
        from datetime import timezone as tz
        dt = dt.replace(tzinfo=tz.utc)
    diff = now - dt
    hours = int(diff.total_seconds() / 3600)
    if hours < 1: return f"{int(diff.total_seconds() / 60)} min ago"
    if hours < 24: return f"{hours} hrs ago"
    return f"{int(hours / 24)} days ago"


def source_row(source):
    """Render a single source row."""
    active_cls = "bg-green-600" if source.is_active else "bg-muted"
    return Div(
        DivLAligned(
            source_status_icon(source),
            Span(source.name, cls="text-sm font-medium text-foreground w-40"),
            Span(source.url, cls="text-xs text-muted-foreground w-56 truncate"),
            Span(format_ago(source.last_success), cls="text-xs text-muted-foreground w-24"),
            Span(
                Span(cls=f"inline-block w-8 h-4 rounded-full {active_cls} cursor-pointer transition"),
                hx_post=f"/admin/sources/{source.id}/toggle",
                hx_target="#admin-content",
                hx_swap="outerHTML"
            ),
            cls="gap-3"
        ),
        id=f"source-{source.id}",
        cls="py-2 border-b border-border"
    )


def sources_table(sources):
    """Render full sources table."""
    header = Div(
        DivLAligned(
            Span("", cls="w-6"),
            Span("Name", cls="text-xs font-semibold text-muted-foreground w-40"),
            Span("URL", cls="text-xs font-semibold text-muted-foreground w-56"),
            Span("Last Run", cls="text-xs font-semibold text-muted-foreground w-24"),
            Span("Active", cls="text-xs font-semibold text-muted-foreground"),
            cls="gap-3"
        ),
        cls="py-2 border-b-2 border-border"
    )
    rows = [source_row(s) for s in sources]
    if not rows:
        rows = [P("No sources configured", cls="text-sm text-muted-foreground italic")]
    return Div(
        H4("Sources", cls="text-sm font-semibold text-foreground mb-3"),
        header,
        *rows
    )

def cost_period_button(label, period, active_period):
    """Render a single cost period button."""
    is_active = period == active_period
    return Span(label,
                cls=PILL_ACTIVE if is_active else PILL_INACTIVE,
                hx_get=f"/admin/tab/costs?period={period}",
                hx_target="#admin-content",
                hx_swap="outerHTML")


def cost_period_filter(active_period='all'):
    """Render cost period filter."""
    return DivLAligned(
        Span("Period:", cls="text-sm font-medium text-foreground"),
        *[cost_period_button(l, p, active_period) for l, p in COST_PERIODS],
        cls="gap-2 mb-4"
    )


def cost_row(name, articles, input_tokens, output_tokens, cost, last_run):
    """Render a single cost row."""
    return Div(
        DivLAligned(
            Span(name, cls="text-sm font-medium text-foreground w-40"),
            Span(str(articles or 0), cls="text-sm text-muted-foreground w-20 text-right"),
            Span(f"{(input_tokens or 0):,}", cls="text-sm text-muted-foreground w-28 text-right"),
            Span(f"{(output_tokens or 0):,}", cls="text-sm text-muted-foreground w-28 text-right"),
            Span(f"${float(cost or 0):.4f}", cls="text-sm text-foreground font-medium w-24 text-right"),
            Span(format_ago(last_run), cls="text-xs text-muted-foreground w-24 text-right"),
            cls="gap-3"
        ),
        cls="py-2 border-b border-border"
    )


def cost_totals_row(totals):
    """Render totals row."""
    return Div(
        DivLAligned(
            Span("TOTAL", cls="text-sm font-semibold text-foreground w-40"),
            Span(str(totals.articles or 0), cls="text-sm font-semibold text-foreground w-20 text-right"),
            Span(f"{(totals.input_tokens or 0):,}", cls="text-sm font-semibold text-foreground w-28 text-right"),
            Span(f"{(totals.output_tokens or 0):,}", cls="text-sm font-semibold text-foreground w-28 text-right"),
            Span(f"${float(totals.cost or 0):.4f}", cls="text-sm font-semibold text-foreground w-24 text-right"),
            Span("", cls="w-24"),
            cls="gap-3"
        ),
        cls="py-2 border-t-2 border-border"
    )


def costs_table(rows, totals, active_period='all'):
    """Render full costs table."""
    header = Div(
        DivLAligned(
            Span("Source", cls="text-xs font-semibold text-muted-foreground w-40"),
            Span("Articles", cls="text-xs font-semibold text-muted-foreground w-20 text-right"),
            Span("Input Tokens", cls="text-xs font-semibold text-muted-foreground w-28 text-right"),
            Span("Output Tokens", cls="text-xs font-semibold text-muted-foreground w-28 text-right"),
            Span("Cost", cls="text-xs font-semibold text-muted-foreground w-24 text-right"),
            Span("Last Run", cls="text-xs font-semibold text-muted-foreground w-24 text-right"),
            cls="gap-3"
        ),
        cls="py-2 border-b-2 border-border"
    )
    data_rows = [cost_row(r.name, r.articles, r.input_tokens, r.output_tokens, r.cost, r.last_run)
                 for r in rows]
    if not data_rows:
        data_rows = [P("No cost data available", cls="text-sm text-muted-foreground italic py-2")]
    return Div(
        H4("Cost Tracking", cls="text-sm font-semibold text-foreground mb-3"),
        cost_period_filter(active_period),
        header,
        *data_rows,
        cost_totals_row(totals) if totals and totals.cost else None,
    )

def job_status_badge(status):
    """Render job status badge."""
    if status == 'running':
        return Span("⏳ Running", cls=f"{PILL} bg-yellow-100 text-yellow-700")
    if status == 'done':
        return Span("✅ Done", cls=f"{PILL} bg-green-100 text-green-700")
    if status == 'failed':
        return Span("⚠️ Failed", cls=f"{PILL} bg-red-100 text-red-700")
    return Span("💤 Idle", cls=f"{PILL} bg-muted text-muted-foreground")

def jobs_table(jobs, get_status_fn):
    """Render full jobs table."""
    rows = [job_row(j, *get_status_fn(j['key'])) for j in jobs]
    return Div(
        H4("Jobs", cls="text-sm font-semibold text-foreground mb-3"),
        *rows
    )

def job_params_form(job):
    """Render parameter inputs for a job."""
    params = job.get('params', [])
    if not params: return None
    inputs = [DivLAligned(
        Span(p['label'] + ":", cls="text-xs text-muted-foreground w-20"),
        Input(type="text", name=p['name'], placeholder=p['placeholder'],
              cls="text-sm border border-input rounded px-2 py-1 bg-background text-foreground w-32"),
        cls="gap-2"
    ) for p in params]
    return Div(*inputs, cls="flex gap-4 mt-2", id=f"job-params-{job['key']}")

def job_row(job, status, last_run, last_result):
    """Render a single job row."""
    is_running = status == 'running'
    params_form = job_params_form(job) if not is_running else None
    row = Div(
        DivLAligned(
            Div(
                Span(job['name'], cls="text-sm font-medium text-foreground"),
                P(job['desc'], cls="text-xs text-muted-foreground"),
                cls="w-64"
            ),
            job_status_badge(status),
            Span(f"Last: {last_run}", cls="text-xs text-muted-foreground w-40"),
            Button("Run Now", cls=BTN_PRIMARY,
                   hx_post=f"/admin/jobs/{job['key']}/run",
                   hx_target="#admin-content",
                   hx_swap="outerHTML",
                   hx_include=f"#job-params-{job['key']}") if not is_running else
            Button("Running...", cls=f"{PILL} bg-muted text-muted-foreground", disabled=True),
            cls="gap-4"
        ),
        params_form,
        P(f"Error: {last_result}", cls="text-xs text-destructive mt-1") if status == 'failed' and last_result else None,
        id=f"job-{job['key']}",
        cls="py-3 border-b border-border"
    )
    if is_running:
        row = Div(row,
                  hx_get="/admin/tab/jobs",
                  hx_trigger="every 3s",
                  hx_target="#admin-content",
                  hx_swap="outerHTML")
    return row

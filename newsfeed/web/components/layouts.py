"""Reusable layout components — ribbons, tabs, category cards, newsletters, keyword search."""
from fasthtml.common import *
from monsterui.all import Card, DivLAligned, Loading
from newsfeed.web.components.styles import (
    PILL_ACTIVE, PILL_INACTIVE, BTN_SUCCESS, BTN_WARNING, BTN_PRIMARY,
    INPUT_EXEC, TEXT_MUTED, TEXT_MUTED_XS, TEXT_ITALIC, TEXT_LINK, TEXT_HEADING,
    TEXT_EDIT, TEXT_CANCEL, TEXT_DELETE, TEXT_REVERT, TEXTAREA,
    ROW_BORDER, ROW_HOVER, ROW_EXPANDED,
    GAP_2, GAP_2_WRAP, GAP_2_MB, GAP_3, SECTION_MT, ICON_SM, ICON_BASE,
)

# ── Category Components ─────────────────────────────────────

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
        cls=f"{GAP_2_WRAP} mb-4"
    )


def category_card(tag_name, summary_text, article_count, star_count):
    """Render selected category's summary."""
    return Card(
        Div(
            Strong(tag_name, cls="text-foreground"),
            Span(f"  ({article_count} articles, {star_count} ⭐)",
                 cls=TEXT_MUTED_XS),
            cls="mb-2"
        ),
        P(summary_text, cls=f"{TEXT_MUTED} leading-relaxed"),
    )

# ── Newsletter Components ──────────────────────────────────

def newsletter_tab(label, count, tab, active_tab):
    """Render a single newsletter ribbon tab."""
    is_active = tab == active_tab
    return Span(f"{label} ({count})",
                cls=PILL_ACTIVE if is_active else PILL_INACTIVE,
                hx_get=f"/executive/newsletters?tab={tab}",
                hx_target="#newsletters-content",
                hx_swap="outerHTML")


def newsletter_ribbon(draft_count, sent_count, active_tab='draft'):
    """Render newsletter tab ribbon."""
    return DivLAligned(
        newsletter_tab("To be Published", draft_count, "draft", active_tab),
        newsletter_tab("Published", sent_count, "sent", active_tab),
        cls=GAP_2_MB
    )


def newsletter_date_range_form():
    """Render date range form for generating newsletters."""
    return Div(
        DivLAligned(
            Label("From:", cls="text-sm text-muted-foreground"),
            Input(type="date", name="from_date", cls="text-sm border rounded px-2 py-1"),
            Label("To:", cls="text-sm text-muted-foreground ml-2"),
            Input(type="date", name="to_date", cls="text-sm border rounded px-2 py-1"),
            Button("Generate Newsletter", cls=f"ml-3 {BTN_PRIMARY}",
                   hx_post="/executive/newsletters/generate",
                   hx_target="#newsletters-content",
                   hx_swap="outerHTML",
                   hx_include="closest div"),
            cls=GAP_2
        ),
        cls="mb-4"
    )


def _newsletter_action_btn(digest_id, show_publish):
    """Render publish or review button for a newsletter."""
    if show_publish:
        return Button("Publish", cls=f"ml-4 {BTN_SUCCESS}",
                      hx_post=f"/executive/newsletters/{digest_id}/publish",
                      hx_target="#newsletters-content", hx_swap="outerHTML")
    return Button("Review", cls=f"ml-4 {BTN_WARNING}",
                  hx_post=f"/executive/newsletters/{digest_id}/review",
                  hx_target="#newsletters-content", hx_swap="outerHTML")


def newsletter_item(digest, item_count, show_publish=False):
    """Render a single newsletter list item."""
    title = digest.title or f"{digest.date_from} — {digest.date_to}"
    return Div(
        DivLAligned(
            Span("📰", cls=ICON_BASE),
            Strong(title, cls=TEXT_LINK,
                   hx_get=f"/executive/newsletters/{digest.id}/expand?tab={'draft' if show_publish else 'sent'}",
                   hx_target=f"#newsletter-{digest.id}",
                   hx_swap="outerHTML"),
            Span(f"({item_count} articles)", cls=TEXT_MUTED_XS),
            _newsletter_action_btn(digest.id, show_publish),
            cls=GAP_2
        ),
        id=f"newsletter-{digest.id}",
        cls=ROW_HOVER
    )


def newsletter_expanded(digest, item_count, summary=None, show_publish=False):
    """Render expanded newsletter with HTML content."""
    title = digest.title or f"{digest.date_from} — {digest.date_to}"
    return Div(
        DivLAligned(
            Span("📰", cls=ICON_BASE),
            Strong(title, cls=TEXT_LINK,
                   hx_get=f"/executive/newsletters/{digest.id}/collapse?tab={'draft' if show_publish else 'sent'}",
                   hx_target=f"#newsletter-{digest.id}",
                   hx_swap="outerHTML"),
            Span(f"({item_count} articles)", cls=TEXT_MUTED_XS),
            _newsletter_action_btn(digest.id, show_publish),
            cls=f"{GAP_2} mb-2"
        ),
        newsletter_summary_display(digest.id, summary, show_edit=show_publish),
        id=f"newsletter-{digest.id}",
        cls=ROW_EXPANDED
    )


def newsletter_summary_display(digest_id, summary, show_edit=False):
    """Render newsletter summary — renders HTML content directly."""
    content = summary.content if summary else "No content available"
    actions = []
    if show_edit:
        actions.append(Span("✏️ Edit", cls=TEXT_EDIT,
                            hx_get=f"/executive/newsletters/{digest_id}/edit",
                            hx_target=f"#newsletter-summary-{digest_id}",
                            hx_swap="outerHTML"))
        if summary and summary.version > 1:
            actions.append(Span("↩ Revert", cls=TEXT_REVERT,
                                hx_post=f"/executive/newsletters/{digest_id}/revert",
                                hx_target=f"#newsletter-summary-{digest_id}",
                                hx_swap="outerHTML"))
    return Div(
        Div(NotStr(content), cls="leading-relaxed"),
        DivLAligned(*actions, cls=f"{GAP_2} mt-2") if actions else None,
        id=f"newsletter-summary-{digest_id}",
        cls="mt-2"
    )


def newsletter_summary_edit_form(digest_id, summary):
    """Render inline edit form for newsletter content (raw HTML)."""
    content = summary.content if summary else ''
    return Div(
        Textarea(content, name="content", rows=12,
                 cls=f"{TEXTAREA} mb-2"),
        DivLAligned(
            Button("Save", cls=BTN_SUCCESS,
                   hx_post=f"/executive/newsletters/{digest_id}/save",
                   hx_target=f"#newsletter-summary-{digest_id}",
                   hx_swap="outerHTML",
                   hx_include=f"#newsletter-summary-{digest_id}"),
            Span("Cancel", cls=TEXT_CANCEL,
                 hx_get=f"/executive/newsletters/{digest_id}/cancel",
                 hx_target=f"#newsletter-summary-{digest_id}",
                 hx_swap="outerHTML"),
            cls=GAP_3
        ),
        id=f"newsletter-summary-{digest_id}",
        cls="mt-2 p-3 border border-border rounded-lg bg-background"
    )

# ── Executive Search ────────────────────────────────────────

def exec_search_box(search=''):
    """Render search box for executive keyword search."""
    return DivLAligned(
        Span("🔍", cls=ICON_SM),
        Input(type="text", name="search", value=search,
              placeholder="Search articles...",
              hx_get="/executive/search",
              hx_target="#search-results",
              hx_swap="outerHTML",
              hx_trigger="keyup changed delay:300ms",
              hx_include="this",
              cls=INPUT_EXEC),
        cls=GAP_2_MB
    )


def exec_search_results(articles, search, article_tags_fn, min_for_summary=5):
    """Render search results with optional summarize button."""
    count = len(articles)
    parts = []
    if count > 0:
        parts.append(P(f"Found {count} articles", cls=f"{TEXT_MUTED} mb-2"))
    if count >= min_for_summary:
        parts.append(Button(f"📝 Summarize these {count} results",
                            cls=f"{BTN_PRIMARY} mb-3",
                            hx_post=f"/executive/search/summarize?search={search}",
                            hx_target="#search-summaries-list",
                            hx_swap="outerHTML"))
    cards = [Div(
        Strong(a.title, cls="text-sm text-foreground"),
        Span(f" — {a.source.name}", cls=TEXT_MUTED_XS),
        Span(f" • {a.date}", cls=TEXT_MUTED_XS),
        cls="py-1"
    ) for a in articles]
    parts.extend(cards)
    return Div(*parts) if parts else P("Type to search", cls=TEXT_ITALIC)


def keyword_summary_item(ks, expanded=True):
    """Render a single saved keyword summary."""
    if ks.status == 'pending':
        return Div(
            DivLAligned(
                Span(f"🔍 \"{ks.query}\"", cls=TEXT_MUTED),
                Loading(),
                cls=GAP_2
            ),
            hx_get="/executive/search/summaries",
            hx_trigger="every 3s",
            hx_target="#search-summaries-list",
            hx_swap="outerHTML",
            cls=ROW_BORDER
        )
    header = DivLAligned(
        Span(f"{'▼' if expanded else '►'} 🔍 \"{ks.query}\"",
             cls=f"{TEXT_LINK} text-sm font-medium",
             hx_get=f"/executive/search/summary/{ks.id}/toggle?expanded={'0' if expanded else '1'}",
             hx_target=f"#ks-{ks.id}",
             hx_swap="outerHTML"),
        Span(f"— {ks.article_count} articles", cls=TEXT_MUTED_XS),
        Span(f"— {ks.created_at.strftime('%b %d, %H:%M')}", cls=TEXT_MUTED_XS),
        Span("✕", cls=f"{TEXT_DELETE} hover:text-destructive/80 ml-auto",
             hx_delete=f"/executive/search/summary/{ks.id}/delete",
             hx_target="#search-summaries-list",
             hx_swap="outerHTML",
             hx_confirm="Delete this summary?"),
        cls=GAP_2
    )
    body = P(ks.summary, cls=f"{TEXT_MUTED} leading-relaxed mt-1") if expanded else None
    return Div(header, body, id=f"ks-{ks.id}", cls=ROW_BORDER)


def keyword_summaries_list(summaries):
    """Render persistent list of generated summaries."""
    has_pending = any(ks.status == 'pending' for ks in summaries)
    items = [keyword_summary_item(ks, expanded=False) for ks in summaries]
    if not items:
        items = [P("No summaries generated yet", cls=TEXT_ITALIC)]
    attrs = {}
    if has_pending:
        attrs = dict(hx_get="/executive/search/summaries",
                     hx_trigger="every 3s",
                     hx_swap="outerHTML")
    return Div(
        H4("Your Summaries", cls=f"{TEXT_HEADING} mb-2"),
        *items,
        id="search-summaries-list",
        cls=SECTION_MT,
        **attrs
    )

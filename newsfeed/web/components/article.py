"""Article card components — cards, tags, stars, summaries."""
from fasthtml.common import *
from monsterui.all import Card, ButtonT, DivHStacked, DivLAligned, Loading
from newsfeed.web.components.styles import (
    PILL_TAG, PILL_TAG_REMOVE, BTN_PRIMARY, BTN_MUTED,
    TEXT_MUTED, TEXT_MUTED_XS, TEXT_ITALIC, TEXT_LINK, TEXT_SUBTITLE,
    TAG_INPUT, TAG_INPUT_ML, TAG_LINK, LIST_DISC, SENTINEL,
    ROW_HOVER, ROW_EXPANDED,
    FLEX_WRAP, FLEX_WRAP_ITEMS, FLEX_CENTER, FLEX_COL_GAP, FLEX_1,
    GAP_3_START, PANEL_MUTED, ICON_EDIT, ICON_STAR,
)
import re as re_module


def tag_pill(name):
    """Render a single tag pill."""
    return Span(name, cls=PILL_TAG)


def tag_display(article_id, tags):
    """Render tags with an edit button — swappable via HTMX."""
    pills = [tag_pill(t) for t in tags]
    return Div(
        *pills,
        Span("✏️", cls=ICON_EDIT,
             hx_get=f"/feed/article/{article_id}/tags/edit",
             hx_target=f"#tags-{article_id}",
             hx_swap="outerHTML",
             title="Edit tags"),
        id=f"tags-{article_id}",
        cls=FLEX_WRAP_ITEMS
    )


def tag_editor(article_id, current_tags, all_tags):
    """Render inline tag editor with add/remove controls."""
    current_pills = [
        Span(
            t, " ✕",
            cls=PILL_TAG_REMOVE,
            hx_post=f"/feed/article/{article_id}/tags/remove?tag_name={t}",
            hx_target=f"#tags-{article_id}",
            hx_swap="outerHTML",
            title=f"Remove {t}"
        ) for t in current_tags
    ]

    available = [t for t in all_tags if t not in current_tags]

    tag_options = [Option(t, value=t) for t in available]
    add_form = Form(
        Select(*tag_options, name="tag_name", id=f"tag-select-{article_id}",
               cls=TAG_INPUT,
               onchange=f"document.getElementById('free-text-{article_id}').style.display = this.value === 'Other' ? 'inline' : 'none'"),
        Input(type="text", name="free_text", placeholder="Enter tag...",
              id=f"free-text-{article_id}",
              cls=TAG_INPUT_ML,
              style="display:none"),
        Button("Add", type="submit",
               cls=f"{BTN_PRIMARY} ml-1"),
        hx_post=f"/feed/article/{article_id}/tags/add",
        hx_target=f"#tags-{article_id}",
        hx_swap="outerHTML",
        cls=FLEX_CENTER
    )

    done_btn = Span("✓ Done", cls=f"{BTN_MUTED} cursor-pointer hover:bg-muted/80 ml-2",
                    hx_get=f"/feed/article/{article_id}/tags/done",
                    hx_target=f"#tags-{article_id}",
                    hx_swap="outerHTML")

    return Div(
        Div(*current_pills, cls=f"{FLEX_WRAP} mb-1"),
        Div(add_form, done_btn, cls=FLEX_CENTER),
        id=f"tags-{article_id}",
        cls=f"{FLEX_COL_GAP} {PANEL_MUTED}"
    )


def card_meta(article, source_name, tags):
    """Render date, source, and tags row."""
    date_str = article.date.strftime("%d %b %Y") if article.date else "No date"
    return DivLAligned(
        Span(date_str, cls=TEXT_MUTED_XS),
        Span("•", cls=TEXT_MUTED_XS),
        Span(source_name, cls=TEXT_MUTED_XS),
        Span("•", cls=TEXT_MUTED_XS) if tags else None,
        tag_display(article.id, tags),
        cls="gap-1.5 flex-wrap mt-0.5"
    )


def star_icon(starred, article_id):
    """Render star icon with HTMX toggle."""
    return Span(
        "⭐" if starred else "☆",
        cls=ICON_STAR,
        hx_post=f"/feed/article/{article_id}/star",
        hx_swap="outerHTML"
    )


def highlight(text, term):
    """Wrap matching term in <mark> tags, case-insensitive."""
    if not term or not text: return text
    parts = re_module.split(f'({re_module.escape(term)})', text, flags=re_module.IGNORECASE)
    return Span(*[Mark(p) if p.lower() == term.lower() else p for p in parts])


def summary_section(summary, search=''):
    """Render subtitle and bullets from summary."""
    if not summary: return P("No summary available", cls=TEXT_ITALIC)
    bullets = summary.bullets or []
    subtitle = highlight(summary.subtitle, search) if search else summary.subtitle
    return Div(
        P(subtitle, cls=TEXT_SUBTITLE) if summary.subtitle else None,
        Ul(*[Li(highlight(b, search) if search else b, cls=TEXT_MUTED)
             for b in bullets], cls=LIST_DISC),
    )


def article_card(article, tags, starred, search=''):
    """Render a collapsed article card."""
    source_name = article.source.name if article.source else "Unknown"
    title = highlight(article.title, search) if search else article.title
    return Div(
        DivHStacked(
            star_icon(starred, article.id),
            Div(
                Div(Strong(title, cls=TEXT_LINK),
                    hx_get=f"/feed/article/{article.id}/expand?search={search}",
                    hx_target=f"#article-{article.id}",
                    hx_swap="outerHTML",
                    onclick="collapseExpanded(this)"),
                card_meta(article, source_name, tags),
                cls=FLEX_1
            ),
            cls=GAP_3_START
        ),
        cls=ROW_HOVER,
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
                Div(Strong(title, cls=TEXT_LINK),
                    hx_get=f"/feed/article/{article.id}/collapse",
                    hx_target=f"#article-{article.id}",
                    hx_swap="outerHTML"),
                card_meta(article, source_name, tags),
                summary_section(summary, search),
                A("🔗 Read original", href=article.url, target="_blank",
                  cls=TAG_LINK),
                cls=FLEX_1
            ),
            cls=GAP_3_START
        ),
        cls=f"{ROW_EXPANDED} expanded",
        id=f"article-{article.id}"
    )


def load_more_sentinel(state, offset, page_size):
    """Hidden div that triggers next page load when scrolled into view."""
    from urllib.parse import urlencode
    params = state.to_params()
    params['offset'] = str(offset)
    params['page_size'] = str(page_size)
    cleaned = {k: v for k, v in params.items() if v}
    url = f"{state.base}/more?{urlencode(cleaned)}"
    return Div(hx_get=url, hx_trigger="revealed", hx_swap="outerHTML", cls=SENTINEL)

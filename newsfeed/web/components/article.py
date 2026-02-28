"""Article card components — cards, tags, stars, summaries."""
from fasthtml.common import *
from monsterui.all import Card, ButtonT, DivHStacked, DivLAligned, Loading
import re as re_module


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

    available = [t for t in all_tags if t not in current_tags]

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


def highlight(text, term):
    """Wrap matching term in <mark> tags, case-insensitive."""
    if not term or not text: return text
    parts = re_module.split(f'({re_module.escape(term)})', text, flags=re_module.IGNORECASE)
    return Span(*[Mark(p) if p.lower() == term.lower() else p for p in parts])


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


def load_more_sentinel(state, offset, page_size):
    """Hidden div that triggers next page load when scrolled into view."""
    from urllib.parse import urlencode
    params = state.to_params()
    params['offset'] = str(offset)
    params['page_size'] = str(page_size)
    cleaned = {k: v for k, v in params.items() if v}
    url = f"{state.base}/more?{urlencode(cleaned)}"
    return Div(hx_get=url, hx_trigger="revealed", hx_swap="outerHTML", cls="h-1")

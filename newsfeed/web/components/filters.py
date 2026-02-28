"""Filter and search components — tags, sources, dates, periods, search."""
from fasthtml.common import *
from monsterui.all import DivLAligned
from urllib.parse import urlencode
from newsfeed.web.filters import FilterState
import json

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

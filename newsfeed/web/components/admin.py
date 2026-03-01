"""Admin panel components — settings, users, sources, costs, jobs."""
from fasthtml.common import *
from monsterui.all import Card, DivLAligned
from newsfeed.web.components.styles import (
    PILL, PILL_ACTIVE, PILL_INACTIVE, PILL_TAG,
    BTN, BTN_SUCCESS, BTN_PRIMARY, BTN_MUTED,
    INPUT, INPUT_WIDE,
    TEXT_MUTED, TEXT_MUTED_XS, TEXT_LABEL, TEXT_HEADING, TEXT_ITALIC, TEXT_COL_HEADER, TEXT_TOTAL, TEXT_EDIT, TEXT_CANCEL, TEXT_DELETE,
    BADGE_RUNNING, BADGE_SUCCESS, BADGE_FAILED, BADGE_IDLE,
    ROW_BORDER, HEADER_ROW, TOTAL_ROW, TOGGLE_ACTIVE, TOGGLE_INACTIVE,
)

# ── Constants ───────────────────────────────────────────────

ADMIN_TABS = [
    ('Costs', 'costs'),
    ('Sources', 'sources'),
    ('Users', 'users'),
    ('Settings', 'settings'),
    ('Jobs', 'jobs'),
]

VALID_ROLES = ['viewer', 'contributor', 'moderator', 'admin']
COST_PERIODS = [('This Week', 'week'), ('This Month', 'month'), ('All Time', 'all')]

# ── Helpers ─────────────────────────────────────────────────

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

# ── Admin Ribbon ────────────────────────────────────────────

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

# ── Settings ────────────────────────────────────────────────

def settings_row(key, value):
    """Render a single settings row."""
    return Div(
        DivLAligned(
            Span(key, cls=f"{TEXT_LABEL} w-48"),
            Span(value, cls=f"{TEXT_MUTED} flex-1",
                 id=f"setting-val-{key}"),
            Span("✏️", cls=TEXT_EDIT,
                 hx_get=f"/admin/settings/{key}/edit",
                 hx_target=f"#setting-{key}",
                 hx_swap="outerHTML"),
            Span("✕", cls=f"{TEXT_DELETE} ml-2",
                 hx_delete=f"/admin/settings/{key}/delete",
                 hx_target="#admin-content",
                 hx_swap="outerHTML",
                 hx_confirm=f"Delete setting '{key}'?"),
            cls="gap-3"
        ),
        id=f"setting-{key}",
        cls=ROW_BORDER
    )


def settings_edit_row(key, value):
    """Render inline edit form for a setting."""
    return Div(
        DivLAligned(
            Span(key, cls=f"{TEXT_LABEL} w-48"),
            Input(type="text", name="value", value=value,
                  cls=INPUT_WIDE),
            Button("Save", cls=BTN_SUCCESS,
                   hx_post=f"/admin/settings/{key}/save",
                   hx_target="#admin-content",
                   hx_swap="outerHTML",
                   hx_include=f"#setting-{key}"),
            Span("Cancel", cls=TEXT_CANCEL,
                 hx_get=f"/admin/tab/settings",
                 hx_target="#admin-content",
                 hx_swap="outerHTML"),
            cls="gap-3"
        ),
        id=f"setting-{key}",
        cls=ROW_BORDER
    )


def settings_add_form():
    """Render form to add a new setting."""
    return Card(
        DivLAligned(
            Input(type="text", name="key", placeholder="Key",
                  cls=f"{INPUT} w-48"),
            Input(type="text", name="value", placeholder="Value",
                  cls=INPUT_WIDE),
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
        rows = [P("No settings configured", cls=TEXT_ITALIC)]
    return Div(
        H4("App Settings", cls=f"{TEXT_HEADING} mb-3"),
        *rows,
        settings_add_form()
    )

# ── Users ───────────────────────────────────────────────────

def user_row(user, role_name):
    """Render a single user row."""
    return Div(
        DivLAligned(
            Span(user.name, cls=f"{TEXT_LABEL} w-40"),
            Span(user.email, cls=f"{TEXT_MUTED} w-56"),
            Span(role_name, cls=PILL_TAG),
            Span("✏️", cls=f"{TEXT_EDIT} ml-auto",
                 hx_get=f"/admin/users/{user.id}/edit",
                 hx_target=f"#user-{user.id}",
                 hx_swap="outerHTML"),
            Span("✕", cls=f"{TEXT_DELETE} ml-2",
                 hx_delete=f"/admin/users/{user.id}/delete",
                 hx_target="#admin-content",
                 hx_swap="outerHTML",
                 hx_confirm=f"Delete user '{user.name}'?"),
            cls="gap-3"
        ),
        id=f"user-{user.id}",
        cls=ROW_BORDER
    )


def user_edit_row(user, role_name):
    """Render inline edit form for a user's role."""
    options = [Option(r, value=r, selected=r == role_name) for r in VALID_ROLES]
    return Div(
        DivLAligned(
            Span(user.name, cls=f"{TEXT_LABEL} w-40"),
            Span(user.email, cls=f"{TEXT_MUTED} w-56"),
            Select(*options, name="role",
                   cls=INPUT),
            Button("Save", cls=BTN_SUCCESS,
                   hx_post=f"/admin/users/{user.id}/save",
                   hx_target="#admin-content",
                   hx_swap="outerHTML",
                   hx_include=f"#user-{user.id}"),
            Span("Cancel", cls=TEXT_CANCEL,
                 hx_get="/admin/tab/users",
                 hx_target="#admin-content",
                 hx_swap="outerHTML"),
            cls="gap-3"
        ),
        id=f"user-{user.id}",
        cls=ROW_BORDER
    )


def user_add_form():
    """Render form to add a new user."""
    options = [Option(r, value=r) for r in VALID_ROLES]
    return Card(
        DivLAligned(
            Input(type="text", name="name", placeholder="Name",
                  cls=f"{INPUT} w-40"),
            Input(type="email", name="email", placeholder="Email",
                  cls=f"{INPUT} w-56"),
            Select(*options, name="role",
                   cls=INPUT),
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
            Span("Name", cls=f"{TEXT_COL_HEADER} w-40"),
            Span("Email", cls=f"{TEXT_COL_HEADER} w-56"),
            Span("Role", cls=f"{TEXT_COL_HEADER}"),
            cls="gap-3"
        ),
        cls=HEADER_ROW
    )
    rows = [user_row(u, get_role_fn(u)) for u in users]
    if not rows:
        rows = [P("No users", cls=TEXT_ITALIC)]
    return Div(
        H4("Users", cls=f"{TEXT_HEADING} mb-3"),
        header,
        *rows,
        user_add_form()
    )

# ── Sources ─────────────────────────────────────────────────

def source_status_icon(source):
    """Render ✅ or ⚠️ based on last success/failure."""
    if not source.last_success and not source.last_failure: return Span("—", cls=TEXT_MUTED_XS)
    if not source.last_failure: return Span("✅", cls="text-sm")
    if not source.last_success: return Span("⚠️", cls="text-sm")
    return Span("✅" if source.last_success > source.last_failure else "⚠️", cls="text-sm")


def source_row(source):
    """Render a single source row."""
    active_cls = TOGGLE_ACTIVE if source.is_active else TOGGLE_INACTIVE
    return Div(
        DivLAligned(
            source_status_icon(source),
            Span(source.name, cls=f"{TEXT_LABEL} w-40"),
            Span(source.url, cls=f"{TEXT_MUTED_XS} w-56 truncate"),
            Span(format_ago(source.last_success), cls=f"{TEXT_MUTED_XS} w-24"),
            Span(
                Span(cls=f"inline-block w-8 h-4 rounded-full {active_cls} cursor-pointer transition"),
                hx_post=f"/admin/sources/{source.id}/toggle",
                hx_target="#admin-content",
                hx_swap="outerHTML"
            ),
            cls="gap-3"
        ),
        id=f"source-{source.id}",
        cls=ROW_BORDER
    )


def sources_table(sources):
    """Render full sources table."""
    header = Div(
        DivLAligned(
            Span("", cls="w-6"),
            Span("Name", cls=f"{TEXT_COL_HEADER} w-40"),
            Span("URL", cls=f"{TEXT_COL_HEADER} w-56"),
            Span("Last Run", cls=f"{TEXT_COL_HEADER} w-24"),
            Span("Active", cls=f"{TEXT_COL_HEADER}"),
            cls="gap-3"
        ),
        cls=HEADER_ROW
    )
    rows = [source_row(s) for s in sources]
    if not rows:
        rows = [P("No sources configured", cls=TEXT_ITALIC)]
    return Div(
        H4("Sources", cls=f"{TEXT_HEADING} mb-3"),
        header,
        *rows
    )

# ── Costs ───────────────────────────────────────────────────

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
        Span("Period:", cls=TEXT_LABEL),
        *[cost_period_button(l, p, active_period) for l, p in COST_PERIODS],
        cls="gap-2 mb-4"
    )


def cost_row(name, articles, input_tokens, output_tokens, cost, last_run):
    """Render a single cost row."""
    return Div(
        DivLAligned(
            Span(name, cls=f"{TEXT_LABEL} w-40"),
            Span(str(articles or 0), cls=f"{TEXT_MUTED} w-20 text-right"),
            Span(f"{(input_tokens or 0):,}", cls=f"{TEXT_MUTED} w-28 text-right"),
            Span(f"{(output_tokens or 0):,}", cls=f"{TEXT_MUTED} w-28 text-right"),
            Span(f"${float(cost or 0):.4f}", cls="text-sm text-foreground font-medium w-24 text-right"),
            Span(format_ago(last_run), cls=f"{TEXT_MUTED_XS} w-24 text-right"),
            cls="gap-3"
        ),
        cls=ROW_BORDER
    )


def cost_totals_row(totals):
    """Render totals row."""
    return Div(
        DivLAligned(
            Span("TOTAL", cls=f"{TEXT_TOTAL} w-40"),
            Span(str(totals.articles or 0), cls=f"{TEXT_TOTAL} w-20 text-right"),
            Span(f"{(totals.input_tokens or 0):,}", cls=f"{TEXT_TOTAL} w-28 text-right"),
            Span(f"{(totals.output_tokens or 0):,}", cls=f"{TEXT_TOTAL} w-28 text-right"),
            Span(f"${float(totals.cost or 0):.4f}", cls=f"{TEXT_TOTAL} w-24 text-right"),
            Span("", cls="w-24"),
            cls="gap-3"
        ),
        cls=TOTAL_ROW
    )


def costs_table(rows, totals, active_period='all'):
    """Render full costs table."""
    header = Div(
        DivLAligned(
            Span("Source", cls=f"{TEXT_COL_HEADER} w-40"),
            Span("Articles", cls=f"{TEXT_COL_HEADER} w-20 text-right"),
            Span("Input Tokens", cls=f"{TEXT_COL_HEADER} w-28 text-right"),
            Span("Output Tokens", cls=f"{TEXT_COL_HEADER} w-28 text-right"),
            Span("Cost", cls=f"{TEXT_COL_HEADER} w-24 text-right"),
            Span("Last Run", cls=f"{TEXT_COL_HEADER} w-24 text-right"),
            cls="gap-3"
        ),
        cls=HEADER_ROW
    )
    data_rows = [cost_row(r.name, r.articles, r.input_tokens, r.output_tokens, r.cost, r.last_run)
                 for r in rows]
    if not data_rows:
        data_rows = [P("No cost data available", cls="text-sm text-muted-foreground italic py-2")]
    return Div(
        H4("Cost Tracking", cls=f"{TEXT_HEADING} mb-3"),
        cost_period_filter(active_period),
        header,
        *data_rows,
        cost_totals_row(totals) if totals and totals.cost else None,
    )

# ── Jobs ────────────────────────────────────────────────────

def job_status_badge(status):
    """Render job status badge."""
    if status == 'running':
        return Span("⏳ Running", cls=BADGE_RUNNING)
    if status == 'done':
        return Span("✅ Done", cls=BADGE_SUCCESS)
    if status == 'failed':
        return Span("⚠️ Failed", cls=BADGE_FAILED)
    return Span("💤 Idle", cls=BADGE_IDLE)


def job_params_form(job):
    """Render parameter inputs for a job."""
    params = job.get('params', [])
    if not params: return None
    inputs = [DivLAligned(
        Span(p['label'] + ":", cls="text-xs text-muted-foreground w-20"),
        Input(type="text", name=p['name'], placeholder=p.get('placeholder', ''),
              cls=f"{INPUT} w-32"),
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
                Span(job['name'], cls=TEXT_LABEL),
                P(job['desc'], cls=TEXT_MUTED_XS),
                cls="w-64"
            ),
            job_status_badge(status),
            Span(f"Last: {last_run}", cls=f"{TEXT_MUTED_XS} w-40"),
            Button("Run Now", cls=BTN_PRIMARY,
                   hx_post=f"/admin/jobs/{job['key']}/run",
                   hx_target="#admin-content",
                   hx_swap="outerHTML",
                   hx_include=f"#job-params-{job['key']}") if not is_running else
            Button("Running...", cls=BTN_MUTED, disabled=True),
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


def jobs_table(jobs, get_status_fn):
    """Render full jobs table."""
    rows = [job_row(j, *get_status_fn(j['key'])) for j in jobs]
    return Div(
        H4("Jobs", cls=f"{TEXT_HEADING} mb-3"),
        *rows
    )

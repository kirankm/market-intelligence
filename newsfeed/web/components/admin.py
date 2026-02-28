"""Admin panel components — settings, users, sources, costs, jobs."""
from fasthtml.common import *
from monsterui.all import Card, DivLAligned
from newsfeed.web.components.filters import PILL, PILL_ACTIVE, PILL_INACTIVE, BTN_SUCCESS, BTN_PRIMARY

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

# ── Users ───────────────────────────────────────────────────

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

# ── Sources ─────────────────────────────────────────────────

def source_status_icon(source):
    """Render ✅ or ⚠️ based on last success/failure."""
    if not source.last_success and not source.last_failure: return Span("—", cls="text-xs text-muted-foreground")
    if not source.last_failure: return Span("✅", cls="text-sm")
    if not source.last_success: return Span("⚠️", cls="text-sm")
    return Span("✅" if source.last_success > source.last_failure else "⚠️", cls="text-sm")


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

# ── Jobs ────────────────────────────────────────────────────

def job_status_badge(status):
    """Render job status badge."""
    if status == 'running':
        return Span("⏳ Running", cls=f"{PILL} bg-yellow-100 text-yellow-700")
    if status == 'done':
        return Span("✅ Done", cls=f"{PILL} bg-green-100 text-green-700")
    if status == 'failed':
        return Span("⚠️ Failed", cls=f"{PILL} bg-red-100 text-red-700")
    return Span("💤 Idle", cls=f"{PILL} bg-muted text-muted-foreground")


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


def jobs_table(jobs, get_status_fn):
    """Render full jobs table."""
    rows = [job_row(j, *get_status_fn(j['key'])) for j in jobs]
    return Div(
        H4("Jobs", cls="text-sm font-semibold text-foreground mb-3"),
        *rows
    )

"""Shared CSS class constants for UI components."""

# ── Pills ───────────────────────────────────────────────────
PILL = "text-xs px-2 py-0.5 rounded-full cursor-pointer transition"
PILL_ACTIVE = f"{PILL} bg-primary text-primary-foreground font-semibold"
PILL_INACTIVE = f"{PILL} bg-muted text-muted-foreground hover:bg-accent"
PILL_CLEAR = f"{PILL} bg-destructive/10 text-destructive hover:bg-destructive/20"
PILL_MORE = f"{PILL} bg-muted text-muted-foreground hover:bg-accent"
PILL_TAG = "text-xs px-2 py-0.5 bg-primary/10 text-primary rounded-full"
PILL_TAG_REMOVE = "text-xs px-2 py-0.5 bg-destructive/10 text-destructive rounded-full cursor-pointer hover:bg-destructive/20"

# ── Buttons ─────────────────────────────────────────────────
BTN = "text-xs px-3 py-1 rounded transition"
BTN_SUCCESS = f"{BTN} bg-green-600 text-white hover:bg-green-700"
BTN_WARNING = f"{BTN} bg-yellow-500 text-white hover:bg-yellow-600"
BTN_PRIMARY = f"{BTN} bg-primary text-primary-foreground hover:bg-primary/90"
BTN_MUTED = f"{BTN} bg-muted text-muted-foreground"

# ── Inputs ──────────────────────────────────────────────────
INPUT = "text-sm border border-input rounded px-2 py-1 bg-background text-foreground"
INPUT_WIDE = f"{INPUT} flex-1"
INPUT_EXEC = f"{INPUT} w-full px-2.5 py-1.5 focus:outline-none focus:ring-1 focus:ring-ring"
TEXTAREA = "w-full text-sm border border-input rounded px-2.5 py-1.5 bg-background text-foreground focus:outline-none focus:ring-1 focus:ring-ring transition"

# ── Text ────────────────────────────────────────────────────
TEXT_MUTED = "text-sm text-muted-foreground"
TEXT_MUTED_XS = "text-xs text-muted-foreground"
TEXT_LABEL = "text-sm font-medium text-foreground"
TEXT_HEADING = "text-sm font-semibold text-foreground"
TEXT_ITALIC = "text-sm text-muted-foreground italic"
TEXT_LINK = "cursor-pointer text-foreground hover:text-primary transition"
TEXT_COL_HEADER = "text-xs font-semibold text-muted-foreground"
TEXT_TOTAL = "text-sm font-semibold text-foreground"
TEXT_SECTION_TITLE = "text-base font-semibold text-foreground cursor-pointer"
TEXT_EDIT = "text-xs text-primary cursor-pointer hover:underline"
TEXT_CANCEL = "text-xs text-muted-foreground cursor-pointer hover:text-foreground transition"
TEXT_DELETE = "text-xs text-destructive cursor-pointer hover:underline"

# ── Status Badges ───────────────────────────────────────────
BADGE_RUNNING = f"{PILL} bg-yellow-100 text-yellow-700"
BADGE_SUCCESS = f"{PILL} bg-green-100 text-green-700"
BADGE_FAILED = f"{PILL} bg-red-100 text-red-700"
BADGE_IDLE = f"{PILL} bg-muted text-muted-foreground"

# ── Layout ──────────────────────────────────────────────────
ROW_BORDER = "py-2 border-b border-border"
ROW_HOVER = "py-3 px-4 border-b border-border hover:bg-muted/50 transition"
ROW_EXPANDED = "py-3 px-4 border-b border-border bg-muted/50"
HEADER_ROW = "py-2 border-b-2 border-border"
TOTAL_ROW = "py-2 border-t-2 border-border"
TOGGLE_ACTIVE = "inline-block w-8 h-4 rounded-full bg-green-600 cursor-pointer transition"
TOGGLE_INACTIVE = "inline-block w-8 h-4 rounded-full bg-muted cursor-pointer transition"

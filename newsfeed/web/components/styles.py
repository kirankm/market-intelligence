"""Shared CSS class constants for UI components."""

# ── Layout Utilities ────────────────────────────────────────
FLEX_WRAP = "flex gap-1.5 flex-wrap"
FLEX_WRAP_ITEMS = "flex gap-1.5 flex-wrap items-center"
FLEX_CENTER = "flex items-center"
FLEX_COL_GAP = "flex flex-col gap-1"
FLEX_1 = "flex-1"
GAP_2 = "gap-2"
GAP_2_WRAP = "gap-2 flex-wrap"
GAP_2_MB = "gap-2 mb-4"
GAP_3 = "gap-3"
GAP_3_START = "gap-3 items-start"
GAP_4 = "gap-4"
SECTION_MT = "mt-4"
PANEL_MUTED = "p-2 bg-muted/30 rounded"
COLLAPSIBLE = "border border-border rounded-lg overflow-hidden mb-4"
COLLAPSIBLE_HEADER = "px-4 py-3 bg-muted/50 hover:bg-muted transition"
COLLAPSIBLE_BODY = "px-4 py-3"

# ── Icons ───────────────────────────────────────────────────
ICON_EDIT = "text-xs cursor-pointer hover:scale-110 transition ml-1"
ICON_STAR = "text-lg cursor-pointer hover:scale-110 transition"
ICON_SM = "text-sm"
ICON_BASE = "text-base"

# ── Tag Editor ──────────────────────────────────────────────
TAG_INPUT = "text-xs px-1 py-0.5 rounded border"
TAG_INPUT_ML = "text-xs px-1 py-0.5 rounded border ml-1"
TAG_LINK = "text-sm text-primary hover:text-primary/80 mt-2 inline-block transition"

# ── Text Extras ─────────────────────────────────────────────
TEXT_SUBTITLE = "text-sm font-medium mt-2"
TEXT_COST = "text-sm text-foreground font-medium w-24 text-right"
TEXT_REVERT = "text-xs text-yellow-600 cursor-pointer hover:underline ml-2"

# ── Lists ───────────────────────────────────────────────────
LIST_DISC = "list-disc ml-5 mt-1"

# ── Sentinel ────────────────────────────────────────────────
SENTINEL = "h-1"

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

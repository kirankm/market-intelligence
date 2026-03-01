# ── AI Model ────────────────────────────────────────────────
DEFAULT_MODEL = "gemma-3-27b-it"
MODELS_WITH_JSON_MODE = {"gemini-2.5-flash", "gemini-2.0-flash", "gemini-1.5-flash", "gemini-1.5-pro"}

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Optional
import json
from pathlib import Path

# ── Dataclasses ─────────────────────────────────────────────

@dataclass
class SiteConfig:
    name: str
    listing_url: str
    pagination: str                          # e.g. "?page={n}"
    source_type: str = "news"                # "news" or "facility_listing"
    poll_frequency_days: int = 1
    request_delay: float = 1.0               # seconds between requests
    max_retries: int = 3
    eager_fetch: bool = True                 # fetch full content immediately?
    verify_ssl: bool = True

    # Config-driven listing parser
    listing_pattern: str = ""                # regex with capture groups
    listing_fields: list[str] = field(default_factory=list)  # field names for capture groups
    date_format: str = "%d %b %Y"            # strptime format for date parsing

    # Content extraction markers
    content_start: Optional[str] = None      # regex marker for body start
    content_end: Optional[str] = None        # regex marker for body end

    # Processing pipeline
    pipeline: list[str] = field(default_factory=lambda: [
        "extract_jina_meta", "remove_noise", "extract_body",
        "strip_byline", "strip_links", "strip_images",
        "decode_entities", "normalize_whitespace"
    ])

@dataclass
class SiteState:
    name: str
    last_pulled_at: Optional[datetime] = None
    last_article_date: Optional[str] = None  # "YYYY-MM-DD"

# ── JSON Loader ─────────────────────────────────────────────

SITES_DIR = Path(__file__).parent / "sites"

def load_site_config(site_name: str) -> SiteConfig:
    """Load a SiteConfig from a JSON file in the sites/ folder."""
    path = SITES_DIR / f"{site_name}.json"
    with open(path) as f:
        data = json.load(f)
    return SiteConfig(**data)

def load_all_site_configs() -> dict[str, SiteConfig]:
    """Load all site configs from the sites/ folder."""
    configs = {}
    for path in SITES_DIR.glob("*.json"):
        if path.stem == 'tags': continue
        with open(path) as f:
            data = json.load(f)
        configs[path.stem] = SiteConfig(**data)
    return configs

# ── State Persistence (DB-backed) ───────────────────────────

def load_state(site_name: str, db=None) -> SiteState:
    """Load SiteState from the sources table, or return fresh state."""
    from newsfeed.storage.database import get_session
    from newsfeed.storage.models import Source
    owns_session = db is None
    if owns_session:
        db = get_session()
    try:
        source = db.query(Source).filter_by(name=site_name).first()
        if source:
            return SiteState(
                name=site_name,
                last_pulled_at=source.last_pulled_at,
                last_article_date=source.last_article_date,
            )
        return SiteState(name=site_name)
    finally:
        if owns_session:
            db.close()

def save_state(state: SiteState, db=None):
    """Save SiteState to the sources table."""
    from newsfeed.storage.database import get_session
    from newsfeed.storage.models import Source
    owns_session = db is None
    if owns_session:
        db = get_session()
    try:
        source = db.query(Source).filter_by(name=state.name).first()
        if source:
            source.last_pulled_at = state.last_pulled_at
            source.last_article_date = state.last_article_date
            db.commit()
    finally:
        if owns_session:
            db.close()

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

# ── State Persistence ───────────────────────────────────────

STATE_DIR = Path(__file__).parent / "state"

def load_state(site_name: str) -> SiteState:
    """Load SiteState from JSON file, or return fresh state."""
    STATE_DIR.mkdir(exist_ok=True)
    path = STATE_DIR / f"{site_name}_state.json"
    if path.exists():
        with open(path) as f:
            data = json.load(f)
        return SiteState(
            name=data["name"],
            last_pulled_at=datetime.fromisoformat(data["last_pulled_at"]) if data.get("last_pulled_at") else None,
            last_article_date=data.get("last_article_date"),
        )
    return SiteState(name=site_name)

def save_state(state: SiteState):
    """Save SiteState to JSON file."""
    STATE_DIR.mkdir(exist_ok=True)
    path = STATE_DIR / f"{state.name}_state.json"
    data = {
        "name": state.name,
        "last_pulled_at": state.last_pulled_at.isoformat() if state.last_pulled_at else None,
        "last_article_date": state.last_article_date,
    }
    with open(path, 'w') as f:
        json.dump(data, f, indent=2)

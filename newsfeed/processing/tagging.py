import json, logging
from pathlib import Path

log = logging.getLogger("newsfeed.processing")

TAGS_PATH = Path(__file__).parent.parent / "sites" / "tags.json"

_tags_config = None

def _load_tags() -> dict:
    global _tags_config
    if _tags_config is None:
        with open(TAGS_PATH) as f:
            _tags_config = json.load(f)
    return _tags_config

def auto_tag(text: str) -> list[str]:
    """Match article text against keyword tag definitions."""
    tags_config = _load_tags()
    text_lower = text.lower()
    matched = [tag for tag, keywords in tags_config.items()
               if any(kw.lower() in text_lower for kw in keywords)]
    log.info(f"Tagged: {matched}")
    return matched

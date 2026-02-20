import re, logging
from datetime import datetime
from typing import Optional
from newsfeed.config import SiteConfig

log = logging.getLogger("newsfeed.fetch")

def _parse_date(date_str: str, date_format: str) -> Optional[str]:
    """Parse a date string into YYYY-MM-DD format."""
    try: return datetime.strptime(date_str.strip(), date_format).strftime("%Y-%m-%d")
    except ValueError: return None

def parse_listing(markdown: str, config: SiteConfig) -> list[dict]:
    """Generic config-driven listing parser.
    
    Uses config.listing_pattern (regex) and config.listing_fields (field names)
    to extract articles from a listing page's markdown.
    """
    if not config.listing_pattern or not config.listing_fields:
        log.warning(f"[{config.name}] No listing_pattern/fields configured")
        return []
    
    articles = []
    for m in re.finditer(config.listing_pattern, markdown, re.MULTILINE):
        groups = m.groups()
        article = {field: (groups[i].strip() if groups[i] else None)
                   for i, field in enumerate(config.listing_fields)}
        
        # Parse date if present
        if "date_raw" in article and article["date_raw"]:
            article["date"] = _parse_date(article["date_raw"], config.date_format)
        
        # Default content to None (populated later by eager/lazy fetch)
        article.setdefault("content", None)
        articles.append(article)
    
    return articles

import logging
from typing import Iterator
from newsfeed.config import SiteConfig
from .client import jina_fetch
from .parser import parse_listing

log = logging.getLogger("newsfeed.fetch")

def build_listing_url(listing_url: str, page_num: int, pagination: str) -> str:
    """Build the URL for a given listing page number."""
    if page_num <= 1: return listing_url
    return listing_url + pagination.format(n=page_num)

def paginate_listings(client, config: SiteConfig, max_pages: int = 5) -> Iterator[list[dict]]:
    """Yield one page of parsed articles at a time."""
    for page in range(1, max_pages + 1):
        url = build_listing_url(config.listing_url, page, config.pagination)
        log.info(f"[{config.name}] Fetching page {page}")
        md = jina_fetch(client, url, config.request_delay)
        articles = parse_listing(md, config)
        log.info(f"[{config.name}] Page {page}: {len(articles)} articles")
        if not articles: break
        yield articles

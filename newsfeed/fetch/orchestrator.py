import logging
from datetime import datetime, timedelta, timezone
from typing import Optional
from newsfeed.config import SiteConfig, SiteState
from .client import make_client, jina_fetch
from .pagination import paginate_listings

log = logging.getLogger("newsfeed.fetch")

def default_from_date(days_back: int = 7) -> str:
    return (datetime.now() - timedelta(days=days_back)).strftime("%Y-%m-%d")

def today() -> str:
    return datetime.now().strftime("%Y-%m-%d")

def resolve_dates(state: SiteState, from_date: Optional[str], to_date: Optional[str]) -> tuple[str, str]:
    """Determine the date range for a fetch run."""
    return (from_date or state.last_article_date or default_from_date(),
            to_date or today())

def update_state(state: SiteState, to_date: str):
    """Update state after a successful run."""
    state.last_pulled_at = datetime.now(timezone.utc)
    state.last_article_date = to_date

def filter_by_date(articles: list[dict], from_date: str, to_date: str) -> tuple[list[dict], bool]:
    """Filter articles by date range. Returns (filtered, reached_cutoff)."""
    filtered = []
    for a in articles:
        if not a.get("date"): continue
        if a["date"] < from_date: return filtered, True
        if a["date"] <= to_date:  filtered.append(a)
    return filtered, False

def enrich_with_content(client, articles: list[dict], config: SiteConfig) -> list[dict]:
    """Fetch full article content for each article (eager mode)."""
    for a in articles:
        log.info(f"[{config.name}] Fetching article: {a.get('title', 'unknown')[:60]}")
        try:    a["content"] = jina_fetch(client, a["url"], config.request_delay)
        except Exception as e:
            log.warning(f"[{config.name}] Failed to fetch {a['url']}: {e}")
            a["content"] = None
    return articles

def fetch_article_content(client, article: dict, config: SiteConfig) -> dict:
    """Fetch full content for a single article (lazy mode)."""
    if article.get("content"): return article
    try:    article["content"] = jina_fetch(client, article["url"], config.request_delay)
    except Exception as e:
        log.warning(f"[{config.name}] Failed to fetch {article['url']}: {e}")
    return article

def fetch_new_articles(
    config: SiteConfig,
    state: SiteState,
    from_date: Optional[str] = None,
    to_date: Optional[str] = None,
    max_pages: int = 5,
) -> list[dict]:
    """Discover and optionally fetch new articles from a site."""
    from_date, to_date = resolve_dates(state, from_date, to_date)
    log.info(f"[{config.name}] Run: {from_date} → {to_date}")

    all_articles = []
    with make_client(config) as client:
        for page_articles in paginate_listings(client, config, max_pages):
            filtered, cutoff = filter_by_date(page_articles, from_date, to_date)
            all_articles.extend(filtered)
            if cutoff: break

        if config.eager_fetch and all_articles:
            enrich_with_content(client, all_articles, config)

    if all_articles: update_state(state, to_date)
    log.info(f"[{config.name}] Done: {len(all_articles)} new articles")
    return all_articles

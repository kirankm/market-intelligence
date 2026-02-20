import time, logging, httpx
from newsfeed.config import SiteConfig

log = logging.getLogger("newsfeed.fetch")

def make_client(config: SiteConfig) -> httpx.Client:
    """Create an HTTP client with retry support."""
    transport = httpx.HTTPTransport(retries=config.max_retries, verify=config.verify_ssl)
    return httpx.Client(transport=transport, timeout=30)

def jina_fetch(client: httpx.Client, url: str, delay: float = 1.0) -> str:
    """Fetch a URL via Jina Reader with rate limiting."""
    time.sleep(delay)
    resp = client.get(f"https://r.jina.ai/{url}")
    resp.raise_for_status()
    log.debug(f"Fetched {url} ({len(resp.text)} chars)")
    return resp.text

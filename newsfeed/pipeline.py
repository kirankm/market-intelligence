"""Full pipeline orchestrator: fetch → process → store → report."""

import logging
from newsfeed.config import SiteConfig, SiteState, load_site_config, load_state, save_state
from newsfeed.fetch import fetch_new_articles
from newsfeed.processing import process_article
from newsfeed.storage.repository import save_article
from newsfeed.cost import get_daily_cost, reset_daily_usage

log = logging.getLogger("newsfeed.pipeline")

def fetch(config, state, from_date, to_date, max_pages):
    """Layer 1: Discover and fetch articles."""
    return fetch_new_articles(config, state, from_date=from_date, to_date=to_date, max_pages=max_pages)

def process(articles, config):
    """Layer 2: Clean and enrich articles."""
    processed = []
    for a in articles:
        if a.get("content"):
            processed.append(process_article(dict(a), config))
        else:
            processed.append(a)
    return processed

def store(articles, config):
    """Layer 3: Save to database."""
    saved, failed = 0, 0
    for a in articles:
        if save_article(a, config.name, config.listing_url):
            saved += 1
        else:
            failed += 1
    log.info(f"Storage: {saved} saved, {failed} failed")
    return saved, failed

def report():
    """Cost reporting."""
    cost = get_daily_cost()
    log.info(f"Cost: ${cost['total_cost']:.6f} ({cost['input_tokens']} in, {cost['output_tokens']} out)")
    return cost

def run(site_name, from_date=None, to_date=None, max_pages=5, no_verify_ssl=False):
    config = load_site_config(site_name)
    if no_verify_ssl:
        config.verify_ssl = False
    state = load_state(site_name)
    reset_daily_usage()

    log.info(f"=== Running {config.name} ===")
    articles = fetch(config, state, from_date, to_date, max_pages)

    saved, failed = 0, 0
    for a in articles:
        processed = process_article(dict(a), config) if a.get("content") else a
        if save_article(processed, config.name, config.listing_url):
            saved += 1
        else:
            failed += 1

    save_state(state)
    cost = report()
    log.info(f"=== {config.name}: {len(articles)} fetched, {saved} saved, {failed} failed ===")

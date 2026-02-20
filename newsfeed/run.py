"""
Entry point for the newsfeed pipeline.

Usage:
    python -m newsfeed.run                          # run all sites
    python -m newsfeed.run --site dcd               # run one site
    python -m newsfeed.run --site dcd --from 2026-02-19 --to 2026-02-20   # manual date range
    python -m newsfeed.run --site dcd --max-pages 2 # limit pages
"""

import argparse, logging, json
from newsfeed.config import load_site_config, load_all_site_configs, load_state, save_state
from newsfeed.fetch import fetch_new_articles
from newsfeed.processing import process_article
from dotenv import load_dotenv
from newsfeed.cost import get_daily_cost, reset_daily_usage

load_dotenv()


logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(name)s] %(message)s")
log = logging.getLogger("newsfeed.run")

def run_site(site_name: str, from_date=None, to_date=None, max_pages=5, no_verify_ssl=False):
    """Run the full pipeline for a single site."""
    config = load_site_config(site_name)
    if no_verify_ssl:
        config.verify_ssl = False
        print(f"verify_ssl = {config.verify_ssl}")
    state = load_state(site_name)

    log.info(f"=== Running {config.name} ===")
    articles = fetch_new_articles(config, state, from_date=from_date, to_date=to_date, max_pages=max_pages)

    processed_articles = []
    for a in articles:
        if a.get("content"):
            processed = process_article(dict(a), config)
            processed_articles.append(processed)
        else:
            processed_articles.append(a)

    save_state(state)
    log.info(f"=== {config.name}: {len(processed_articles)} articles processed, state saved ===")
    cost = get_daily_cost()
    log.info(f"Cost: ${cost['total_cost']:.6f} ({cost['input_tokens']} in, {cost['output_tokens']} out)")
    return processed_articles

def run_all(from_date=None, to_date=None, max_pages=5):
    """Run the full pipeline for all configured sites."""
    configs = load_all_site_configs()
    all_results = {}
    for site_name in configs:
        all_results[site_name] = run_site(site_name, from_date, to_date, max_pages)
    return all_results

def main():
    parser = argparse.ArgumentParser(description="Market Intelligence News Feed Pipeline")
    parser.add_argument("--site", type=str, default=None, help="Run a specific site (e.g. 'dcd')")
    parser.add_argument("--from", dest="from_date", type=str, default=None, help="Start date (YYYY-MM-DD)")
    parser.add_argument("--to", dest="to_date", type=str, default=None, help="End date (YYYY-MM-DD)")
    parser.add_argument("--max-pages", type=int, default=5, help="Max listing pages to fetch (default: 5)")
    parser.add_argument("--no-verify-ssl", action="store_true", help="Disable SSL verification")
    args = parser.parse_args()

    if args.site:
        results = run_site(args.site, args.from_date, args.to_date, args.max_pages, args.no_verify_ssl)
    else:
        results = run_all(args.from_date, args.to_date, args.max_pages)

if __name__ == "__main__":
    main()

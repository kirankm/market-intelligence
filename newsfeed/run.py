"""CLI entry point for the newsfeed pipeline."""

import argparse, logging
from dotenv import load_dotenv
load_dotenv()

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(name)s] %(message)s")

from newsfeed.pipeline import run

def main():
    parser = argparse.ArgumentParser(description="Market Intelligence News Feed")
    parser.add_argument("--site", default=None, help="Site name (e.g. dcd)")
    parser.add_argument("--from", dest="from_date", default=None, help="From date (YYYY-MM-DD)")
    parser.add_argument("--to", dest="to_date", default=None, help="To date (YYYY-MM-DD)")
    parser.add_argument("--max-pages", type=int, default=5, help="Max listing pages to fetch")
    parser.add_argument("--no-verify-ssl", action="store_true", help="Disable SSL verification")
    args = parser.parse_args()

    if args.site:
        run(args.site, args.from_date, args.to_date, args.max_pages, args.no_verify_ssl)
    else:
        from newsfeed.config import load_all_site_configs
        for site_name in load_all_site_configs():
            run(site_name, args.from_date, args.to_date, args.max_pages, args.no_verify_ssl)

if __name__ == "__main__":
    from newsfeed.web.queries.feed import set_job_complete
    from newsfeed.storage.database import get_session
    try:
        main()
        db = get_session()
        set_job_complete(db, 'pipeline', success=True)
        db.close()
    except Exception as e:
        db = get_session()
        set_job_complete(db, 'pipeline', success=False, error=str(e))
        db.close()


"""Background worker — processes pending keyword summaries via Gemini."""
import time, logging
from dotenv import load_dotenv
load_dotenv()
import google.generativeai as genai
from datetime import datetime
from newsfeed.storage.database import get_session
from newsfeed.storage.models import KeywordSummary, Article, ArticleSummary
from sqlalchemy import desc, cast, String
from newsfeed.web.queries.feed import search_articles

log = logging.getLogger("newsfeed.keyword_summarizer")

PROMPT_TEMPLATE = """You are a market intelligence analyst.
Summarize the following {count} articles matching the search query "{query}".
Provide a concise 3-5 sentence summary highlighting key themes, trends, and implications.

Articles:
{articles_text}
"""


def get_pending_summaries(db):
    """Fetch all pending keyword summary requests."""
    return (db.query(KeywordSummary)
            .filter(KeywordSummary.status == 'pending')
            .order_by(KeywordSummary.created_at)
            .all())

def get_matching_articles(db, query, limit=50):
    """Fetch articles matching the search query."""
    term = f"%{query}%"
    return (db.query(Article)
            .outerjoin(ArticleSummary)
            .filter(Article.title.ilike(term) |
                    ArticleSummary.subtitle.ilike(term) |
                    cast(ArticleSummary.bullets, String).ilike(term))
            .order_by(desc(Article.date))
            .limit(limit)
            .all())

def format_articles(articles):
    """Format articles for the LLM prompt."""
    parts = []
    for a in articles:
        date_str = a.date.strftime('%Y-%m-%d') if a.date else 'Unknown'
        parts.append(f"- [{date_str}] {a.title}")
    return '\n'.join(parts)


def generate_summary(query, articles):
    """Call Gemini to generate the summary."""
    model = genai.GenerativeModel('gemini-2.5-flash')
    prompt = PROMPT_TEMPLATE.format(
        count=len(articles),
        query=query,
        articles_text=format_articles(articles)
    )
    response = model.generate_content(prompt)
    return response.text


def process_one(db, ks):
    """Process a single pending keyword summary."""
    try:
        log.info(f"Searching for: '{ks.query}'")
        articles = search_articles(db, ks.query)
        log.info(f"Found {len(articles)} articles for '{ks.query}'")
        if not articles:
            ks.status = 'failed'
            ks.summary = 'No matching articles found'
        else:
            ks.summary = generate_summary(ks.query, articles)
            ks.status = 'complete'
            ks.article_count = len(articles)
        ks.completed_at = datetime.now()
        db.commit()
        log.info(f"Completed summary {ks.id} for query '{ks.query}'")
    except Exception as e:
        ks.status = 'failed'
        ks.summary = str(e)
        ks.completed_at = datetime.now()
        db.commit()
        log.error(f"Failed summary {ks.id}: {e}")


def run_once(db):
    """Process all pending summaries."""
    pending = get_pending_summaries(db)
    for ks in pending:
        process_one(db, ks)
    return len(pending)


def run_loop(poll_interval=5):
    """Continuously poll for and process pending summaries."""
    log.info(f"Starting keyword summarizer (poll every {poll_interval}s)")
    while True:
        db = get_session()
        try:
            count = run_once(db)
            if count: log.info(f"Processed {count} summaries")
        finally:
            db.close()
        time.sleep(poll_interval)


if __name__ == "__main__":
    import argparse
    logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(name)s] %(message)s")
    parser = argparse.ArgumentParser()
    parser.add_argument("--once", action="store_true", help="Process pending and exit")
    parser.add_argument("--interval", type=int, default=5, help="Poll interval in seconds")
    args = parser.parse_args()
    if args.once:
        db = get_session()
        run_once(db)
        db.close()
    else:
        run_loop(args.interval)

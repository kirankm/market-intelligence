"""Job endpoints — triggered by Cloud Scheduler or admin UI."""
from fasthtml.common import *
from newsfeed.web.scripts.keyword_summarizer import run_once
from newsfeed.web.queries.admin import set_job_complete
import logging

ar = APIRouter()

@ar.get('/process-pending-keywords')
def process_pending_keywords(request):
    db = request.state.db
    try:
        count = run_once(db)
        set_job_complete(db, 'keyword_summarizer', success=True)
        return JSONResponse({'processed': count})
    except Exception as e:
        set_job_complete(db, 'keyword_summarizer', success=False, error=str(e))
        return JSONResponse({'status': 'error', 'message': str(e)}, status_code=500)

@ar.get('/run-pipeline')
def run_pipeline(request):
    db = request.state.db
    try:
        logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(name)s] %(message)s")
        from newsfeed.config import load_all_site_configs
        from newsfeed.pipeline import run
        for site_name in load_all_site_configs():
            run(site_name)
        set_job_complete(db, 'pipeline', success=True)
        return JSONResponse({'status': 'success'})
    except Exception as e:
        set_job_complete(db, 'pipeline', success=False, error=str(e))
        return JSONResponse({'status': 'error', 'message': str(e)}, status_code=500)

@ar.get('/run-category-summaries')
def run_category_summaries(request):
    db = request.state.db
    try:
        logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(name)s] %(message)s")
        from newsfeed.scripts.category_summaries import run
        run()
        set_job_complete(db, 'category_summarizer', success=True)
        return JSONResponse({'status': 'success'})
    except Exception as e:
        set_job_complete(db, 'category_summarizer', success=False, error=str(e))
        return JSONResponse({'status': 'error', 'message': str(e)}, status_code=500)

@ar.get('/run-newsletter')
def run_newsletter(request):
    db = request.state.db
    try:
        logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(name)s] %(message)s")
        from newsfeed.scripts.create_newsletter import run
        run()
        set_job_complete(db, 'newsletter_creator', success=True)
        return JSONResponse({'status': 'success'})
    except Exception as e:
        set_job_complete(db, 'newsletter_creator', success=False, error=str(e))
        return JSONResponse({'status': 'error', 'message': str(e)}, status_code=500)

@ar.get('/backfill')
def backfill(request):
    try:
        logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(name)s] %(message)s")
        from newsfeed.backfill import run_backfill
        result = run_backfill()
        return JSONResponse({'status': 'success', **result})
    except Exception as e:
        return JSONResponse({'status': 'error', 'message': str(e)}, status_code=500)

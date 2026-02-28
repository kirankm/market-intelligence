from fasthtml.common import *
from newsfeed.web.scripts.keyword_summarizer import run_once
import logging

ar = APIRouter()

@ar.get('/process-pending-keywords')
def process_pending_keywords(request):
    db = request.state.db
    count = run_once(db)
    return JSONResponse({'processed': count})

@ar.get('/run-pipeline')
def run_pipeline(request):
    try:
        logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(name)s] %(message)s")
        from newsfeed.config import load_all_site_configs
        from newsfeed.pipeline import run
        for site_name in load_all_site_configs():
            run(site_name)
        return JSONResponse({'status': 'success'})
    except Exception as e:
        return JSONResponse({'status': 'error', 'message': str(e)}, status_code=500)

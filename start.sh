#!/bin/bash
python -c "from newsfeed.storage.database import init_db; init_db()"
python -c "
from newsfeed.storage.database import get_session
from newsfeed.storage.models import User
db = get_session()
if db.query(User).count() == 0:
    import subprocess, sys
    cmds = [
        [sys.executable, '-m', 'newsfeed.web.scripts.seed_user', 'Alice', 'alice@equinix.com', 'contributor'],
        [sys.executable, '-m', 'newsfeed.web.scripts.seed_user', 'Bob', 'bob@equinix.com', 'viewer'],
        [sys.executable, '-m', 'newsfeed.web.scripts.seed_user', 'Admin', 'admin@equinix.com', 'admin'],
        [sys.executable, '-m', 'newsfeed.web.scripts.seed_setting', 'top_tags_count', '5'],
        [sys.executable, '-m', 'newsfeed.web.scripts.seed_setting', 'min_articles_for_summary', '5'],
        [sys.executable, '-m', 'newsfeed.web.scripts.seed_setting', 'search_debounce_ms', '300'],
        [sys.executable, '-m', 'newsfeed.web.scripts.seed_setting', 'page_size', '20'],
        [sys.executable, '-m', 'newsfeed.web.scripts.seed_setting', 'summary_categories', 'Telecom,Expansion,Funding,AI,Partnership'],
    ]
    for cmd in cmds: subprocess.run(cmd, check=True)
    print('Seeded successfully')
else:
    print('Data exists, skipping seed')
db.close()
"
uvicorn newsfeed.web.app:app --host 0.0.0.0 --port 8080






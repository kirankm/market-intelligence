"""Feed queries — re-export layer for backward compatibility.

All query functions have been split into focused modules:
  - articles.py  — article fetching, search, stars
  - tags.py      — tag counts, edits, add/remove
  - settings.py  — app settings CRUD
  - users.py     — user/role CRUD
  - digests.py   — digests, category summaries, keyword summaries
  - admin.py     — jobs, sources, costs
"""

# Articles
from newsfeed.web.queries.articles import (
    get_articles, get_starred_articles, get_article, get_latest_summary,
    article_tags, is_starred, toggle_star, search_articles
)

# Tags
from newsfeed.web.queries.tags import (
    get_tags_with_counts, get_sources_with_counts,
    get_starred_tags_with_counts, get_starred_sources_with_counts,
    get_all_tags, add_tag_to_article, remove_tag_from_article
)

# Settings
from newsfeed.web.queries.settings import (
    get_setting, get_all_settings, upsert_setting, delete_setting
)

# Users
from newsfeed.web.queries.users import (
    get_all_users, get_all_roles, get_user_role_name,
    create_user, update_user_role, delete_user
)

# Digests & Category Summaries
from newsfeed.web.queries.digests import (
    get_category_summaries, get_category_article_counts,
    get_category_star_counts, get_available_summary_periods,
    get_digests, get_digest_articles, publish_digest, unpublish_digest,
    get_latest_digest_summary, get_original_digest_summary,
    create_digest_summary_version, create_keyword_summary,
    get_keyword_summary, get_recent_keyword_summaries, delete_keyword_summary
)

# Admin
from newsfeed.web.queries.admin import (
    JOBS, get_all_sources, toggle_source_active,
    get_cost_by_source, get_cost_totals,
    get_job_status, set_job_running, run_job_background, set_job_complete
)

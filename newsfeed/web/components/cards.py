"""Backward-compatible re-export layer — import from submodules directly for new code."""

# Article components
from newsfeed.web.components.article import (
    tag_pill, tag_display, tag_editor, card_meta, star_icon,
    highlight, summary_section, article_card, expanded_card, load_more_sentinel
)

# Filter components
from newsfeed.web.components.filters import (
    build_filter_url, build_tags_param,
    PILL, PILL_ACTIVE, PILL_INACTIVE, PILL_CLEAR, PILL_MORE,
    BTN_SUCCESS, BTN_WARNING, BTN_PRIMARY, EXEC_INPUT,
    tag_pill_filter, clear_pill, more_pill, less_pill,
    tag_filter, source_filter, date_button, date_filter, search_box,
    collapsible_section, period_label, category_period_dropdown
)

# Layout components
from newsfeed.web.components.layouts import (
    category_tab, category_ribbon, category_card,
    digest_tab, digest_ribbon, digest_item, digest_expanded,
    digest_summary_display, digest_summary_edit_form,
    exec_search_box, exec_search_results,
    keyword_summary_item, keyword_summaries_list
)

# Admin components
from newsfeed.web.components.admin import (
    ADMIN_TABS, VALID_ROLES, COST_PERIODS,
    format_ago, admin_tab, admin_ribbon,
    settings_row, settings_edit_row, settings_add_form, settings_table,
    user_row, user_edit_row, user_add_form, users_table,
    source_status_icon, source_row, sources_table,
    cost_period_button, cost_period_filter, cost_row, cost_totals_row, costs_table,
    job_status_badge, job_params_form, job_row, jobs_table
)

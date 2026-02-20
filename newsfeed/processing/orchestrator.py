import logging
from newsfeed.config import SiteConfig
from .noise import remove_noise
from .extraction import extract_jina_meta, extract_body_by_markers, extract_body_by_heuristic
from .cleanup import decode_entities, normalize_whitespace, strip_links, strip_images, strip_byline
from .summarization import summarize
from .tagging import auto_tag

log = logging.getLogger("newsfeed.processing")

# ── Tool Registry ──────────────────────────────────────────

TOOLS = {}

def register_tool(name):
    def decorator(fn):
        TOOLS[name] = fn
        return fn
    return decorator

# ── Registered Tools ───────────────────────────────────────

@register_tool("extract_jina_meta")
def _tool_extract_jina_meta(article: dict, config: SiteConfig) -> dict:
    meta = extract_jina_meta(article.get("content") or "")
    article["jina_title"] = meta["jina_title"]
    article["jina_url"] = meta["jina_url"]
    article["content"] = meta["body"]
    return article

@register_tool("extract_body")
def _tool_extract_body(article: dict, config: SiteConfig) -> dict:
    if config.content_start or config.content_end:
        article["content"] = extract_body_by_markers(article["content"], config.content_start, config.content_end)
    else:
        article["content"] = extract_body_by_heuristic(article["content"])
    return article

@register_tool("remove_noise")
def _tool_remove_noise(article: dict, config: SiteConfig) -> dict:
    article["content"] = remove_noise(article["content"])
    return article

@register_tool("decode_entities")
def _tool_decode_entities(article: dict, config: SiteConfig) -> dict:
    article["content"] = decode_entities(article["content"])
    article["title"] = decode_entities(article.get("title", ""))
    return article

@register_tool("normalize_whitespace")
def _tool_normalize(article: dict, config: SiteConfig) -> dict:
    article["content"] = normalize_whitespace(article["content"])
    return article

@register_tool("strip_links")
def _tool_strip_links(article: dict, config: SiteConfig) -> dict:
    article["content"] = strip_links(article["content"])
    return article

@register_tool("strip_images")
def _tool_strip_images(article: dict, config: SiteConfig) -> dict:
    article["content"] = strip_images(article["content"])
    return article

@register_tool("strip_byline")
def _tool_strip_byline(article: dict, config: SiteConfig) -> dict:
    article["content"] = strip_byline(article["content"])
    return article

@register_tool("summarize")
def _tool_summarize(article: dict, config) -> dict:
    result = summarize(article.get("content", ""))
    article["subtitle"] = result.get("subtitle", "")
    article["bullets"] = result.get("bullets", [])
    return article

@register_tool("auto_tag")
def _tool_auto_tag(article: dict, config) -> dict:
    article["tags"] = auto_tag(article.get("content", ""))
    return article

# ── Pipeline Runner ─────────────────────────────────────────

def process_article(article: dict, config: SiteConfig, pipeline: list[str] = None) -> dict:
    """Run an article through the processing pipeline."""
    if pipeline is None:
        pipeline = config.pipeline
    for tool_name in pipeline:
        tool = TOOLS.get(tool_name)
        if tool:
            article = tool(article, config)
        else:
            log.warning(f"Unknown processing tool: {tool_name}")
    return article

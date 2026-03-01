"""AI summarization using Gemini with retry + failure tracking."""

import os, json, re, time, logging
from google import genai
from newsfeed.cost import track_usage

log = logging.getLogger("newsfeed.processing")

SUMMARY_SCHEMA = {
    "type": "object",
    "properties": {
        "subtitle": {"type": "string", "description": "One sentence: what happened and why it matters"},
        "bullets": {
            "type": "array",
            "items": {"type": "string"},
            "minItems": 3,
            "maxItems": 5,
            "description": "Key facts: who, what, where, how much, when"
        }
    },
    "required": ["subtitle", "bullets"]
}

SUMMARY_PROMPT = """You are a market intelligence analyst for a data center company.
Summarize this article for a sales team.

Return JSON with exactly this structure:
{
    "subtitle": "One sentence: what happened and why it matters",
    "bullets": ["key fact 1", "key fact 2", "key fact 3"]
}

Rules:
- subtitle: max 15 words, headline style, no filler words
- bullets: 3-5 items, each a key fact (who, what, where, how much, when)
- Focus on competitive intelligence: new builds, expansions, partnerships, financials
- No fluff, no opinions

Article:
"""

# ── Failure Tracking ────────────────────────────────────────

def log_failure(url: str, step: str, error: str, retries: int, db=None):
    """Log a failure record to the database."""
    from newsfeed.storage.models import Failure
    own_session = db is None
    if own_session:
        from newsfeed.storage.database import get_session
        db = get_session()
    try:
        # Update existing unresolved failure or create new
        existing = (db.query(Failure)
                    .filter(Failure.url == url, Failure.step == step, Failure.resolved == False)
                    .first())
        if existing:
            existing.error = error
            existing.retries = retries
        else:
            db.add(Failure(url=url, step=step, error=error, retries=retries))
        db.commit()
    except Exception as e:
        log.error(f"Failed to log failure to DB: {e}")
        db.rollback()
    finally:
        if own_session:
            db.close()

# ── Gemini Client ───────────────────────────────────────────

_client = None

def _get_client():
    global _client
    if _client is None:
        api_key = os.environ.get("GOOGLE_API_KEY")
        if not api_key:
            raise ValueError("GOOGLE_API_KEY not set in environment")
        _client = genai.Client(api_key=api_key)
    return _client

# ── JSON Extraction ─────────────────────────────────────────

def extract_json(text: str) -> dict:
    """Extract JSON from response text, handling markdown fences and extra text."""
    # Strip markdown fences
    cleaned = re.sub(r'```(?:json)?\s*', '', text).strip()
    cleaned = re.sub(r'```\s*$', '', cleaned).strip()
    # Try parsing directly
    try: return json.loads(cleaned)
    except json.JSONDecodeError: pass
    # Fallback: find first { ... } block
    match = re.search(r'\{.*\}', cleaned, re.DOTALL)
    if match:
        try: return json.loads(match.group())
        except json.JSONDecodeError: pass
    raise ValueError(f"Could not extract JSON from response: {text[:200]}")

# ── Summarize with Retry ───────────────────────────────────

def summarize(text: str, url: str = "", model: str = None,
              max_retries: int = 3, retry_delay: float = 2.0) -> dict:
    """Generate subtitle + bullet summary with retry logic."""
    from newsfeed.config import DEFAULT_MODEL, MODELS_WITH_JSON_MODE
    if model is None: model = DEFAULT_MODEL
    client = _get_client()
    use_json_mode = model in MODELS_WITH_JSON_MODE

    for attempt in range(1, max_retries + 1):
        try:
            config = {"response_mime_type": "application/json"} if use_json_mode else {}
            response = client.models.generate_content(
                model=model,
                contents=SUMMARY_PROMPT + text,
                config=config,
            )
            # Track cost
            usage = response.usage_metadata
            input_tok = getattr(usage, 'prompt_token_count', None) or 0
            output_tok = getattr(usage, 'candidates_token_count', None) or 0
            track_usage(input_tok, output_tok, model)
            log.info(f"Summarized ({input_tok} in, {output_tok} out tokens)")

            result = extract_json(response.text) if not use_json_mode else json.loads(response.text)

            # Validate structure
            if "subtitle" not in result or "bullets" not in result:
                raise ValueError(f"Missing fields in response: {list(result.keys())}")
            if not isinstance(result["bullets"], list) or len(result["bullets"]) < 1:
                raise ValueError(f"Invalid bullets: {result['bullets']}")

            return result

        except Exception as e:
            log.warning(f"Attempt {attempt}/{max_retries} failed: {e}")
            if attempt < max_retries:
                time.sleep(retry_delay * (2 ** attempt))  # exponential backoff
            else:
                log.error(f"All {max_retries} attempts failed for: {url}")
                log_failure(url, "summarize", str(e), max_retries)
                return {"subtitle": "", "bullets": []}

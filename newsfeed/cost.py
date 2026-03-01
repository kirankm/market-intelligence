"""Cost tracking for LLM API usage."""
import threading
from newsfeed.config import DEFAULT_MODEL

_lock = threading.Lock()

# Pricing per 1M tokens
PRICING = {
    "gemini-2.5-flash": {"input": 0.30, "output": 2.50},
    "gemini-2.5-pro":   {"input": 1.25, "output": 10.00},
    "gemini-3-flash":   {"input": 0.50, "output": 3.00},
    "gemma-3-27b-it":   {"input": 0.00, "output": 0.00},  # free tier
}

_daily_usage = {"input_tokens": 0, "output_tokens": 0, "model": DEFAULT_MODEL}

def track_usage(input_tokens: int, output_tokens: int, model: str = None):
    """Add token counts to daily running total."""
    if model is None: model = DEFAULT_MODEL
    with _lock:
        _daily_usage["input_tokens"] += input_tokens or 0
        _daily_usage["output_tokens"] += output_tokens or 0
        _daily_usage["model"] = model

def get_daily_cost() -> dict:
    """Calculate cost for today's usage."""
    with _lock:
        model = _daily_usage["model"]
        input_tokens = _daily_usage["input_tokens"]
        output_tokens = _daily_usage["output_tokens"]
    prices = PRICING.get(model, PRICING[DEFAULT_MODEL])
    input_cost = (input_tokens / 1_000_000) * prices["input"]
    output_cost = (output_tokens / 1_000_000) * prices["output"]
    return {
        "model": model,
        "input_tokens": input_tokens,
        "output_tokens": output_tokens,
        "input_cost": round(input_cost, 6),
        "output_cost": round(output_cost, 6),
        "total_cost": round(input_cost + output_cost, 6),
    }

def reset_daily_usage():
    """Reset counters (call at start of each run)."""
    with _lock:
        _daily_usage["input_tokens"] = 0
        _daily_usage["output_tokens"] = 0

import re, html

def decode_entities(text: str) -> str:
    """Decode HTML entities like &#x27; → '"""
    return html.unescape(text)

def normalize_whitespace(text: str) -> str:
    """Collapse 3+ blank lines to 2, strip trailing spaces."""
    text = re.sub(r'\n{3,}', '\n\n', text)
    text = re.sub(r'[ \t]+$', '', text, flags=re.MULTILINE)
    return text.strip()

def strip_links(text: str) -> str:
    """Convert [text](url) → text, remove bare [](url)."""
    return re.sub(r'\[([^\]]*)\]\([^)]+\)', r'\1', text)

def strip_images(text: str) -> str:
    """Remove ![alt](url) image tags and standalone captions like '– Google Maps'."""
    text = re.sub(r'!\[[^\]]*\]\([^)]+\)', '', text)
    text = re.sub(r'^–\s+.{1,30}$', '', text, flags=re.MULTILINE)
    return text

def strip_byline(text: str) -> str:
    """Remove byline line like 'February 19, 2026 ByDan SwinhoeHave your say'."""
    return re.sub(
        r'^(?:January|February|March|April|May|June|July|August|September|October|November|December)\s+\d{1,2},\s+\d{4}\s+By.+$',
        '', text, count=1, flags=re.MULTILINE
    )

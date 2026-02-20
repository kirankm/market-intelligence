import re
from typing import Optional

def extract_jina_meta(raw: str) -> dict:
    """Parse Jina header: Title, URL Source, and body after 'Markdown Content:'."""
    title = re.search(r'^Title:\s*(.+)$', raw, re.MULTILINE)
    url = re.search(r'^URL Source:\s*(.+)$', raw, re.MULTILINE)
    body_start = raw.find('Markdown Content:')
    body = raw[body_start + len('Markdown Content:'):].strip() if body_start != -1 else raw
    return {
        "jina_title": title.group(1).strip() if title else None,
        "jina_url": url.group(1).strip() if url else None,
        "body": body,
    }

def extract_body_by_markers(text: str, start_marker: Optional[str] = None, end_marker: Optional[str] = None) -> str:
    """Extract body between optional start/end regex markers."""
    start_idx = 0
    end_idx = len(text)
    if start_marker:
        m = re.search(start_marker, text, re.MULTILINE)
        if m: start_idx = m.start()
    if end_marker:
        m = re.search(end_marker, text[start_idx:], re.MULTILINE)
        if m: end_idx = start_idx + m.start()
    return text[start_idx:end_idx].strip()

def extract_body_by_heuristic(text: str, min_paragraph_len: int = 80) -> str:
    """Fallback: find the longest contiguous run of real paragraphs."""
    lines = text.split('\n')
    best_start, best_end, best_len = 0, 0, 0
    curr_start, curr_len = None, 0

    for i, line in enumerate(lines):
        stripped = line.strip()
        is_paragraph = len(stripped) >= min_paragraph_len and not stripped.startswith(('*', '-', '|', '#', '[', '!'))
        if is_paragraph:
            if curr_start is None: curr_start = i
            curr_len += len(stripped)
        elif stripped == '':
            continue
        else:
            if curr_len > best_len:
                best_start, best_end, best_len = curr_start or 0, i, curr_len
            curr_start, curr_len = None, 0
    if curr_len > best_len:
        best_start, best_end = curr_start or 0, len(lines)
    return '\n'.join(lines[best_start:best_end]).strip()

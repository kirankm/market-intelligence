import re

def is_nav_block(lines: list[str], threshold: int = 5) -> list[tuple[int, int]]:
    """Find blocks of 5+ consecutive bullet-point links (nav menus)."""
    blocks, start, count = [], None, 0
    for i, line in enumerate(lines):
        if re.match(r'\s*\*\s+\[', line):
            if start is None: start = i
            count += 1
        else:
            if count >= threshold: blocks.append((start, i - 1))
            start, count = None, 0
    if count >= threshold: blocks.append((start, len(lines) - 1))
    return blocks

def is_link_cluster(lines: list[str], threshold: int = 4) -> list[tuple[int, int]]:
    """Find blocks of consecutive lines that are mostly links with no paragraph text."""
    blocks, start, count = [], None, 0
    for i, line in enumerate(lines):
        stripped = line.strip()
        if stripped and (re.match(r'\[.*\]\(.*\)', stripped) or re.match(r'\*\s+\[', stripped)):
            if start is None: start = i
            count += 1
        elif stripped == '':
            continue
        else:
            if count >= threshold: blocks.append((start, i - 1))
            start, count = None, 0
    if count >= threshold: blocks.append((start, len(lines) - 1))
    return blocks

def is_form_block(lines: list[str]) -> list[tuple[int, int]]:
    """Detect form regions (inputs, dropdowns, checkboxes, country lists)."""
    form_patterns = re.compile(
        r'(^\s*(Nome|Email|Telefone|Empresa|Segmento)\*?\s*$)'
        r'|(\(?\+\d{1,4}\)\s*$)'
        r'|(- \[[ x]\])'
        r'|(^\s*Submit\s*$)'
        r'|(^\s*Iniciar a conversa\s*$)',
        re.IGNORECASE
    )
    blocks, start, form_line_count, total_count = [], None, 0, 0
    for i, line in enumerate(lines):
        if form_patterns.search(line):
            if start is None: start = i
            form_line_count += 1
            total_count += 1
        else:
            total_count += 1
            if start is not None and form_line_count < 2 and (total_count - form_line_count) > 3:
                if form_line_count >= 3: blocks.append((start, i - 1))
                start, form_line_count, total_count = None, 0, 0
    if form_line_count >= 3: blocks.append((start, len(lines) - 1))
    return blocks

def is_cookie_banner(line: str) -> bool:
    """Detect cookie/consent banner lines."""
    return bool(re.search(r'cookie|consent|privac|aceitar|recusar', line, re.IGNORECASE))

def is_share_row(line: str) -> bool:
    """Detect social share link rows."""
    social = re.findall(r'\[(Facebook|Twitter|LinkedIn|Reddit|Email|Share)\]', line, re.IGNORECASE)
    return len(social) >= 3

def remove_noise(text: str) -> str:
    """Remove all detected noise blocks from markdown text."""
    lines = text.split('\n')

    noise_ranges = []
    noise_ranges.extend(is_nav_block(lines))
    noise_ranges.extend(is_link_cluster(lines))
    noise_ranges.extend(is_form_block(lines))

    noise_lines = set()
    for start, end in noise_ranges:
        noise_lines.update(range(start, end + 1))
    for i, line in enumerate(lines):
        if is_cookie_banner(line) or is_share_row(line):
            noise_lines.add(i)

    cleaned = [line for i, line in enumerate(lines) if i not in noise_lines]
    return '\n'.join(cleaned)

"""Filter state management."""
from dataclasses import dataclass, field
from datetime import date, timedelta


@dataclass
class FilterState:
    tags: set = field(default_factory=set)
    source: str = ''
    date: str = ''
    search: str = ''
    expanded: bool = False
    base: str = '/feed'
    target: str = 'feed-content'

    def to_params(self):
        """Convert to URL params dict (excludes base)."""
        return {
            'tags': ','.join(sorted(self.tags)) if self.tags else '',
            'source': self.source,
            'date': self.date,
            'search': self.search,
            'expanded': '1' if self.expanded else '0',
        }

    @classmethod
    def from_request(cls, tags='', source='', date='', search='', expanded='0', base='/feed', target='feed-content'):
        parsed_tags = {t.strip() for t in tags.split(',') if t.strip()}
        return cls(tags=parsed_tags, source=source, date=date, search=search,
                   expanded=expanded == '1', base=base, target=target)

def date_range(period):
    """Convert period string to (date_from, date_to)."""
    today = date.today()
    if period == 'today': return today, today
    if period == 'week':  return today - timedelta(days=today.weekday()), today
    if period == 'month': return today.replace(day=1), today
    return None, None


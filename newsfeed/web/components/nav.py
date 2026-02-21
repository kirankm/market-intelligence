from fasthtml.common import *

NAV_BY_ROLE = {
    'contributor': [('Feed', '/feed')],
    'viewer':      [('Executive', '/executive'), ('Feed', '/feed'), ('Sources', '/admin/sources')],
    'admin':       [('Feed', '/feed'), ('Executive', '/executive'), ('Sources', '/admin/sources')],
    'moderator':   [('Feed', '/feed')],
}


def nav_links(role, current_path):
    """Build nav links, highlighting the current page."""
    links = NAV_BY_ROLE.get(role, [])
    return [A(label, href=path,
              cls="font-bold" if path == current_path else "")
            for label, path in links]


def navbar(session, current_path):
    """Render full nav bar."""
    role = session.get('role', '')
    name = session.get('user_name', '')
    return Nav(
        Div(Strong("MI News Feed"), cls="flex-none"),
        Div(*nav_links(role, current_path), cls="flex gap-4"),
        Div(Span(name, cls="mr-2"), A("Logout", href="/logout")),
        cls="flex items-center justify-between p-4 border-b"
    )

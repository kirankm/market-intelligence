"""Shared navigation bar."""
from fasthtml.common import *
from monsterui.all import DivFullySpaced, DivHStacked, TextPresets

NAV_BY_ROLE = {
    'contributor': [('Feed', '/feed')],
    'viewer':      [('Executive', '/executive'), ('Feed', '/feed'), ('Admin', '/admin/sources')],
    'admin':       [('Feed', '/feed'), ('Executive', '/executive'), ('Admin', '/admin/sources')],
    'moderator':   [('Feed', '/feed')],
}


def nav_links(role, current_path):
    """Build nav links, highlighting the current page."""
    links = NAV_BY_ROLE.get(role, [])
    return [A(label, href=path,
              cls="font-semibold text-foreground" if path == current_path
              else TextPresets.muted_sm + " hover:text-foreground transition")
            for label, path in links]


def navbar(session, current_path):
    """Render full nav bar."""
    role = session.get('role', '')
    name = session.get('user_name', '')
    return Nav(
        DivFullySpaced(
            Strong("MI News Feed", cls="text-foreground"),
            DivHStacked(*nav_links(role, current_path), cls="gap-6"),
            DivHStacked(
                P(name, cls=TextPresets.muted_sm),
                A("Logout", href="/logout", cls=TextPresets.muted_sm + " hover:text-foreground transition"),
                cls="gap-3"
            ),
        ),
        cls="border-b border-border p-4 bg-background sticky top-0 z-10"
    )


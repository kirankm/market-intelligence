"""Login and logout routes."""
from fasthtml.common import *
from fasthtml.core import APIRouter
from monsterui.all import Card, ButtonT, DivCentered
from newsfeed.storage.models import User, Role, UserRole

ar = APIRouter()


def lookup_user(db, email):
    """Find user by email."""
    return db.query(User).filter(User.email == email).first()


def get_user_role(db, user):
    """Get primary role name for user."""
    role = (db.query(Role)
            .join(UserRole)
            .filter(UserRole.user_id == user.id)
            .first())
    return role.name if role else None


def landing_for_role(role_name):
    """Return landing page path for role."""
    return '/executive' if role_name == 'viewer' else '/feed'


def login_form(error=None):
    """Render login page."""
    return Div(
        DivCentered(
            Card(
                H2("Market Intelligence Feed", cls="text-xl font-semibold text-foreground mb-4"),
                Form(
                    Label("Email", cls="text-sm font-medium text-foreground"),
                    Input(id="email", type="email", name="email",
                          placeholder="Enter your email", required=True,
                          cls="w-full text-sm border border-input rounded px-2.5 py-1.5 bg-background text-foreground focus:outline-none focus:ring-1 focus:ring-ring transition mb-3"),
                    Button("Sign In", type="submit", cls=ButtonT.primary + " w-full"),
                    P(error, cls="text-sm text-destructive mt-2") if error else None,
                    method="post", action="/login",
                    cls="space-y-2"
                ),
                cls="w-full max-w-sm"
            ),
            cls="min-h-screen bg-background"
        ),
    )


@ar('/login')
def get():
    return login_form()


@ar('/login')
def post(email: str, session, request):
    db = request.state.db
    user = lookup_user(db, email)
    if not user: return login_form("Not authorized")
    role = get_user_role(db, user)
    if not role: return login_form("No role assigned")
    session['user_id'] = user.id
    session['user_name'] = user.name
    session['role'] = role
    return Redirect(landing_for_role(role))


@ar('/logout')
def logout(session):
    session.clear()
    return Redirect('/login')


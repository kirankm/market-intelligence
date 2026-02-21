"""Login and logout routes."""
from fasthtml.common import *
from fasthtml.core import APIRouter
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
    """Render login page with optional error."""
    return Titled("Market Intelligence Feed",
        Form(
            Label("Email", _for="email"),
            Input(id="email", type="email", name="email",
                  placeholder="Enter your email", required=True),
            Button("Sign In", type="submit"),
            P(error, style="color:red") if error else None,
            method="post", action="/login"
        ))


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

"""Onboarding script — add a user with a role."""
import sys
from dotenv import load_dotenv
load_dotenv()
from newsfeed.storage.database import get_session
from newsfeed.storage.models import User, Role, UserRole


def get_or_create_role(db, role_name):
    """Find or create a role by name."""
    role = db.query(Role).filter(Role.name == role_name).first()
    if not role:
        role = Role(name=role_name)
        db.add(role)
        db.flush()
    return role


def create_user(db, name, email, role_name):
    """Create user and assign role."""
    existing = db.query(User).filter(User.email == email).first()
    if existing:
        print(f"User {email} already exists (id={existing.id})")
        return existing
    user = User(name=name, email=email)
    db.add(user)
    db.flush()
    role = get_or_create_role(db, role_name)
    db.add(UserRole(user_id=user.id, role_id=role.id))
    db.commit()
    print(f"Created user '{name}' ({email}) with role '{role_name}'")
    return user


VALID_ROLES = ('viewer', 'contributor', 'moderator', 'admin')

if __name__ == "__main__":
    if len(sys.argv) != 4:
        print("Usage: python -m newsfeed.web.scripts.seed_user <name> <email> <role>")
        print(f"Roles: {', '.join(VALID_ROLES)}")
        sys.exit(1)
    name, email, role_name = sys.argv[1], sys.argv[2], sys.argv[3]
    if role_name not in VALID_ROLES:
        print(f"Invalid role '{role_name}'. Must be one of: {', '.join(VALID_ROLES)}")
        sys.exit(1)
    db = get_session()
    try:
        create_user(db, name, email, role_name)
    finally:
        db.close()

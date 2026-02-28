"""User and role queries."""

from sqlalchemy.orm import joinedload
from newsfeed.storage.models import User, Role, UserRole


def get_all_users(db):
    """Fetch all users with their roles."""
    return (db.query(User)
            .options(joinedload(User.roles))
            .order_by(User.name)
            .all())


def get_all_roles(db):
    """Fetch all available roles."""
    return db.query(Role).order_by(Role.name).all()


def get_user_role_name(user):
    """Get primary role name for a user."""
    return user.roles[0].name if user.roles else 'none'


def create_user(db, name, email, role_name):
    """Create a new user with a role."""
    existing = db.query(User).filter(User.email == email).first()
    if existing: return None
    user = User(name=name, email=email)
    db.add(user)
    db.flush()
    role = db.query(Role).filter(Role.name == role_name).first()
    if role:
        db.add(UserRole(user_id=user.id, role_id=role.id))
    db.commit()
    return user


def update_user_role(db, user_id, new_role_name):
    """Update a user's role."""
    db.query(UserRole).filter(UserRole.user_id == user_id).delete()
    role = db.query(Role).filter(Role.name == new_role_name).first()
    if role:
        db.add(UserRole(user_id=user_id, role_id=role.id))
    db.commit()


def delete_user(db, user_id):
    """Hard delete a user."""
    user = db.query(User).filter(User.id == user_id).first()
    if not user: return False
    db.delete(user)
    db.commit()
    return True

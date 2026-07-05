"""Service layer for users and roles."""

from typing import List, Optional

from sqlalchemy.orm import Session

from app.models import Role, User


# ── Roles ─────────────────────────────────────────────────────────────────

def get_roles(db: Session) -> List[Role]:
    return db.query(Role).order_by(Role.name).all()


def get_role(db: Session, role_id: int) -> Optional[Role]:
    return db.query(Role).filter(Role.id == role_id).first()


def get_role_by_name(db: Session, name: str) -> Optional[Role]:
    return db.query(Role).filter(Role.name == name).first()


def create_role(db: Session, name: str, description: str = "") -> Role:
    role = Role(name=name, description=description)
    db.add(role)
    db.commit()
    db.refresh(role)
    return role


def delete_role(db: Session, role_id: int) -> bool:
    role = get_role(db, role_id)
    if not role:
        return False
    db.delete(role)
    db.commit()
    return True


# ── Users ─────────────────────────────────────────────────────────────────

def get_users(db: Session) -> List[dict]:
    rows = db.query(User, Role.name).outerjoin(Role, User.role_id == Role.id).order_by(User.username).all()
    result = []
    for user, role_name in rows:
        result.append({
            "id": user.id,
            "username": user.username,
            "role_id": user.role_id,
            "role_name": role_name,
            "is_active": user.is_active,
            "created_at": user.created_at,
        })
    return result


def get_user(db: Session, user_id: int) -> Optional[User]:
    return db.query(User).filter(User.id == user_id).first()


def get_user_by_username(db: Session, username: str) -> Optional[User]:
    return db.query(User).filter(User.username == username).first()


def create_user(db: Session, username: str, role_id: Optional[int] = None) -> User:
    user = User(username=username, role_id=role_id)
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def delete_user(db: Session, user_id: int) -> bool:
    user = get_user(db, user_id)
    if not user:
        return False
    db.delete(user)
    db.commit()
    return True

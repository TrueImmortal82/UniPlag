import secrets

from fastapi import Depends, HTTPException, Request
from sqlalchemy.orm import Session

from .db import SessionLocal, User


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


_sessions: dict[str, int] = {}


def create_session(user_id: int) -> str:
    token = secrets.token_urlsafe(32)
    _sessions[token] = user_id
    return token


def drop_session(token: str) -> None:
    _sessions.pop(token, None)


def current_user(request: Request, db: Session = Depends(get_db)) -> User:
    token = request.cookies.get("uniplag_session", "")
    user_id = _sessions.get(token)
    if not user_id:
        raise HTTPException(status_code=302, headers={"Location": "/login"})
    user = db.get(User, user_id)
    if not user:
        raise HTTPException(status_code=302, headers={"Location": "/login"})
    return user


def require_admin(user: User = Depends(current_user)) -> User:
    if getattr(user, "role", "student") != "admin":
        raise HTTPException(status_code=403, detail="Доступ разрешён только администраторам")
    return user


def require_teacher_or_admin(user: User = Depends(current_user)) -> User:
    if getattr(user, "role", "student") not in ("teacher", "admin"):
        raise HTTPException(status_code=403, detail="Доступ разрешён преподавателям и администраторам")
    return user


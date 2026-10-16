from passlib.context import CryptContext
from fastapi import Request
from sqlalchemy.orm import Session
from app.models import User


# Контекст для хэширования bcrypt
pwd_context = CryptContext(schemes=['bcrypt'], deprecated='auto')


def get_password_hash(password: str) -> str:
    """Хэширует пароль"""
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Проверяет пароль"""
    return pwd_context.verify(plain_password, hashed_password)


def authenticate_user(db: Session, username: str, password: str):
    """Проверяет логин/пароль. Возвращает User или None"""
    user = db.query(User).filter(User.username == username).first()

    if not user:
        return None
    if not verify_password(password, user.hashed_password):
        return None
    
    return user


# Сессии

def set_user_session(request: Request, user_id: int, username: str, email: str, is_admin: bool = False):
    """Сохраняет пользователя в сессии"""
    request.session['user_id'] = user_id
    request.session['username'] = username
    request.session['email'] = email
    request.session['is_admin'] = is_admin


def get_current_user(request: Request):
    """
    Получает текущего пользователя из сессии.
    Возвращает dict или None
    """
    user_id = request.session.get("user_id")
    username = request.session.get("username")
    email = request.session.get("email")
    is_admin = request.session.get("is_admin")

    if user_id and username:
        return {
            "id": user_id,
            "username": username,
            "email": email,
            "is_admin": is_admin
            }

    return None


def clear_user_session(request: Request):
    """Очищает сессию (выход)"""
    request.session.clear()


# Flash-сообщения

def flash(request: Request, message: str, category: str = "info"):
    """Сохраняет flash-сообщение в сессии"""
    request.session['flash'] = {
        "message": message,
        "category": category
    }


def get_flash(request: Request):
    """Забирает flash-сообщения из сессии (удаляя его)"""
    return request.session.pop('flash', None)
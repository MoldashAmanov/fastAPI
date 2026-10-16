# Общие зависимости для роутеров

from fastapi import Request, HTTPException, status
from fastapi.responses import RedirectResponse
from app.auth import get_current_user

def require_user(request: Request) -> dict:
    """
    Требует авторизованного пользователя.
    Использование: user: dict = Depends(require_user)
    """
    user = get_current_user(request)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Требуется авторизация"
        )
    return user


def require_admin(request: Request) -> dict:
    """Требует администратора"""
    user = get_current_user(request)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Требуется авторизация"
        )
    return user
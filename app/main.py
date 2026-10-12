from fastapi import FastAPI, Request, Form, Depends
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from starlette.middleware.sessions import SessionMiddleware
from sqlalchemy.orm import Session
from app.database import engine, Base, get_db
from app import models
from app.config import SECRET_KEY, APP_TITLE, APP_DESCRIPTION, APP_VERSION
from app.models import User
from app.auth import (
    get_password_hash, authenticate_user,
    set_user_session, clear_user_session,
    get_current_user, flash, get_flash)

# Создаем таблицы, если их нет
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title = "APP_TITLE",
    description = "APP_DESCRIPTION",
    version = "APP_VERSION"
)

# Middleware для сессий
app.add_middleware(SessionMiddleware, secret_key=SECRET_KEY)

# Статика (css, картинки) и шаблоны
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

# ====== Главная ======

@app.get("/", response_class=HTMLResponse)
async def root(request: Request):
    """
    Теперь возвращаем HTML-страницу
    """
    return render(request, "index.html", {
        "reviews": [],
        "stats": {"total": 0, "avg_rating": 0},
        "current_page": "home"
    })

@app.get("/about")
async def about():
    """Информация о проекте"""
    return {
        "project": "Сайт отзывов",
        "author": "А.М.Ж.",
        "version": "1.0.0"
    }

# ===== Вспомогательная функция ======

def render(request: Request, template: str, extra: dict = None) -> HTMLResponse:
    """
    Обертка для TemplateResponse.
    Автоматически добавляет user и flash в контекст
    """
    ctx = {
        "request": request,
        "user": get_current_user(request),
        "flash": get_flash(request)
    }
    if extra:
        ctx.update(extra)
    return templates.TemplateResponse(template, ctx)


# ===== Страницы авторизации ======

@app.get("/auth/login", response_class=HTMLResponse)
async def login_page(request: Request):
    return render(request, "login.html")


@app.post("/auth/login")
async def login_post(
    request: Request, 
    username: str = Form(...), 
    password: str = Form(...),
    db: Session = Depends(get_db)
    ):
    user = authenticate_user(db, username, password)
    if not user:
        return render(request, "login.html",
                      {"error": "Неверное имя пользователя или пароль"})

    set_user_session(request, user.id, user.username)
    flash(request, f"Добро пожаловать, {user.username}:", "success")
    return RedirectResponse("/", status_code=303)


@app.get("/auth/register", response_class=HTMLResponse)
async def register_page(request: Request):
    return render(request, "register.html")


@app.post("/auth/register")
async def register_post(
    request: Request, 
    username: str = Form(...), 
    email: str = Form(...),
    password: str = Form(...),
    confirm_password: str = Form(...),
    db: Session = Depends(get_db)
):
    errors = []

    # Валидация
    if len(username) < 3:
        errors.append("Имя пользователя минимум 3 символа")
    if len(password) < 6:
        errors.append("Пароль минимум 6 символов")
    if password != confirm_password:
        errors.append("Пароли не совпадают")
    if not username.replace('_', '').isalnum():
        errors.append("Имя может содержать только буквы, цифры и _")
    # Уникальность
    if db.query(User).filter(User.username == username).first():
        errors.append("Имя пользователя уже занято")
    if db.query(User).filter(User.email == email).first():
        errors.append("Email уже зарегистрирован")
    if errors:
        return render(request, "register.html", {
            "errors": errors,
            "form_data": {"username": username, "email": email}
        })

    # Создание пользователя
    user = User(
        username=username, 
        email=email,
        hashed_password=get_password_hash(password)
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    # Автоматический вход
    set_user_session(request, user.id, user.username)
    flash(request, "Регистрация прошла успешно!", "success")
    return RedirectResponse("/", status_code=303)
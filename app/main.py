from fastapi import FastAPI, Request, Form, Depends
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi import HTTPException
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
from app.schemas import ReviewCreate, ReviewUpdate
from app.crud import (
    get_review, get_reviews_paginated, get_user_reviews,
    get_reviews_stats, search_reviews,
    create_review, update_review, delete_review
)

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


@app.get("/auth/logout")
async def logout(request: Request):
    clear_user_session(request)
    return RedirectResponse("/", status_code=303)


# ===== Страницы отзывов =====

@app.get("/", response_class=HTMLResponse)
async def root(request: Request, page: int = 1, sort: str = "new",
               db: Session = Depends(get_db)):
    """Главная с пагинацией"""
    pagination = get_reviews_paginated(db, page=page, per_page=5, sort=sort)
    stats = get_reviews_stats(db)

    return render(request, "index.html", {
        "reviews": pagination['items'],
        "pagination": pagination,
        "stats": stats,
        "sort": sort,
        "current_page": "home"
    })


@app.get("/reviews/new", response_class=HTMLResponse)
async def new_review(request: Request):
    """Форма создания отзыва"""
    user = get_current_user(request)
    if not user:
        return RedirectResponse("/auth/login", status_code=303)

    return render(request, "add_review.html", {"current_page": "add_review"})


@app.post("/reviews/create")
async def create_review_route(
    request: Request,
    title: str = Form(...),
    content: str = Form(...),
    rating: int = Form(...),
    db: Session = Depends(get_db)
):
    """Создание отзывов"""
    user = get_current_user(request)
    if not user:
        return RedirectResponse("/auth/login", status_code=303)

    try:
        review_data = ReviewCreate(title=title, content=content, rating=rating)
        create_review(db, review_data, user["id"])
        flash(request, "Отзыв создан успешно", "success")
    except Exception as e:
        flash(request, f"Ошибка {e}", "danger")

    return RedirectResponse("/", status_code=303)


@app.get("/my-reviews", response_class=HTMLResponse)
async def my_reviews(request: Request, db: Session = Depends(get_db)):
    """Мои отзывы"""
    user = get_current_user(request)
    if not user:
        return RedirectResponse("/auth/login", status_code=303)

    reviews = get_user_reviews(db, user["id"])

    return render(request, "my_reviews.html", {
        "reviews": reviews,
        "current_page": "my_reviews"
    })


@app.get("/reviews/{review_id}", response_class=HTMLResponse)
async def review_detail(review_id: int, request: Request,
                        db: Session = Depends(get_db)):
    """Просмотр отзыва"""
    review = get_review(db, review_id)
    if not review:
        raise HTTPException(404, "Отзыв не найден")

    return render(request, "review_detail.html", {"review": review})


@app.get("/reviews/{review_id}/edit", response_class=HTMLResponse)
async def edit_review_page(review_id: int, request: Request,
                           db: Session = Depends(get_db)):
    """Форма редактирования"""
    user = get_current_user(request)
    if not user:
        return RedirectResponse("/auth/login", status_code=303)
    review = get_review(db, review_id)
    if not review:
        raise HTTPException(404, "Отзыв не найден")
    if review.user_id != user["id"]:
        raise HTTPException(403, "Нет прав")

    return render(request, "edit_review.html", {
        "review": review,
        "current_page": "edit_review"
    })


@app.post("/reviews/{review_id}/edit")
async def edit_review_route(
    review_id: int,
    request: Request,
    title: str = Form(...),
    content: str = Form(...),
    rating: int = Form(...),
    db: Session = Depends(get_db)
):
    """Сохрание изменений"""
    user = get_current_user(request)
    if not user:
        return RedirectResponse("/auth/login", status_code=303)

    try:
        update_data = ReviewUpdate(title=title, content=content, rating=rating)
        update_review(db, review_id, update_data, user["id"])
        flash(request, "Отзыв обновлен!", "success")
    except HTTPException as e:
        flash(request, f"Ошибка: {e.detail}", "danger")

    return RedirectResponse("/my-reviews", status_code=303)


@app.post("/reviews/{review_id}/delete")
async def delete_review_route(review_id: int, request: Request,
                              db: Session = Depends(get_db)):
    """Удаление отзыва"""
    user = get_current_user(request)
    if not user:
        return RedirectResponse("/auth/login", status_code=303)

    try:
        delete_review(db, review_id, user["id"])
        flash(request, "Отзыв удален!", "success")
    except HTTPException as e:
        flash(request, f"Ошибка {e.detail}", "danger")

    return RedirectResponse("/my-reviews", status_code=303)
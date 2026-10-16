from fastapi import APIRouter, Request, Depends, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import User
from app.auth import (
    get_password_hash, authenticate_user,
    set_user_session, clear_user_session, flash
)
from app.crud import get_user_by_username, get_user_by_email


router = APIRouter(prefix='/auth', tags=['Авторизация'])

@router.get('/login', response_class=HTMLResponse)
async def login_page(request: Request):
    return request.state.templates.TemplateResponse(
        'login.html',
        {'request': request, 'user': None, 'flash': None}
    )


@router.post('/login')
async def login(
    request: Request,
    username: str = Form(...),
    password: str = Form(...),
    db: Session = Depends(get_db)
):
    user = authenticate_user(db, username, password)

    if not user:
        return request.state.templates.TemplateResponse(
            'login.html',
            {
                'request': request,
                'user': None,
                'flash': None,
                'error': 'Неверное имя пользователя и пароль'
            }
        )

    set_user_session(
        request,
        user.id,
        user.username,
        user.email,
        user.is_admin
        )
    flash(request, f"Добро пожаловать, {user.username}!", 'success')

    return RedirectResponse('/', status_code=303)


@router.get('/register', response_class=HTMLResponse)
async def register_page(request: Request):
    return request.state.templates.TemplateResponse(
        'register.html',
        {'request': request, 'user': None, 'flash': None}
    )


@router.post('/register')
async def register(
    request: Request,
    username: str = Form(...),
    email: str = Form(...),
    password: str = Form(...),
    confirm_password: str = Form(...),
    db: Session = Depends(get_db)
):
    errors = []

    if len(username) < 3:
        errors.append('Имя пользователя минимум 3 символа')
    if len(password) < 6:
        errors.append('Пароль минимум 6 символов')
    if password != confirm_password:
        errors.append('Пароли не совпадают')
    if not username.replace('_', '').isalnum():
        errors.append('Имя может содержать только буквы, цифры и _')
    if get_user_by_username(db, username):
        errors.append('Имя пользователя уже занято')
    if get_user_by_email(db, email):
        errors.append('Email уже зарегистрирован')

    if errors:
        return request.state.templates.TemplateResponse(
            'register.html',
            {
                'request': request,
                'user': None,
                'flash': None,
                'errors': errors,
                'form_data': {'username': username, 'email': email}
            }
        )

    user = User(
        username=username,
        email=email,
        hashed_password = get_password_hash(password)
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    set_user_session(
        request,
        user.id,
        user.username,
        user.email,
        user.is_admin
        )
    flash(request, "Регистрация прошла успешно!", "success")

    return RedirectResponse('/', status_code=303)

@router.get('/logout')
async def logout(request: Request):
    clear_user_session(request)
    return RedirectResponse('/', status_code=303)
from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from starlette.middleware.sessions import SessionMiddleware
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException
from app.database import engine, Base
from app.config import SECRET_KEY, APP_TITLE, APP_DESCRIPTION, APP_VERSION
from app import models
from app.models import User
from app.routers import auth, reviews, pages

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

# middleware для добавления  шаблонов в request.state
@app.middleware('http')
async def add_template_to_request(request: Request, call_next):
    request.state.templates = templates
    response = await call_next(request)
    return response


# Обработчик HTTP-ошибок
@app.exception_handler(StarletteHTTPException)
async def http_exception_handler(request: Request, exc: StarletteHTTPException):
    return templates.TemplateResponse(
        'error.html',
        {
            'request': request,
            'user': None,
            'flash': None,
            'status_code': exc.status_code,
            'detail': exc.detail
        },
        status_code=exc.status_code
    )


# Обработчие ошибок валидации
@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc):
    return templates.TemplateResponse(
        'error.html',
        {
            'request': request,
            'user': None,
            'flash': None,
            'status_code': 422,
            'detail': 'Ошибка валидации данных'
        },
        status_code=422
    )


# Подключаем роутеры
app.include_router(auth.router)
app.include_router(reviews.router)
app.include_router(pages.router)


@app.get("/about")
async def about():
    """Информация о проекте"""
    return {
        "project": "Сайт отзывов",
        "author": "А.М.Ж.",
        "version": "1.0.0"
    }


# Запуск
if __name__ == "__main__":
    import uvicorn
    uvicorn.run('app.main:app', host='127.0.0.1', port=8000, reload=True)

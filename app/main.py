from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from app.database import engine, Base
from app import models
from app.config import APP_TITLE, APP_DESCRIPTION, APP_VERSION
from datetime import datetime


# Создаем таблицы, если их нет
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title = "APP_TITLE",
    description = "APP_DESCRIPTION",
    version = "APP_VERSION"
)

# Статика (css, картинки)
app.mount("/static", StaticFiles(directory="static"), name="static")

# Шаблоны
templates = Jinja2Templates(directory="templates")

# Декоратор @app.get("/") говорит, что эта функция обрабатывает
# GET-запросы по адресу "/"
@app.get("/", response_class=HTMLResponse)
async def root(request: Request):
    """
    Теперь возвращаем HTML-страницу
    """
    return templates.TemplateResponse(
        "index.html",
        {"request": request}
    )

@app.get("/about")
async def about():
    """Информация о проекте"""
    return {
        "project": "Сайт отзывов",
        "author": "А.М.Ж.",
        "version": "1.0.0"
    }

@app.get("/hello/{name}")
async def hello(name: str):
    return {"message": f"Hello, {name}!"}

@app.get("/time")
async def current_time():
    now = datetime.now()
    return {
        "time": now.strftime("%H:%M:%S"),
        "date": now.strftime("%Y-%m-%d")
    }

@app.get("/status")
async def status():
    return {
        "status": "online",
        "timestamp": datetime.now().isoformat()
    }


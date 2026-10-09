from fastapi import FastAPI
from app.database import engine, Base
from app.schemas import ReviewCreate
from app import models
from datetime import datetime


# Создаем таблицы, если их нет
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title = "Сайт отзывов",
    description = "Учебный проект для изучения FastAPI",
    version = "1.0.0"
)

# Декоратор @app.get("/") говорит, что эта функция обрабатывает
# GET-запросы по адресу "/"
@app.get("/")
async def root():
    """
    Корневой эндпоинт.
    Возвращаем словать, который FastAPI преобразует в JSON
    """
    return {"message": "Добро пожаловать на сайт отзывов"}

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

@app.post("/test-review")
async def test_review(review: ReviewCreate):
    """Для проверки валидации"""
    return {
        "message": "Отзыв прошел валидацию",
        "data": review.model_dump()
    }
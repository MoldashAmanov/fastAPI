"""
Конфигурация приложения.
Читает переменные окружения из .env
"""

import os
from dotenv import load_dotenv

# Загружаем переменные из .env
load_dotenv()

# Секретный ключ для сессий
SECRET_KEY = os.getenv("SECRET_KEY", "dev-secret-key-change-me")

# URL базы данных
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./reviews.db")

# Режим отладки
DEBUG = os.getenv("DEBUG", "True").lower() == 'true'

# Настройки приложения
APP_TITLE = "Сайт отзывов"
APP_DESCRIPTION = "Учебный проект по FastAPI"
APP_VERSION = "1.0.0"
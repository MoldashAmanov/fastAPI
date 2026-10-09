"""
Настройки подключения к базе данных SQLAlchemy
"""

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from app.config import DATABASE_URL

# Создаем движок SQLAlchemy
# connect_args для SQLite - чтобы можно было обращаться из разных потоков
engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False} if "sqlite" in DATABASE_URL else {}
)

# Фабрика сессий
# autocommit=False - не делать коммит автоматически
# autoflush=False - не сбрасывать данные автоматически
# bind=engine - привязать к движку
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Базовый класс для моделей
Base = declarative_base()

def get_db():
    """
    Для получения сессии БД.
    db: Session = Depends(get_db)
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
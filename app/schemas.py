from pydantic import BaseModel, Field, EmailStr, validator
from datetime import datetime
from typing import Optional

# Пользователи
class UserCreate(BaseModel):
    """Схема для регистрации"""
    username: str = Field(..., min_length=3, max_length=50)
    email: EmailStr
    password: str = Field(..., min_length=3, max_length=100)

    @validator('username')
    def username_valid(cls, v):
        """Разрешаем только буквы, цифры и подчеркивание"""
        if not v.replace('_', '').isalnum():
            raise ValueError('Тольк буквы, цифры и _')
        return v.strip()
    

class UserLogin(BaseModel):
    """Схема для входа"""
    username: str
    password: str


class UserResponse(BaseModel):
    """Схема ответа с данными пользователей"""
    id: int
    username: str
    email: str
    created_at: datetime

    class Config:
        from_attributes = True


# Отзывы
class ReviewCreate(BaseModel):
    """Схема создания отзыва"""
    title: str = Field(..., min_length=3, max_length=200, description="Заголовок отзыва")
    content: str = Field(..., min_length=10, max_length=5000, description="Содержимое отзыва")
    rating: int = Field(..., ge=1, le=5, description="Оценка от 1 до 5")

    @validator('title', 'content')
    def not_empty(cls, v):
        if not v.strip():
            raise ValueError('Поле не может быть пустым')
        return v.strip()


class ReviewUpdate(BaseModel):
    """Схема обновления отзыва (все поля опциональны)"""
    title: Optional[str] = Field(None, min_length=3, max_length=200)
    content: Optional[str] = Field(None, min_length=10, max_length=5000)
    rating: Optional[int] = Field(None, ge=1, le=5)


class ReviewResponse(BaseModel):
    """Схема ответа с данными отзыва"""
    id: int
    title: str
    content: str
    rating: int
    created_at: datetime
    updated_at: Optional[datetime]
    user_id: int
    author: UserResponse

    class Config:
        from_attributes = True

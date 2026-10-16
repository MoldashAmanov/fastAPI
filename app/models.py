"""
SQLAlchemy модели - таблицы базы данных
"""

from sqlalchemy import (
    Column, Integer, String, Text, 
    DateTime, ForeignKey, Boolean, UniqueConstraint
)
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database import Base


class User(Base):
    """Таблица пользователей"""
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, index=True, nullable=False)
    email = Column(String(100), unique=True, index=True, nullable=True)
    hashed_password = Column(String(255), nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Связь один-ко-многим с Review
    reviews = relationship(
        "Review",
        back_populates="author",
        cascade="all, delete-orphan"
    )
    comments = relationship(
        'Comment',
        back_populates='author',
        cascade='all, delete-orphan'
    )
    likes = relationship(
        'Like', back_populates='user', cascade='all, delete-orphan'
    )

class Review(Base):
    """Таблица отзывов"""
    __tablename__ = "reviews"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(200), nullable=False)
    content = Column(Text, nullable=False)
    rating = Column(Integer, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    user_id = Column(
        Integer,
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False
    )

    author = relationship("User", back_populates="reviews")
    comments = relationship(
        'Comment',
        back_populates='review',
        cascade='all, delete-orphan',
        order_by='Comment.created_at'
    )
    likes = relationship(
        'Like', back_populates='review', cascade='all, delete-orphan'
    )


class Comment(Base):
    """Таблица комментариев.
    Привязка: пользователь плюс отзыв
    """
    __tablename__ = 'comments'

    id = Column(Integer, primary_key=True, index=True)
    content = Column(Text, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    user_id = Column(
        Integer,
        ForeignKey('users.id', ondelete='CASCADE'),
        nullable=False
    )
    review_id = Column(
        Integer,
        ForeignKey('reviews.id', ondelete='CASCADE'),
        nullable=False
    )

    # Связи
    author = relationship('User', back_populates='comments')
    review = relationship('Review', back_populates='comments')


class Like(Base):
    """Таблица лайков.
    Составной уникальный ключ (user_id, review_id) - один лайк на 
    отзыв от пользователя
    """
    __tablename__ = 'likes'

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(
        Integer,
        ForeignKey('users.id', ondelete='CASCADE'),
        nullable=False
    )
    review_id = Column(
        Integer,
        ForeignKey('reviews.id', ondelete='CASCADE'),
        nullable=False
    )
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Уникальность: один пользователь - один лайк на отзыв
    __table_args__ = (
        UniqueConstraint('user_id', 'review_id', name='unique_user_review_like'),
    )

    user = relationship('User', back_populates='likes')
    review = relationship('Review', back_populates='likes')
    
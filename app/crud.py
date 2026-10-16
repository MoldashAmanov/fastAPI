from sqlalchemy.orm import Session
from sqlalchemy import desc, func, or_
from fastapi import HTTPException
from typing import Optional, List
from app.models import Review, User, Comment, Like
from app.schemas import ReviewCreate, ReviewUpdate, CommentCreate, CommentUpdate


# ===== Отзывы =====

def get_review(db: Session, review_id: int) -> Optional[Review]:
    """Получить отзыв по id"""
    return db.query(Review).filter(Review.id == review_id).first()


def get_reviews(
        db: Session,
        skip: int = 0,
        limit: int = 20,
        min_rating: Optional[int] = None,
        search: Optional[str] = None,
        sort: str = "new"
) -> List[Review]:
    """Список отзывов с фильтрами"""
    query = db.query(Review)

    if min_rating:
        query = query.filter(Review.rating >= min_rating)

    if search:
        pattern = f"%{search}%"
        query = query.filter(
            or_(
                Review.title.ilike(pattern),
                Review.content.ilike(pattern)
            )
        )

    order_map = {
        "new": desc(Review.created_at),
        "old": Review.created_at,
        "rating_high": desc(Review.rating),
        "rating_low": Review.rating,
    }
    query = query.order_by(order_map.get(sort, desc(Review.created_at)))

    return query.offset(skip).limit(limit).all()


def get_reviews_paginated(
        db: Session,
        page: int = 1,
        per_page: int = 5,
        sort: str = "new"
) -> dict:
    """Пагинированный список отзывов"""
    total = db.query(Review).count()
    total_pages = (total + per_page - 1) // per_page if total > 0 else 1
    page = max(1, min(page, total_pages))
    skip = (page - 1) * per_page

    order_map = {
        "new": desc(Review.created_at),
        "old": Review.created_at,
        "rating_high": desc(Review.rating),
        "rating_low": Review.rating,
    }
    order = order_map.get(sort, desc(Review.created_at))

    items = (db.query(Review).order_by(order).offset(skip).limit(per_page).all())

    return {
        "items": items,
        "page": page,
        "per_page": per_page,
        "total": total,
        "total_pages": total_pages,
        "has_prev": page > 1,
        "has_next": page < total_pages,
    }


def get_user_reviews(db: Session, user_id: int) -> List[Review]:
    """Все отзывы пользователя"""
    return (
        db.query(Review)
        .filter(Review.user_id == user_id)
        .order_by(desc((Review.created_at)))
        .all()
    )


def search_reviews(db: Session, query: str, limit: int = 50) -> List[Review]:
    """Поиск отзывов по тексту"""
    if not query or len(query) < 2:
        return []

    pattern = f"%{query}%"
    return (
        db.query(Review)
        .filter(or_(
            Review.title.ilike(pattern),
            Review.content.ilike(pattern)
        ))
        .order_by(desc(Review.created_at))
        .limit(limit)
        .all()
    )


def create_review(db: Session, review_data: ReviewCreate, user_id: int) -> Review:
    """Создать отзыв"""
    review = Review(
        title = review_data.title,
        content = review_data.content,
        rating = review_data.rating,
        user_id = user_id
    )
    db.add(review)
    db.commit()
    db.refresh(review)
    return review


def update_review(db: Session, review_id: int, review_data: ReviewUpdate, user_id: int) -> Review:
    """Обновить отзыва (только свой)"""
    review = get_review(db, review_id)

    if not review:
        raise HTTPException(404, "Отзыв не найден")

    if review.user_id != user_id:
        raise HTTPException(403, "Нет прав для редактирования")

    update_data = review_data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(review, field, value)

    db.commit()
    db.refresh(review)
    return review


def delete_review(db: Session, review_id: int, user_id: int) -> None:
    """Удалить свой отзыв (только свой)"""
    review = get_review(db, review_id)

    if not review:
        raise HTTPException(404, "Отзыв не найден")

    if review.user_id != user_id:
        raise HTTPException(403, "Нет прав на удаление")

    db.delete(review)
    db.commit()


def get_reviews_stats(db: Session) -> dict:
    """Статистика: всего отзывов, средний рейтинг"""
    total = db.query(Review).count()
    if total == 0:
        return {"total": 0, "avg_rating": 0}

    avg = db.query(func.avg(Review.rating)).scalar()
    return {"total": total, "avg_rating": round(float(avg), 1)}


# ===== Пользователи =====

def get_user_by_username(db: Session, username: str) -> Optional[User]:
    return db.query(User).filter(User.username == username).first()


def get_user_by_email(db: Session, email: str) -> Optional[User]:
    return db.query(User).filter(User.email == email).first()


# ===== Комментарии =====

def get_comment(db: Session, comment_id: int) -> Optional[Comment]:
    """Получить комментарий по ID"""
    return db.query(Comment).filter(Comment.id == comment_id).first()


def get_review_comments(db: Session, review_id: int) -> List[Comment]:
    """Все комментарии к отзыву (в хронологическом порядке)"""
    return (
        db.query(Comment)
        .filter(Comment.review_id == review_id)
        .order_by(Comment.created_at)
        .all()
    )


def create_comment(
        db: Session,
        review_id: int,
        comment_data: CommentCreate,
        user_id: int
) -> Comment:
    """Создать комментарий"""
    review = get_review(db, review_id)
    if not review:
        raise HTTPException(404, 'Отзыв не найден')

    comment = Comment(
        content=comment_data.content,
        user_id=user_id,
        review_id=review_id
    )
    db.add(comment)
    db.commit()
    db.refresh(comment)
    return comment


def update_comment(
        db: Session,
        comment_id: int,
        comment_data: CommentUpdate,
        user_id: int
) -> Comment:
    """Обновить комментарий"""

    comment = get_comment(db, comment_id)

    if not comment:
        raise HTTPException(404, 'Комментарий не найден')

    if comment.user_id != user_id:
        raise HTTPException(403, 'Нет прав на редактирование')

    update_data = comment_data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(comment, field, value)

    db.commit()
    db.refresh(comment)
    return comment


def delete_comment(
        db: Session,
        comment_id: int,
        user_id: int
) -> None:
    """Удалить комментарий (только свой)"""

    comment = get_comment(db, comment_id)

    if not comment:
        raise HTTPException(404, 'Комментарий не найден')

    if comment.user_id != user_id:
        raise HTTPException(403, 'Нет прав на удаление')

    db.delete(comment)
    db.commit()


def count_review_comments(db: Session, review_id: int) -> int:
    """Количество комментариев к отзыву"""
    return db.query(Comment).filter(Comment.review_id==review_id).count()


# ===== Лайки =====

def has_user_liked(db: Session, user_id: int, review_id: int) -> bool:
    """Проверка: лайкнул ли пользователь отзыв"""
    return db.query(Like).filter(
        Like.user_id == user_id,
        Like.review_id == review_id
    ).first() is not None


def count_review_likes(db: Session, review_id: int) -> int:
    """Количество лайков у отзыва"""
    return db.query(Like).filter(Like.review_id == review_id).count()


def toggle_like(db: Session, user_id: int, review_id: int) -> dict:
    """
    Переключить лайк:
    - если лайка нет - ставим
    - если есть - убираем
    Возвращает: {'liked': bool, 'count': int}
    """
    # Проверка: существует ли отзыв
    review = get_review(db, review_id)
    if not review:
        raise HTTPException(404, 'Отзыв не найден')

    existing = db.query(Like).filter(
        Like.user_id == user_id,
        Like.review_id == review_id
    ).first()

    if existing:
        db.delete(existing)
        liked = False
    else:
        new_like = Like(user_id=user_id, review_id=review_id)
        db.add(new_like)
        liked = True

    db.commit()
    count = count_review_likes(db, review_id)
    return {'liked': liked, 'count': count}
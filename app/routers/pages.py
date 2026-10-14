from fastapi import APIRouter, Request, Depends, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlalchemy.orm import Session
from app.database import get_db
from app.auth import get_current_user, get_flash
from app.crud import (
    get_review, get_reviews_paginated, get_user_reviews,
    get_reviews_stats, search_reviews
)


router = APIRouter(tags=['Страницы'])


def _ctx(request: Request, extra: dict = None) -> dict:
    """
    Формирует базовый контекст для шаблонов
    Добавляет user и flash
    """
    ctx = {
        'request': request,
        'user': get_current_user(request),
        'flash': get_flash(request)
    }

    if extra:
        ctx.update(extra)
    return ctx


@router.get('/', response_class=HTMLResponse)
async def home(request: Request, page: int = 1, sort: str = 'new',
               db: Session = Depends(get_db)):
    pagination = get_reviews_paginated(db, page=page, per_page=5, sort=sort)
    stats = get_reviews_stats(db)

    return request.state.templates.TemplateResponse(
        'index.html',
        _ctx(request, {
            'reviews': pagination['items'],
            'pagination': pagination,
            'stats': stats,
            'sort': sort,
            'current_page': 'home'
        })
    )


@router.get('/search', response_class=HTMLResponse)
async def search_page(request: Request, q: str = '',
                      db: Session = Depends(get_db)):
    reviews = search_reviews(db, q) if q else []

    return request.state.templates.TemplateResponse(
        'search.html',
        _ctx(request, {
            'reviews': reviews,
            'query': q,
            'current_page': 'search'
        })
    )


@router.get('/my-reviews', response_class=HTMLResponse)
async def my_reviews(request: Request, db: Session = Depends(get_db)):
    user = get_current_user(request)
    if not user:
        return RedirectResponse('/auth/login', status_code=303)

    reviews = get_user_reviews(db, user['id'])

    return request.state.templates.TemplateResponse(
        'my_reviews.html',
        _ctx(request, {
            'reviews': reviews,
            'current_page': 'my-reviews'
        })
    )


@router.get('/reviews/new', response_class=HTMLResponse)
async def new_review(request: Request):
    user = get_current_user(request)
    if not user:
        return RedirectResponse('/auth/login', status_code=303)

    return request.state.templates.TemplateResponse(
        'add_review.html',
        _ctx(request, {'current_page': 'add_review'})
    )


@router.get('/reviews/{review_id}', response_class=HTMLResponse)
async def review_detail(review_id: int, request: Request,
                        db: Session = Depends(get_db)):
    review = get_review(db, review_id)
    if not review:
        raise HTTPException(404, "Отзыв не найден")

    return request.state.templates.TemplateResponse(
        'review_detail.html',
        _ctx(request, {'review': review})
    )


@router.get('/reviews/{review_id}/edit', response_class=HTMLResponse)
async def edit_review_page(review_id: int, request: Request,
                           db: Session = Depends(get_db)):
    user = get_current_user(request)
    if not user:
        return RedirectResponse('/auth/login', status_code=303)

    review = get_review(db, review_id)
    if not review:
        raise HTTPException(404, 'Отзыв не найден')
    if review.user_id != user['id']:
        raise HTTPException(403, 'Нет прав')

    return request.state.templates.TemplateResponse(
        'edit_review.html',
        _ctx(request, {
            'review': review,
            'current_page': 'edit_review'
        })
    )

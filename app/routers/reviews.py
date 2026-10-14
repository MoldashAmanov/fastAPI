from fastapi import APIRouter, Request, Depends, Form, HTTPException
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session
from app.database import get_db
from app.auth import get_current_user, flash
from app.schemas import ReviewUpdate, ReviewCreate
from app.crud import create_review, update_review, delete_review

router = APIRouter(prefix='/reviews', tags=['Действия'])


@router.post('/create')
async def create(
    request: Request,
    title: str = Form(...),
    content: str = Form(...),
    rating: int = Form(...),
    db: Session = Depends(get_db)
):
    user = get_current_user(request)
    if not user:
        return RedirectResponse('/auth/login', status_code=303)

    try:
        review_data = ReviewCreate(title=title, content=content, rating=rating)
        create_review(db, review_data, user['id'])
        flash(request, 'Отзыв успешно создан!', 'success')
        return RedirectResponse('/', status_code=303)
    except Exception as e:
        flash(request, f"Ошибка {e}", "danger")
        return RedirectResponse('/reviews/new', status_code=303)


@router.post('/{review_id}/edit')
async def edit(
    review_id: int,
    request: Request,
    title: str = Form(...),
    content: str = Form(...),
    rating: int = Form(...),
    db: Session = Depends(get_db)
):
    user = get_current_user(request)
    if not user:
        return RedirectResponse('/auth/login', status_code=303)

    try:
        review_data = ReviewUpdate(title=title, content=content, rating=rating)
        update_review(db, review_id, review_data, user['id'])
        flash(request, 'Отзыв обновлен!', 'success')
    except HTTPException as e:
        flash(request, f'Ошибка {e.detail}', 'danger')

    return RedirectResponse('/my-reviews', status_code=303)


@router.post('/{review_id}/delete')
async def delete(
    review_id: int,
    request: Request,
    db: Session = Depends(get_db)
):
    user = get_current_user(request)
    if not user:
        return RedirectResponse('/auth/login', status_code=303)

    try:
        delete_review(db, review_id, user['id'])
        flash(request, 'Отзыв удален!', 'success')
    except HTTPException as e:
        flash(request, f'Ошибка {e.detail}', 'danger')

    return RedirectResponse('/my-reviews', status_code=303)
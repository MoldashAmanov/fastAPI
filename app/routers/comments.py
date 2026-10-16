from fastapi import APIRouter, Request, Depends, Form, HTTPException
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session
from app.database import get_db
from app.auth import get_current_user, flash
from app.schemas import CommentCreate, CommentUpdate
from app.crud import create_comment, update_comment, delete_comment, get_comment

router = APIRouter(prefix='/comments', tags=['Комментарии'])


@router.post('/review/{review_id}/create')
async def create(
    review_id: int,
    request: Request,
    content: str = Form(...),
    db: Session = Depends(get_db)
):
    """Создать комментарий к отзыву"""
    user = get_current_user(request)
    if not user:
        return RedirectResponse('/auth/login', status_code=303)

    try:
        comment_data = CommentCreate(content=content)
        create_comment(db, review_id, comment_data, user['id'])
        flash(request, 'Комментарий добавлен', 'success')
    except HTTPException as e:
        flash(request, f'Ошибка {e.detail}', 'danger')
    except Exception as e:
        flash(request, f'Ошибка {e}', 'danger')

    return RedirectResponse(f'/reviews/{review_id}', status_code=303)


@router.post('/{comment_id}/delete')
async def delete(
    comment_id: int,
    request: Request,
    db: Session = Depends(get_db)
):
    """Удалить комментарий"""
    user = get_current_user(request)
    if not user:
        return RedirectResponse('/auth/login', status_code=303)

    # Запоминаем review_id для редиректа
    comment = get_comment(db, comment_id)
    review_id = comment.review_id if comment else None

    try:
        delete_comment(db, comment_id, user['id'])
        flash(request, 'Комментарий удален!', 'success')
    except HTTPException as e:
        flash(request, f'Ошибка {e.detail}', 'danger')

    if review_id:
        return RedirectResponse(f'/reviews/{review_id}', status_code=303)


from fastapi import APIRouter, Request, Depends
from fastapi.responses import RedirectResponse, JSONResponse
from sqlalchemy.orm import Session
from app.database import get_db
from app.auth import get_current_user
from app.crud import toggle_like


router = APIRouter(prefix='/likes', tags=['Лайки'])

@router.post('/review/{review_id}/toggle')
async def toggle(
    review_id: int,
    request: Request,
    db: Session = Depends(get_db)
):
    """
    Переключить лайк.
    Возвращает JSON: {'liked': true, 'count': 5}
    """
    user = get_current_user(request)
    if not user:
        return JSONResponse(
            {'error': 'Требуется авторизация'},
            status_code=401
        )

    try:
        result = toggle_like(db, user['id'], review_id)
        return JSONResponse(result)
    except Exception as e:
        return JSONResponse({'error': str(e)}, status_code=400)
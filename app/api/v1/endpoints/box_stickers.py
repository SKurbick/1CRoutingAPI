from datetime import datetime

from fastapi import APIRouter, HTTPException, status, Depends
from fastapi.responses import StreamingResponse

from app.dependencies import get_box_sticker_service
from app.models.box_stickers import BoxDataRequest
from app.service.box_stickers import BoxStickerService


router = APIRouter(prefix="/stickers", tags=["Сткеры для коробов"])


@router.post(
        "/generate",
        status_code=status.HTTP_200_OK,
        description="""
    **Генерирует PDF со стикерами для коробов.**

    Возвращает: PDF файл для скачивания
"""
)
async def generate_stickers(
    data: BoxDataRequest,
    service: BoxStickerService = Depends(get_box_sticker_service)
):
    try:
        result = await service.generate_stickers(data)
        return StreamingResponse(
            iter([result]),
            media_type="application/pdf",
            headers={
                "Content-Disposition": 
                f"attachment; filename=stickers_{data.article}_{datetime.now()}.pdf"
            }
        )
    except Exception as e:
        print(f"Ошибка во время генерации стикеров: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Internal server error"
        )

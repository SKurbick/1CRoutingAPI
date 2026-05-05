from datetime import datetime
from typing import Annotated

from fastapi import APIRouter, HTTPException, status, Depends, Query, Path
from fastapi.responses import StreamingResponse

from app.dependencies import get_box_sticker_service
from app.dependencies.box_stickers import get_box_sticker_service_1, get_sticker_generation_service, get_sticker_template_save_service
from app.models.box_stickers import BoxDataRequest, BoxStickerTemplate, BoxStickerTemplateShort, BoxStickerTemplateView, BoxStickerTemplateViewShort, StickerGenerationTaskResult
from app.service.box_stickers import BoxStickerService, StickerTemplateBuilderService
from app.service.sticker_generation_service import StickerGenerationService
from app.service.sticker_template_save import StickerTemplateSaveService
from app.service.translate_manager import translation_manager


router = APIRouter(prefix="/stickers", tags=["Стикеры для коробов"])


@router.post(
        "/generate",
        status_code=status.HTTP_200_OK,
        description="""
    **Сгенерировать PDF со стикерами для коробов.**

    Возвращает: PDF файл для скачивания
""",
include_in_schema=False
)
async def generate_stickers(
    data: BoxDataRequest,
    service: Annotated[BoxStickerService, Depends(get_box_sticker_service)],
) -> StreamingResponse:
    """Сгенерировать PDF со стикерами для коробов."""
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


@router.get(
        "/templates/{article}",
        status_code=status.HTTP_200_OK,
        description="""
    **Получить шаблон стикера по артикулу.**
""",
include_in_schema=False
)
async def get_sticker_template(
    article: Annotated[str, Path(..., description="Артикул товара для поиска шаблона")],
    service: Annotated[BoxStickerService, Depends(get_box_sticker_service)],
) -> BoxStickerTemplate:
    """Получить шаблон стикера по артикулу."""
    return await service.get_template(article)

@router.get(
        "/NEWtemplates/{product_id}",
        status_code=status.HTTP_200_OK,
        description="""
    **Получить шаблон стикера по артикулу.**
"""
)
async def get_sticker_template_(
    product_id: Annotated[str, Path(..., description="Артикул товара для поиска шаблона")],
    service: Annotated[StickerTemplateBuilderService, Depends(get_box_sticker_service_1)],
) -> BoxStickerTemplateView:
    """Получить шаблон транспортного стикера по артикулу."""
    # return await service.get_box_sticker_template(product_id)
    try:
        return await service.get_box_sticker_template(product_id)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )

@router.post(
    "/NEWtemplates/save",
    status_code=status.HTTP_200_OK,
    description="Сохранить пользовательские данные и локализации шаблона",
)
async def save_sticker_template_new(
    data: BoxStickerTemplateView,
    service: Annotated[StickerTemplateSaveService, Depends(get_sticker_template_save_service)],
) -> BoxStickerTemplateView:
    return await service.save_box_sticker_template(data)


@router.post("/NEWgeneration_tasks")
async def create_or_get_generation_task(
    template_data: BoxStickerTemplateView,
    user_id: int, #TODO: временное решение для тестирования
    # user_id: int = Depends(get_current_user_id), #TODO: как получит user_id?
    service: StickerGenerationService = Depends(get_sticker_generation_service),
) -> StickerGenerationTaskResult:
    try:
        return await service.create_or_get_box_generation_task(
            user_id=user_id,
            template_data=template_data,
        )
    except ValueError as e:
        raise HTTPException(status_code=409, detail=str(e))
    
@router.get(
        "/NEWtemplates",
        status_code=status.HTTP_200_OK,
        description="""
    **Получить список существующих шаблонов для стикеров.**
"""
)
async def get_list_templates(
    service: Annotated[StickerTemplateBuilderService, Depends(get_box_sticker_service_1)],
) -> list[BoxStickerTemplateViewShort]:
    """Получить список существующих шаблонов для стикеров."""
    return await service.get_list_templates()


@router.get(
        "/templates",
        status_code=status.HTTP_200_OK,
        description="""
    **Получить список существующих шаблонов для стикеров.**
""",
include_in_schema=False
)
async def get_list_templates(
    service: Annotated[BoxStickerService, Depends(get_box_sticker_service)],
) -> list[BoxStickerTemplateShort]:
    """Получить список существующих шаблонов для стикеров."""
    return await service.get_list_templates()


@router.get(
        "/color/translate",
        status_code=status.HTTP_200_OK,
        description="""
    **Получить перевод цвета или его транслитерацию.**
""",
include_in_schema=False
)
async def translate_color(
    color: Annotated[str, Query(..., min_length=3, description="Цвет на русском языке.")]
) -> str:
    """Получить перевод цвета или его транслитерацию."""
    return translation_manager.translate_color(color)


@router.get(
        "/country/translate",
        status_code=status.HTTP_200_OK,
        description="""
    **Получить перевод названия страны или транслитерацию названия.**
""",
include_in_schema=False
)
async def translate_country(
    country: Annotated[str, Query(..., min_length=3, description="Страна производства на русском языке.")]
) -> str:
    """Получить перевод названия страны или транслитерацию названия."""
    return translation_manager.translate_country(country)


@router.get(
        "/title/transliterate",
        status_code=status.HTTP_200_OK,
        description="""
    **Сделать транслитерацию названия на русском латиницей.**
""",
include_in_schema=False
)
async def transliterate_title(
    title: Annotated[str, Query(..., min_length=3, description="Название товара на русском языке.")]
) -> str:
    """Сделать транслитерацию названия на русском латиницей."""
    return translation_manager.transliterate_string(title)


@router.get(
        "/colors",
        status_code=status.HTTP_200_OK,
        description="""
    **Получить список цветов.**
""",
include_in_schema=False
)
async def get_colors() -> list[str]:
    """Получить список цветов."""
    return [color.capitalize() for  color in sorted(translation_manager.colors.keys())]


@router.get(
        "/countries",
        status_code=status.HTTP_200_OK,
        description="""
    **Получить список стран.**
""",
include_in_schema=False
)
async def get_countries() -> list[str]:
    """Получить список стран."""
    return sorted(translation_manager.countries.keys())

from datetime import datetime
from typing import Annotated

from fastapi import APIRouter, HTTPException, status, Depends, Query, Path
from fastapi.responses import StreamingResponse

from app.dependencies import get_box_sticker_service
from app.dependencies.box_stickers import get_box_sticker_service_1, get_sticker_generation_service, get_sticker_template_save_service
from app.exceptions.stickers import TotalTaskLimit
from app.models.box_stickers import (
    BoxDataRequest, 
    BoxStickerTemplate, 
    BoxStickerTemplateShort, 
    BoxStickerTemplateView, 
    BoxStickerTemplateViewShort,
    IndividualStickerTemplateView,
    StickerGenerationTaskResultResponse,
)
from app.service.box_stickers import BoxStickerService, StickerTemplateBuilderService
from app.service.sticker_generation_service import StickerGenerationService
from app.service.sticker_template_save import StickerTemplateSaveService
from app.service.translate_manager import translation_manager


router = APIRouter(prefix="/stickers", tags=["Стикеры для коробов"])

@router.get(
        "/templates/{product_id}",
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

# @router.post(
#     "/templates/save",
#     status_code=status.HTTP_200_OK,
#     description="**Сохранить пользовательские данные и локализации шаблона**",
# )
# async def save_sticker_template_new(
#     data: BoxStickerTemplateView,
#     service: Annotated[StickerTemplateSaveService, Depends(get_sticker_template_save_service)],
# ) -> BoxStickerTemplateView:
#     return await service.save_box_sticker_template(data)


@router.post("/sticker_generation",
             status_code=status.HTTP_200_OK,
            description="**Инициировать создание стикера**")
async def create_or_get_generation_task(
    template_data: BoxStickerTemplateView,
    # user_id: int, #TODO: временное решение для тестирования
    # user_id: int = Depends(get_current_user_id), #TODO: как получит user_id?
    service: StickerGenerationService = Depends(get_sticker_generation_service),
) -> StickerGenerationTaskResultResponse:
    try:
        return await service.create_or_get_box_generation_task(
            # user_id=user_id,
            template_data=template_data,
        )
        
    except ValueError as e:
        raise HTTPException(status_code=409, detail=str(e))
    except TotalTaskLimit as e:
        raise HTTPException(status_code=429, detail=str(e))

@router.post("/sticker_generation_TEST",
             status_code=status.HTTP_200_OK,
            description="**Инициировать создание стикера**")
async def create_or_get_generation_task(
    template_data: IndividualStickerTemplateView,
    # user_id: int, #TODO: временное решение для тестирования
    # user_id: int = Depends(get_current_user_id), #TODO: как получит user_id?
    service: StickerGenerationService = Depends(get_sticker_generation_service),
) -> StickerGenerationTaskResultResponse:
    print("направил POST запрос с данными:")
    print(template_data)
    try:
        return await service.create_or_get_individual_task(
            # user_id=user_id,
            template_data=template_data,
        )
    except ValueError as e:
        raise HTTPException(status_code=409, detail=str(e))
    except TotalTaskLimit as e:
        raise HTTPException(status_code=429, detail=str(e))    
IndividualStickerTemplateView    

    
@router.get(
        "/templates",
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
        "/tasks",
        status_code=status.HTTP_200_OK,
        description="""
    **Получить список задач на генерацию стикеров.**
"""
)
async def get_generation_tasks(
    service: Annotated[StickerGenerationService, Depends(get_sticker_generation_service)]
) -> list[StickerGenerationTaskResultResponse]:
    """
    Получить список задач на генерацию файлов.
    """
    result = await service.get_sticker_tasks()
    return result

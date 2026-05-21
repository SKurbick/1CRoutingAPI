from datetime import datetime
from typing import Annotated, Union

from fastapi import APIRouter, Body, HTTPException, status, Depends, Query, Path
from fastapi import APIRouter, HTTPException, status, Depends, Path
from fastapi.responses import StreamingResponse
from sse_starlette import EventSourceResponse
from app.dependencies.box_stickers import get_box_sticker_service, get_importer_service, get_sticker_generation_service, get_sticker_template_save_service
from app.exceptions.stickers import TotalTaskLimit
from app.models.box_stickers import (
    BoxStickerTemplateView,
    BoxStickerTemplateViewShort,
    ImporterView,
    IndividualStickerTemplateView,
    ManufacturerView,
    StickerGenerationTaskResultResponse,
    StickerGenerationTaskInfo,
)
from app.service.box_stickers import StickerTemplateBuilderService
from app.service.importers import ImporterService
from app.service.sticker_generation_service import StickerGenerationService
# from app.service.translate_manager import translation_manager
from app.service.sticker_tasks_notification import StickerTasksNotificationsService
from app.dependencies.sticker_tasks_notification import get_sticker_tasks_notification_service
from app.file_storage import StorageFileNotFoundError

router = APIRouter(prefix="/stickers", tags=["Стикеры для коробов"])


@router.get(
    "/transport_templates/{product_id}",  # TODO: templates/transport/{product_id}
    status_code=status.HTTP_200_OK,
    description="""
    **Получить шаблон стикера по артикулу.**
""")
async def get_transport_sticker_template_(
    product_id: Annotated[
        str, Path(..., description="Артикул товара для поиска шаблона")],
    service: Annotated[StickerTemplateBuilderService,
                       Depends(get_box_sticker_service)],
) -> BoxStickerTemplateView:
    """Получить шаблон транспортного стикера по артикулу."""
    try:
        return await service.get_box_sticker_template(product_id)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail=str(e))


@router.get(
    "/individual_templates/{product_id}",  # TODO: templates/individual/{product_id}
    status_code=status.HTTP_200_OK,
    description="""
    **Получить шаблон стикера по артикулу.**
""")
async def get_individual_sticker_template_(
    product_id: Annotated[
        str, Path(..., description="Артикул товара для поиска шаблона")],
    service: Annotated[StickerTemplateBuilderService,
                       Depends(get_box_sticker_service)],
) -> IndividualStickerTemplateView:
    """Получить шаблон индивидуального стикера по артикулу."""
    # return await service.get_box_sticker_template(product_id)
    try:
        return await service.get_unit_sticker_template(product_id)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail=str(e))


@router.post(
    "/sticker_generation_transport",  # TODO: sticker_generation/transport
    status_code=status.HTTP_200_OK,
    description="**Инициировать создание стикера**")
async def create_or_get_generation_task(
    template_data: BoxStickerTemplateView,
    # user_id: int, #TODO: временное решение до авторизации пользователей
    service: Annotated[StickerGenerationService,
                       Depends(get_sticker_generation_service)],
) -> StickerGenerationTaskResultResponse:
    try:
        print("принял форму для BoxStickerTemplateView")
        return await service.create_or_get_box_generation_task(
            template_data=template_data)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT,
                            detail=str(e))
    except TotalTaskLimit as e:
        raise HTTPException(status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                            detail=str(e))


@router.post(
    "/sticker_generation_individual",  # TODO: sticker_generation/individual
    status_code=status.HTTP_200_OK,
    description="**Инициировать создание стикера**")
async def create_or_get_generation_task(
    template_data: IndividualStickerTemplateView,
    # user_id: int, #TODO: временное решение до авторизации пользователей
    service: Annotated[StickerGenerationService,
                       Depends(get_sticker_generation_service)],
) -> StickerGenerationTaskResultResponse:
    #TODO: Логирование
    try:
        return await service.create_or_get_individual_task(
            # user_id=user_id,
            template_data=template_data, )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT,
                            detail=str(e))
    except TotalTaskLimit as e:
        raise HTTPException(status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                            detail=str(e))


@router.get("/templates",
            status_code=status.HTTP_200_OK,
            description="""
    **Получить список существующих шаблонов для стикеров.**
""")
async def get_list_templates(
    service: Annotated[StickerTemplateBuilderService,
                       Depends(get_box_sticker_service)],
) -> list[BoxStickerTemplateViewShort]:
    """Получить список существующих шаблонов для стикеров."""
    return await service.get_list_templates()


@router.get("/manufacturers",
            status_code=status.HTTP_200_OK,
            description="""
    **Получить список существующих производителей для стикеров.**
""")
async def get_list_manufacturers(
    service: Annotated[StickerTemplateBuilderService,
                       Depends(get_box_sticker_service)],
) -> list[ManufacturerView]:
    """Получить список существующих шаблонов для стикеров."""
    return await service.get_list_manufacturers()

@router.get("/importers",
            status_code=status.HTTP_200_OK,
            description="""
    **Получить список существующих импортеров для стикеров.**
""")
async def get_list_importers(
    service: Annotated[ImporterService,
                       Depends(get_importer_service)],
) -> list[ImporterView]:
    """Получить список существующих шаблонов для стикеров."""
    return await service.get_list_importers()


@router.get("/tasks",
            status_code=status.HTTP_200_OK,
            description="""
    **Получить список задач на генерацию стикеров.**
""")
async def get_generation_tasks(
    service: Annotated[StickerGenerationService,
                       Depends(get_sticker_generation_service)]
) -> list[StickerGenerationTaskInfo]:
    """
    Получить список задач на генерацию файлов.
    """
    result = await service.get_sticker_tasks()
    return result


@router.get("/tasks/{task_id}/download",
            status_code=status.HTTP_200_OK,
            description="""
    **Получить ссылку для скачивания файла, если задача по генерации успешно выполнена.**
""")
async def get_file_url_for_download(
    task_id: Annotated[int, Path(description="ID задачи на генерацию файла.")],
    service: Annotated[StickerGenerationService, Depends(get_sticker_generation_service)]
) -> str:
    """
    Получить ссылку для скачивания файла, если задача по генерации успешно выполнена.
    """
    try:
        return await service.get_file_url_by_task_id(task_id=task_id)
    except StorageFileNotFoundError:
        raise HTTPException(status_code=404, detail={"task_id": task_id, "message": "Файл не найден. Проверьте статус задачи или корректность task_id."})


@router.get("/tasks/events",
            description="""
    **Устанавливает SSE-соединение с клиентом и возвращает уведомления по задачам генерации файлов.**

    Возвращает media_type: text/event-stream.
""")
async def stream_tasks_notifications(
    service: Annotated[StickerTasksNotificationsService,
                       Depends(get_sticker_tasks_notification_service)],
) -> EventSourceResponse:
    """
    Устанавливает SSE-соединение с клиентом и возвращает уведомления по задачам генерации файлов.
    """

    return EventSourceResponse(service.listen())


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

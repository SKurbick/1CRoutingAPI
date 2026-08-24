from typing import Annotated
from fastapi import APIRouter, HTTPException, status, Depends, Path
from sse_starlette import EventSourceResponse

from app.dependencies.box_stickers import (get_box_sticker_service,
                                           get_importer_service,
                                           get_sticker_generation_service,
                                           get_sticker_template_save_service)
from app.exceptions.stickers import TotalTaskLimit
from app.models.box_stickers import (
    BoxStickerTemplateView,
    BoxStickerTemplateViewRequest,
    StickerTemplateViewShort,
    ImporterView,
    IndividualStickerTemplateView,
    ManufacturerView,
    StickerGenerationTaskResultResponse,
    StickerGenerationTaskInfo,
)
from app.service.box_stickers import StickerTemplateBuilderService
from app.service.importers import ImporterService
from app.service.sticker_generation_service import StickerGenerationService

from app.service.sticker_tasks_notification import StickerTasksNotificationsService
from app.dependencies.sticker_tasks_notification import get_sticker_tasks_notification_service
from app.file_storage import StorageFileNotFoundError

router = APIRouter(prefix="/stickers", tags=["Стикеры для коробов"])


@router.get("/transport/template/{product_id}",
            status_code=status.HTTP_200_OK,
            description="""
    **Получить шаблон транспортного стикера по артикулу.**
""")
async def get_transport_sticker_template_(
    product_id: Annotated[
        str, Path(..., description="Артикул товара для поиска шаблона")
        ],
        service: Annotated[
            StickerTemplateBuilderService,
            Depends(get_box_sticker_service)
            ],
) -> BoxStickerTemplateView:
    """Получить шаблон транспортного стикера по артикулу."""
    try:
        return await service.get_box_sticker_template(product_id)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail=str(e))


@router.get("/individual/template/{product_id}",
            status_code=status.HTTP_200_OK,
            description="""
    **Получить шаблон индивидуального стикера по артикулу.**
""")
async def get_individual_sticker_template_(
    product_id: Annotated[
        str, Path(..., description="Артикул товара для поиска шаблона")
        ],
        service: Annotated[
            StickerTemplateBuilderService,
            Depends(get_box_sticker_service)
                       ],
) -> IndividualStickerTemplateView:
    """Получить шаблон индивидуального стикера по артикулу."""
    try:
        return await service.get_unit_sticker_template(product_id)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                            detail=str(e))


@router.post(
    "/transport/generate",
    status_code=status.HTTP_200_OK,
    description="**Инициировать создание стикера**")
async def create_or_get_transport_generation_task(
    template_data: BoxStickerTemplateViewRequest,
    service: Annotated[
        StickerGenerationService,
        Depends(get_sticker_generation_service)
        ],
) -> StickerGenerationTaskResultResponse:
    """Отправляет форму для генерации странспортного стикера"""
    try:
        print("Принял форму для транспортного стикера")
        return await service.create_or_get_box_generation_task(
            template_data=template_data
            ) #передавать user_id после добавления авторизации
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                            detail=str(e))
    except TotalTaskLimit as e:
        raise HTTPException(status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                            detail=str(e))


@router.post(
    "/individual/generate",
    status_code=status.HTTP_200_OK,
    description="**Инициировать создание стикера**")
async def create_or_get_individual_generation_task(
    template_data: IndividualStickerTemplateView,
    service: Annotated[
        StickerGenerationService,
        Depends(get_sticker_generation_service)
        ],
) -> StickerGenerationTaskResultResponse:
    """Отправляет форму для генерации индивидуального стикера"""
    try:
        print("Принял форму для индивидуального стикера")
        return await service.create_or_get_individual_task(
            template_data=template_data
            ) #передавать user_id после добавления авторизации
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
    service: Annotated[
        StickerTemplateBuilderService,
        Depends(get_box_sticker_service)
        ],
) -> list[StickerTemplateViewShort]:
    """Получить список существующих шаблонов для стикеров."""
    return await service.get_list_templates()


@router.get("/manufacturers",
            status_code=status.HTTP_200_OK,
            description="""
    **Получить список существующих производителей для стикеров.**
""")
async def get_list_manufacturers(
    service: Annotated[
        StickerTemplateBuilderService,
        Depends(get_box_sticker_service)
        ],
) -> list[ManufacturerView]:
    """Получить список существующих производителей для стикеров."""
    return await service.get_list_manufacturers()


@router.get("/importers",
            status_code=status.HTTP_200_OK,
            description="""
    **Получить список существующих импортеров для стикеров.**
""")
async def get_list_importers(
    service: Annotated[
        ImporterService,
        Depends(get_importer_service)
        ],
) -> list[ImporterView]:
    """Получить список существующих импортеров для стикеров."""
    return await service.get_list_importers()


@router.get("/tasks",
            status_code=status.HTTP_200_OK,
            description="""
    **Получить список задач на генерацию стикеров.**
""")
async def get_generation_tasks(
    service: Annotated[
        StickerGenerationService,
        Depends(get_sticker_generation_service)
        ]
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
        raise HTTPException(
            status_code=404,
            detail={
                "task_id":
                task_id,
                "message":
                "Файл не найден. Проверьте статус задачи или корректность task_id."
            })


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

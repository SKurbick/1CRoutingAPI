import logging
from app.database.repositories.sticker_generation_tasks import StickerGenerationTasksRepository
from app.exceptions.stickers import TotalTaskLimit
from app.file_storage.base.interface import IFileStorage
from app.models.box_stickers import (
    BoxStickerTemplateView,
    IndividualStickerTemplateView,
    StickerGenerationTaskResultResponse,
    StickerType,
    GenerationStatus,
    StickerGenerationTaskInfo,
    StickerGenerationTaskEvent,
    StickerGenerationTaskNotice,
)
from app.service.localisation import LocalisationService
from app.service.sticker_generation_publisher import StickerGenerationPublisher
from app.service.sticker_template_hash import StickerTemplateHashService
from app.service.sticker_user_data import StickerUserDataService
from app.service.sticker_tasks_notification import StickerTasksNotificationsService

logger = logging.getLogger(__name__)


class StickerGenerationService:

    def __init__(
        self,
        generation_tasks_repo: StickerGenerationTasksRepository,
        user_data_service: StickerUserDataService,
        localisation_service: LocalisationService,
        publisher: StickerGenerationPublisher,
        file_storage: IFileStorage,
        task_notification_service: StickerTasksNotificationsService,
    ):
        self.generation_tasks_repo = generation_tasks_repo
        self.user_data_service = user_data_service
        self.localisation_service = localisation_service
        self.publisher = publisher
        self.file_storage = file_storage
        self.task_notification_service = task_notification_service

    async def create_or_get_box_generation_task(
        self,
        # user_id: int, #TODO: пока нет авторизации польщователей
        template_data: BoxStickerTemplateView,
    ) -> StickerGenerationTaskResultResponse:
        await self.user_data_service.save_box_sticker_user_data(template_data)
        await self.localisation_service.save_localisations(template_data)
        hash_payload = {
            "sticker_type":
            StickerType.TRANSPORT.value,
            "product_id":
            template_data.product_id,
            "name":
            template_data.name,
            "name_en":
            template_data.name_en,
            "color":
            template_data.color,
            "color_en":
            template_data.color_en,
            "gross_weight":
            template_data.gross_weight,
            "net_weight":
            template_data.net_weight,
            "box_size":
            template_data.box_size.model_dump()
            if template_data.box_size else None,
            "items_per_box":
            template_data.items_per_box,
            "total_boxes":
            template_data.total_boxes,
            "produced_in":
            template_data.produced_in,
            "produced_in_en":
            template_data.produced_in_en,
            "proforma_number":
            template_data.proforma_number,
            "certification_type":
            template_data.certification_type.value,
            "limit":
            template_data.limit,
            "offset":
            template_data.offset
        }
        template_hash = StickerTemplateHashService.calculate(hash_payload)
        #проверяем существования таски по составному ключу (product_id, sticker_type, template_hash)
        existing_task = await self.generation_tasks_repo.get_by_unique_key(
            product_id=template_data.product_id,
            sticker_type=StickerType.TRANSPORT,
            template_hash=template_hash,
        )
        #TODO: логирование
        if existing_task:
            #TODO: ограничивать таски на каждого пользователя
            print("нашел готовую таску")
            #TODO: логирование
            response = response = StickerGenerationTaskResultResponse(
                task_id=existing_task.task_id,
                product_id=template_data.product_id,
                generation_status=existing_task.generation_status,
                error_message=existing_task.error_message,
                document_url=None)

            if existing_task.generation_status == GenerationStatus.COMPLETED:
                document_url = await self.file_storage.get_presigned_url(
                    file_key=existing_task.document_path, expires_in=180)
                response = StickerGenerationTaskResultResponse(
                    task_id=existing_task.task_id,
                    product_id=template_data.product_id,
                    generation_status=existing_task.generation_status,
                    error_message=existing_task.error_message,
                    document_url=document_url)
            return response

        total_active_tasks = await self.generation_tasks_repo.count_total_active_tasks(
        )
        if total_active_tasks > 80:  #TODO: вынести константу
            raise TotalTaskLimit(
                "Превышен лимит общего количества активных задач")

        #TODO: логировать данные для стикеры
        generation_task = await self.generation_tasks_repo.create_task(
            product_id=template_data.product_id,
            sticker_type=StickerType.TRANSPORT,
            hash=template_hash,
            path=None,
        )

        task_info = await self.generation_tasks_repo.get_task_by_uuid(
            generation_task.task_uuid)
        if task_info:
            await self.send_notice_with_updated_task_status(
                StickerGenerationTaskInfo(
                    task_id=task_info.id,
                    product_id=task_info.product_id,
                    generation_status=task_info.generation_status,
                    error_message=task_info.error_message,
                    document_url=None,
                    sticker_type=task_info.sticker_type,
                    created_at=task_info.created_at,
                    updated_at=task_info.updated_at,
                ))

        broker_payload = {
            "task_id": generation_task.task_uuid,
            "limit": template_data.limit,
            "offset": template_data.offset,
            "data": {
                "product_id":
                template_data.product_id,
                "gross_weight":
                template_data.gross_weight,
                "net_weight":
                template_data.net_weight,
                "box_size": {
                    "length": template_data.box_size.box_length,
                    "width": template_data.box_size.box_width,
                    "height": template_data.box_size.box_height,
                } if template_data.box_size else None,
                "proforma_number":
                template_data.proforma_number,
                "items_per_box":
                template_data.items_per_box,
                "total_boxes":
                template_data.total_boxes,
                "certification_type":
                template_data.certification_type.value,
                "local_data": [{
                    "local": "en",
                    "data": {
                        "name": template_data.name_en,
                        "color": template_data.color_en,
                        "produced_in": template_data.produced_in_en,
                    }
                }, {
                    "local": "ru",
                    "data": {
                        "name": template_data.name,
                        "color": template_data.color,
                        "produced_in": template_data.produced_in,
                    }
                }]
            }
        }

        broker_task_id = await self.publisher.publish_generation_task(
            broker_payload)
        response = StickerGenerationTaskResultResponse(
            task_id=generation_task.task_id,
            product_id=template_data.product_id,
            generation_status=generation_task.generation_status,
            error_message=generation_task.error_message,
            document_url=None)
        return response

    async def create_or_get_individual_task(
        self, template_data: IndividualStickerTemplateView
    ) -> StickerGenerationTaskResultResponse:

        await self.user_data_service.save_unit_sticker_user_data(template_data)
        # await self.localisation_service.save_localisations(template_data)
        hash_payload = {
            "sticker_type": StickerType.INDIVIDUAL.value,
            "product_id": template_data.product_id,
            "manufacturer": template_data.manufacturer,
            "importer_details": template_data.importer_details,
            "production_date": template_data.production_date,
            "certification_type": template_data.certification_type.value,
            "name": template_data.name,
            "color": template_data.color,
            "material": template_data.material,
            "produced_in": template_data.produced_in,
            "quantity": template_data.quantity,
        }

        template_hash = StickerTemplateHashService.calculate(hash_payload)

        existing_task = await self.generation_tasks_repo.get_by_unique_key(
            product_id=template_data.product_id,
            sticker_type=StickerType.INDIVIDUAL,
            template_hash=template_hash)

        if existing_task:
            print(
                f"Нашел готовую задачу INDIVIDUAL для {template_data.product_id}"
            )
            document_url = None
            if existing_task.generation_status == GenerationStatus.COMPLETED:
                document_url = await self.file_storage.get_presigned_url(
                    file_key=existing_task.document_path, expires_in=180)

            return StickerGenerationTaskResultResponse(
                task_id=existing_task.task_id,
                product_id=template_data.product_id,
                generation_status=existing_task.generation_status,
                error_message=existing_task.error_message,
                document_url=document_url)

        total_active_tasks = await self.generation_tasks_repo.count_total_active_tasks(
        )
        if total_active_tasks > 80:
            #TODO: убрать константу
            raise TotalTaskLimit(
                "Превышен лимит общего количества активных задач")
        print(f"генерирую таску для {template_data.product_id}")
        generation_task = await self.generation_tasks_repo.create_task(
            product_id=template_data.product_id,
            sticker_type=StickerType.INDIVIDUAL,
            hash=template_hash,
            path=None,
        )
        #TODO: логирование

        task_info = await self.generation_tasks_repo.get_task_by_uuid(
            generation_task.task_uuid)
        if task_info:
            await self.send_notice_with_updated_task_status(
                StickerGenerationTaskInfo(
                    task_id=task_info.id,
                    product_id=task_info.product_id,
                    generation_status=task_info.generation_status,
                    error_message=task_info.error_message,
                    document_url=None,
                    sticker_type=task_info.sticker_type,
                    created_at=task_info.created_at,
                    updated_at=task_info.updated_at,
                ))

        broker_payload = {
            "task_id": str(generation_task.task_uuid),
            "quantity": template_data.quantity,
            "data": {
                "product_id":
                template_data.product_id,
                "manufacturer":
                template_data.manufacturer,
                "importer_details":
                template_data.importer_details,
                "production_date":
                template_data.production_date,
                "certification_type":
                template_data.certification_type.value,
                "local_data": [{
                    "local": "ru",
                    "data": {
                        "name": template_data.name,
                        "color": template_data.color,
                        "material": template_data.material,
                        "produced_in": template_data.produced_in
                    }
                }]
            }
        }
        #TODO: логирование

        broker_task_id = await self.publisher.publish_generation_task_for_individual(
            broker_payload)
        updated = await self.generation_tasks_repo.get_by_id(
            generation_task.task_id)
        if updated:
            return StickerGenerationTaskResultResponse(
                task_id=updated.task_id,
                product_id=template_data.product_id,
                generation_status=updated.generation_status,
                error_message=updated.error_message,
                document_url=None)

        return StickerGenerationTaskResultResponse(
            task_id=generation_task.task_id,
            product_id=template_data.product_id,
            generation_status=generation_task.generation_status,
            error_message=generation_task.error_message,
            document_url=None)

    async def handle_broker_response(self, data: dict) -> None:
        """Бизнес логика обработки сообщения от брокера"""

        task_uuid = data.get("task_id")
        status = data.get("status")
        document_path = data.get("file_storage_key")
        error_message = data.get("error")

        if not task_uuid:
            print("пошло не так в handle_broker_response")
            #TODO: логирование
            return
        await self.generation_tasks_repo.update_task_result(
            task_uuid=task_uuid,
            status=status,
            document_path=document_path,
            error_message=error_message)

        task_info = await self.generation_tasks_repo.get_task_by_uuid(task_uuid
                                                                      )

        if task_info:
            await self.send_notice_with_updated_task_status(
                StickerGenerationTaskInfo(
                    task_id=task_info.id,
                    product_id=task_info.product_id,
                    generation_status=task_info.generation_status,
                    error_message=task_info.error_message,
                    document_url=None,
                    sticker_type=task_info.sticker_type,
                    created_at=task_info.created_at,
                    updated_at=task_info.updated_at,
                ))

    async def get_sticker_tasks(
            self,
            user_id: int | None = None) -> list[StickerGenerationTaskInfo]:
        """
        Получить список задач на генерацию стикеров.
        """
        tasks = await self.generation_tasks_repo.get_tasks_list(user_id=user_id
                                                                )
        result = []
        for task in tasks:
            url = None

            if task.generation_status == GenerationStatus.COMPLETED:
                url = await self.file_storage.get_presigned_url(
                    file_key=task.document_path,
                    expires_in=120,
                )

            result.append(
                StickerGenerationTaskInfo(
                    task_id=task.id,
                    product_id=task.product_id,
                    generation_status=task.generation_status,
                    error_message=task.error_message,
                    document_url=url,
                    sticker_type=task.sticker_type,
                    created_at=task.created_at,
                    updated_at=task.updated_at,
                ))

        return result

    async def send_notice_with_updated_task_status(
            self, task_info: StickerGenerationTaskInfo):
        """
        Отправить уведомление об изменении статуса задачи на генерацию.
        """
        notice = StickerGenerationTaskNotice(
            event=StickerGenerationTaskEvent.UPDATE_STATUS,
            task_data=task_info,
        )

        await self.task_notification_service.publish_notice(notice)



import logging
from app.database.repositories.sticker_generation_tasks import StickerGenerationTasksRepository
from app.exceptions.stickers import TotalTaskLimit
from app.file_storage.base.interface import IFileStorage
from app.models.box_stickers import BoxStickerTemplateView, GenerationStatus, StickerGenerationTaskResultResponse, StickerType
from app.service.localisation import LocalisationService
from app.service.sticker_generation_publisher import StickerGenerationPublisher
from app.service.sticker_template_hash import StickerTemplateHashService
from app.service.sticker_user_data import StickerUserDataService


logger = logging.getLogger(__name__)

class StickerGenerationService:
    def __init__(
        self,
        generation_tasks_repo: StickerGenerationTasksRepository,
        user_data_service: StickerUserDataService,
        localisation_service: LocalisationService,
        publisher: StickerGenerationPublisher,
        file_storage: IFileStorage,
    ):
        self.generation_tasks_repo = generation_tasks_repo
        self.user_data_service = user_data_service
        self.localisation_service = localisation_service
        self.publisher = publisher
        self.file_storage = file_storage


    async def create_or_get_box_generation_task(
        self,
        # user_id: int, #TODO: пока нет авторизации польщователей
        template_data: BoxStickerTemplateView,
        ) -> StickerGenerationTaskResultResponse:
        await self.user_data_service.save_box_sticker_user_data(template_data)
        await self.localisation_service.save_localisations(template_data)
        hash_payload = {
            "sticker_type": StickerType.TRANSPORT.value,
            "product_id": template_data.product_id,
            "name": template_data.name,
            "name_en": template_data.name_en,
            "color": template_data.color,
            "color_en": template_data.color_en,
            "gross_weight": template_data.gross_weight,
            "net_weight": template_data.net_weight,
            "box_size": template_data.box_size.model_dump() if template_data.box_size else None,
            "items_per_box": template_data.items_per_box,
            "total_boxes": template_data.total_boxes,
            "produced_in": template_data.produced_in,
            "produced_in_en": template_data.produced_in_en,
            "proforma_number": template_data.proforma_number,
            "certification_type": template_data.certification_type.value,
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
            # await self.generation_tasks_repo.add_user_to_task(
            #     task_id=existing_task.task_id,
            #     user_id=user_id,
            #     )
            #TODO: убрать пока не будет актуально ограничивать таски на каждого пользователя 
            print("нашел готовую") #TODO: логирование
            response = response = StickerGenerationTaskResultResponse(
                    task_id=existing_task.task_id,
                    generation_status=existing_task.generation_status,
                    error_message=existing_task.error_message,
                    document_url=None
                    )

            if existing_task.generation_status == GenerationStatus.COMPLETED:
                document_url = await self.file_storage.get_presigned_url(
                        file_key=existing_task.document_path, 
                        expires_in=180
                    )
                response = StickerGenerationTaskResultResponse(
                    task_id=existing_task.task_id,
                    generation_status=existing_task.generation_status,
                    error_message=existing_task.error_message,
                    document_url=document_url
                    )
            return response

        # active_count = await self.generation_tasks_repo.count_active_tasks_by_user(user_id) TODO: добавляем проверку на общее количество активных запросов

        # if active_count >= self.max_active_tasks_per_user: TODO: использовать ограничения по количеству тасок на пользователя в конфиге?
        #     raise ValueError("Превышен лимит документов в обработке")
        
        total_active_tasks = await self.generation_tasks_repo.count_total_active_tasks()
        if total_active_tasks > 80: #TODO: вынести константу
            raise TotalTaskLimit("Превышен лимит общего количества активных задач")
        
        #TODO: логировать данные для стикеры
        generation_task = await self.generation_tasks_repo.create_task(
            product_id=template_data.product_id,
            sticker_type=StickerType.TRANSPORT,
            hash=template_hash,
            path=None,
        )

        # await self.generation_tasks_repo.add_user_to_task(
        #     task_id=generation_task.task_id,
        #     user_id=user_id,
        # )
 
        broker_payload = {
            "task_id": generation_task.task_uuid,
            "limit": None,
            "offset": None,
            "data": {
                "product_id": template_data.product_id,
                "gross_weight": template_data.gross_weight,
                "net_weight": template_data.net_weight,
                "box_size": {
                    "length": template_data.box_size.box_length,
                    "width": template_data.box_size.box_width,
                    "height": template_data.box_size.box_height,
                } if template_data.box_size else None,
                "proforma_number": template_data.proforma_number,
                "items_per_box": template_data.items_per_box,
                "total_boxes": template_data.total_boxes,
                "certification_type": template_data.certification_type.value,
                "local_data": [
                    {
                        "local": "en",
                        "data": {
                            "name": template_data.name_en,
                            "color": template_data.color_en,
                            "produced_in": template_data.produced_in_en,
                        }
                    },
                    {
                        "local": "ru",
                        "data": {
                            "name": template_data.name,
                            "color": template_data.color,
                            "produced_in": template_data.produced_in,
                        }
                    }
                ]
            }
        }

        broker_task_id = await self.publisher.publish_generation_task(broker_payload)
        if broker_task_id:
            await self.generation_tasks_repo.set_processing(
                task_uuid=generation_task.task_uuid)

            updated = await self.generation_tasks_repo.get_by_id(generation_task.id)
            if updated:
                return updated
        response = StickerGenerationTaskResultResponse(
                 task_id=generation_task.task_id,
                 generation_status=generation_task.generation_status,
                 error_message=generation_task.error_message,
                 document_url=None
                 )
        return response
    

    async def handle_broker_response(self, data: dict) -> None:
        """Бизнес-логика обработки сообщения от брокера"""

        task_uuid = data.get("task_id")
        status = data.get("status")
        document_path = data.get("file_storage_key")
        error_message = data.get("error")

        
        if not task_uuid:
                print("пошло не так в handle_broker_response")
                return
        await self.generation_tasks_repo.update_task_result(
                task_uuid=task_uuid,
                status=status,
                document_path=document_path,
                error_message=error_message
            )


import logging
from app.database.repositories.sticker_generation_tasks import StickerGenerationTasksRepository
from app.models.box_stickers import BoxStickerTemplateView, StickerGenerationTaskResult, StickerType
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
    ):
        self.generation_tasks_repo = generation_tasks_repo
        self.user_data_service = user_data_service
        self.localisation_service = localisation_service
        self.publisher = publisher


    async def create_or_get_box_generation_task(
        self,
        user_id: int,
        template_data: BoxStickerTemplateView,
        ) -> StickerGenerationTaskResult:
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
        print(existing_task)

        if existing_task:
            await self.generation_tasks_repo.add_user_to_task(
                task_id=existing_task.task_id,
                user_id=user_id,
                )
            print("нашел готовую")
            #TODO: если таска висит со статусом ошибки, то другому польщователю вернем чужую ошибку. Нужен ретрай!
            return existing_task

        active_count = await self.generation_tasks_repo.count_active_tasks_by_user(user_id)

        print("active_count", active_count)

        # if active_count >= self.max_active_tasks_per_user:
        #     raise ValueError("Превышен лимит документов в обработке")
        
        #TODO: StickerType.TRANSPORT.value.lower() ? stickers/{template_data.product_id}_{StickerType.TRANSPORT.value}_{template_hash}.pdf лучше? хуже?
        document_path = (
            f"stickers/{template_data.product_id}/"
            f"{StickerType.TRANSPORT.value}/"
            f"{template_hash}.pdf"
        )
        
        #TODO: логировать данные для стикеры

        generation_task = await self.generation_tasks_repo.create_task(
            product_id=template_data.product_id,
            sticker_type=StickerType.TRANSPORT,
            hash=template_hash,
            path=document_path,
        )

        await self.generation_tasks_repo.add_user_to_task(
            task_id=generation_task.task_id,
            user_id=user_id,
        )
        
        #добавляем 
        broker_payload = {
            "task_id": generation_task.task_id,
            "product_id": template_data.product_id,
            "sticker_type": StickerType.TRANSPORT.value,
            "template_hash": template_hash,
            "template_data": hash_payload,
            "document_path": document_path,
        }

        broker_task_id = await self.publisher.publish_generation_task(broker_payload)

        if broker_task_id:
            await self.generation_tasks_repo.set_processing(
                task_id=generation_task.task_id,
                generation_task=broker_task_id)

            updated = await self.generation_tasks_repo.get_by_id(generation_task.id)
            if updated:
                return updated

        return generation_task
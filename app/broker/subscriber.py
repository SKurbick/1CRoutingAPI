from app.cache.client import RedisClient
from app.service.sticker_tasks_notification import StickerTasksNotificationsService
from faststream import Context
from app.broker.broker import broker_manager
from app.broker.topology import ExchangeName, QueueName
from app.database.repositories.sticker_generation_tasks import StickerGenerationTasksRepository
from app.dependencies.config import SETTINGS

from app.file_storage import IFileStorage
from app.service.sticker_generation_service import StickerGenerationService
from asyncpg import Pool


@broker_manager.subscriber(exchange=ExchangeName.DOCGEN_EVENT,
                           queue=QueueName.RABBIT_Q_DOCGEN_BOX_LABEL_RESPONSE)
async def handle_responses_box(
        data: dict,
        file_storage: IFileStorage = Context(),
        pool: Pool = Context(),
        redis_client: RedisClient = Context(),
) -> None:
    """Обрабатывает данные из брокера по транспортным стикерам, переданные сервисом генерации стикеров"""
    tasks_repo = StickerGenerationTasksRepository(pool)
    task_notification_service = StickerTasksNotificationsService(
        redis_client=redis_client
        )
    service = StickerGenerationService(
        generation_tasks_repo=tasks_repo,
        user_data_service=None,
        localisation_service=None,
        publisher=None,
        file_storage=file_storage,
        task_notification_service=task_notification_service
        )
    await service.handle_broker_response(data)


@broker_manager.subscriber(exchange=ExchangeName.DOCGEN_EVENT,
                           queue=QueueName.RABBIT_Q_DOCGEN_UNIT_LABEL_RESPONSE)
async def handle_responses_unit(
        data: dict,
        file_storage: IFileStorage = Context(),
        pool: Pool = Context(),
        redis_client: RedisClient = Context(),
        ) -> None:
    """Обрабатывает данные из брокера по индивидуальным стикерам, переданные сервисом генерации стикеров"""
    tasks_repo = StickerGenerationTasksRepository(pool)
    task_notification_service = StickerTasksNotificationsService(
        redis_client=redis_client
        )
    service = StickerGenerationService(
        generation_tasks_repo=tasks_repo,
        user_data_service=None,
        localisation_service=None,
        publisher=None,
        file_storage=file_storage,
        task_notification_service=task_notification_service
        )
    await service.handle_broker_response(data)

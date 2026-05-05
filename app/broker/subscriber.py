from fastapi import Depends
from faststream import Context
from app.broker.broker import broker_manager
from app.broker.topology import ExchangeName, QueueName, RoutingKey
from app.database.repositories.sticker_generation_tasks import StickerGenerationTasksRepository
from app.dependencies.box_stickers import get_pool
from app.dependencies.config import SETTINGS

from faststream import Context
from app.file_storage import IFileStorage
from app.models.box_stickers import GenerationStatus
from app.service.sticker_generation_service import StickerGenerationService
from faststream.rabbit import RabbitMessage
from asyncpg import Pool



@broker_manager.subscriber(
        exchange="docgen.event.exchange",
        # routing_key="doc.generated.box_label",
        queue="docgen.box_label.event.queue")
async def handle_responses(data: dict, file_storage: IFileStorage = Context()):
    print("-"*25)
    print(f"Получен ответ от брокера: {data}")
    key = data.get("file_storage_key")
    if key:
        url = await file_storage.get_presigned_url(file_key=key, expires_in=180)
        print(url)
    else:
        print("Ключ не найден.")
        tasks_repo = StickerGenerationTasksRepository(pool)
    service = StickerGenerationService(
        generation_tasks_repo=tasks_repo,
        user_data_service=None,
        localisation_service=None,
        publisher=None
    )


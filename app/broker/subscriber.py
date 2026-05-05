from fastapi import Depends
from faststream import Context
from app.broker.broker import broker_manager
from app.broker.topology import ExchangeName, QueueName, RoutingKey
from app.database.repositories.sticker_generation_tasks import StickerGenerationTasksRepository
from app.dependencies.box_stickers import get_pool
from app.dependencies.config import SETTINGS
from app.models.box_stickers import GenerationStatus
from app.service.sticker_generation_service import StickerGenerationService
from faststream.rabbit import RabbitMessage
from asyncpg import Pool



@broker_manager.subscriber(
    exchange=ExchangeName.DOCGEN_EVENT,
    queue=QueueName.RABBIT_Q_DOCGEN_BOX_LABEL_RESPONSE
)
async def handle_responses(body: dict,
    message: RabbitMessage,
    pool: Pool = Depends(get_pool),
):


    tasks_repo = StickerGenerationTasksRepository(pool)
    service = StickerGenerationService(
        generation_tasks_repo=tasks_repo,
        user_data_service=None,
        localisation_service=None,
        publisher=None
    )


    await service.handle_broker_response(body)


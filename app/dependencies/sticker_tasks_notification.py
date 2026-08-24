from typing import Annotated

from fastapi import Request, Depends

from app.cache.client import RedisClient
from app.service.sticker_tasks_notification import StickerTasksNotificationsService


def get_redis_client(request: Request) -> RedisClient:
    return request.app.state.redis_client


def get_sticker_tasks_notification_service(
        redis_client: Annotated[RedisClient, Depends(get_redis_client)],
) -> StickerTasksNotificationsService:
    return StickerTasksNotificationsService(
        redis_client=redis_client,
    )

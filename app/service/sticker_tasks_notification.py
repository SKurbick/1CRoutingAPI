import asyncio
import json
from contextlib import asynccontextmanager
from typing import AsyncGenerator

from redis.asyncio.client import PubSub
from sse_starlette import JSONServerSentEvent

from app.cache.client import RedisClient
from app.models.box_stickers import StickerGenerationTaskEvent


class StickerTasksNotificationsService:
    """
    Сервис для обмена уведомлениями о задачах по генерации стикеров маркировки.
    """

    CHANNEL = "stickers-tasks-notifications"
    
    def __init__(
            self,
            redis_client: RedisClient,
    ):
        self._redis_client = redis_client
        self._pubsub = None

    @asynccontextmanager
    async def listener(self) -> AsyncGenerator[PubSub, None]:
        """
        Контестный менеджер возвращает подписчика на уведомления.
        При завершении отписывается от канала и закрывается.
        """
        if not self._pubsub:
            self._pubsub = self._redis_client.get_pubsub()
            print("Создан подписчик на уведомления о задачах по генерации стикеров.")
        
        await self._pubsub.subscribe(self.CHANNEL)
        try:
            yield self._pubsub
        finally:
            await self._pubsub.unsubscribe(self.CHANNEL)
            print("Подписчик на уведомления о задачах по генерации стикеров отписался.")
            await self._pubsub.close()
            print("Подписчик на уведомления о задачах по генерации стикеров закрыт.")

    async def listen(self) -> AsyncGenerator[JSONServerSentEvent, None]:
        """
        Генератор, слушает канал Redis и возвращает новые сообщения.
        """
        async with self.listener() as listener:
            try:
                while True:
                    try:
                        message = await asyncio.wait_for(
                            listener.get_message(ignore_subscribe_messages=True),
                            timeout=1.0
                        )

                        if message and message["type"] == "message":
                            print(f"Получено сообщение: {message}")
                            data = json.loads(message["data"])
                            yield JSONServerSentEvent(data)
                    except asyncio.TimeoutError:
                        continue
                    except asyncio.CancelledError:
                        break
            except Exception as e:
                print(f"Необработанное исключение: {e}")
                raise

    async def publish_notice(self, notice: StickerGenerationTaskEvent):
        """
        Отправить уведомление подписчикам.
        """
        message = json.dumps(notice, ensure_ascii=False)
        await self._redis_client.publish(
            channel=self.CHANNEL,
            message=message
        )

import asyncio
import json
from contextlib import asynccontextmanager
from typing import AsyncGenerator

from redis.asyncio.client import PubSub
from sse_starlette import JSONServerSentEvent

from app.cache.client import RedisClient, PubSubConnLimitError
from app.models.box_stickers import StickerGenerationTaskNotice


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
            await self._redis_client.close_pubsub(self._pubsub)

    async def listen(self) -> AsyncGenerator[JSONServerSentEvent, None]:
        """
        Генератор, слушает канал Redis и возвращает новые сообщения.
        """
        try:
            async with self.listener() as listener:
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
                            print(f"Галя! У нас ОТМЕНА подписки на SSE: {listener.channels}")
                            break
        except PubSubConnLimitError as e:
            print(str(e))
            yield JSONServerSentEvent({"message": "Превышено количество подписчиков на события."})
        except Exception as e:
            print(f"Необработанное исключение: {e}")
            raise

    async def publish_notice(self, notice: StickerGenerationTaskNotice):
        """
        Отправить уведомление подписчикам.
        """
        message = notice.model_dump_json()
        await self._redis_client.publish(channel=self.CHANNEL, message=message)

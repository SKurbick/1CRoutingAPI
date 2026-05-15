from typing import Optional

from redis.asyncio import Redis, ConnectionPool
from redis.asyncio.client import PubSub
from redis.exceptions import ConnectionError, TimeoutError

from app.dependencies.config import settings


class RedisClient:
    def __init__(self):
        self.pool: Optional[ConnectionPool] = None
        self.client: Optional[Redis] = None
        self._pubsubs: list[PubSub] = []

    def _build_pool(self) -> ConnectionPool:
        print("Создаем пул соединений к Redis...")
        return ConnectionPool(
            host=settings.REDIS_HOST,
            port=settings.REDIS_PORT,
            db=settings.REDIS_DB,
            password=settings.REDIS_PASSWORD,
            socket_connect_timeout=settings.REDIS_TIMEOUT,
            socket_timeout=settings.REDIS_TIMEOUT,
            max_connections=settings.REDIS_MAX_CONNECTIONS,
            health_check_interval=30,
            decode_responses=True,
        )

    async def connect(self) -> Redis:
        if self.client is None:
            self.pool = self._build_pool()
            self.client = Redis(connection_pool=self.pool)

            try:
                await self.client.ping()
                print(f"Redis подключён: {settings.REDIS_HOST}:{settings.REDIS_PORT}/{settings.REDIS_DB}")
            except (ConnectionError, TimeoutError) as e:
                print(f"Ошибка подключения к Redis: {e}")
                raise

        return self.client

    async def disconnect(self):
        if self._pubsubs:
            print("Закрываем всех подписчиков Redis.Pubsub...")
            for ps in self._pubsubs:
                try:
                    print(f"Закрываем подписчика Redis: {ps.channels}")
                    await ps.unsubscribe()
                    print(f"Pubsub отписан от всех каналов: {ps.channels}")
                    await ps.close()
                    print("Pubsub закрыт")
                except Exception as e:
                    print(f"Ошибка при закрытии Pubsub Redis: {e}")

            self._pubsubs = []
            print(f"Закрыли всех Pubsubs.")

        if self.client:
            await self.client.aclose()
            self.client = None
            print("Закрыли клиента Redis.")

        if self.pool:
            await self.pool.disconnect()
            self.pool = None
            print("Закрыли пул соединений с Redis")

    async def publish(self, channel: str, message, **kwargs):
        client = self.get_client()
        print(f"Опубликовано сообщение в {channel}: '{message}'")
        await client.publish(
            channel=channel,
            message=message,
            **kwargs
        )

    def get_client(self) -> Redis:
        if self.client is None:
            raise RuntimeError("Клиент Redis не подключен. Сначала вызовите connect().")

        return self.client

    def get_pubsub(self) -> PubSub:
        print("Создаем нового подписчика Redis Pubsub...")
        new_pubsub = self.get_client().pubsub()
        self._pubsubs.append(new_pubsub)
        return new_pubsub


redis_client = RedisClient()

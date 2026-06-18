from typing import Optional

from redis.asyncio import Redis, ConnectionPool
from redis.asyncio.client import PubSub
from redis.exceptions import ConnectionError, TimeoutError

from app.dependencies.config import settings


class PubSubConnLimitError(Exception):
    """
    Превышение максимального количества подключений подписчиков к Redis.
    """


class RedisClient:
    def __init__(self):
        self.pool: Optional[ConnectionPool] = None
        self.client: Optional[Redis] = None
        self.max_pubsub_count = settings.REDIS_MAX_CONNECTIONS // 2
        self._pubsubs_count = 0

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
        if self._pubsubs_count >= self.max_pubsub_count:
            raise PubSubConnLimitError("Превышено максимально допустимое количество подписчиков Redis!")

        print("Создаем нового подписчика Redis Pubsub...")
        new_pubsub = self.get_client().pubsub()
        self._pubsubs_count += 1
        print(f"Всего подписчиков Redis: {self._pubsubs_count}/{self.max_pubsub_count}")
        return new_pubsub

    async def close_pubsub(self, pubsub: PubSub):
        print("Закрываем подписчика...")
        try:
            await pubsub.aclose()
            print("Подписчик закрыт.")
        finally:
            await pubsub.aclose()
            print("Подписчик закрыт принудительно.")
            self._pubsubs_count -= 1
            print(f"Всего подписчиков Redis: {self._pubsubs_count}/{self.max_pubsub_count}")
            print(await pubsub.ping())


class DisabledRedisClient:
    def __init__(self):
        self.enabled = False

    async def connect(self):
        print("Redis disabled by REDIS_ENABLED=False.")
        return None

    async def disconnect(self):
        return None

    async def publish(self, channel: str, message, **kwargs):
        print(f"Redis disabled, message to {channel} was not published.")

    def get_client(self):
        raise RuntimeError("Redis disabled by REDIS_ENABLED=False.")

    def get_pubsub(self):
        raise RuntimeError("Redis disabled by REDIS_ENABLED=False.")

    async def close_pubsub(self, pubsub):
        return None


redis_client = RedisClient()

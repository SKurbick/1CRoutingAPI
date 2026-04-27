from functools import lru_cache
from typing import Callable, Any, Coroutine, Self

from faststream.rabbit import RabbitBroker, RabbitExchange, RabbitQueue


from .topology import EXCHANGE_CONFIGS, QUEUE_CONFIGS, ExchangeName, QueueName, RoutingKey


class BrokerManager:
    __instance: Self | None = None

    def __init__(self):
        self._broker: RabbitBroker | None = None
        self._host = SETTINGS.RABBIT_HOST
        self._port = SETTINGS.RABBIT_PORT
        self.__user = SETTINGS.RABBIT_USER
        self.__pass = SETTINGS.RABBIT_PASS

        self.exchanges: dict[ExchangeName, RabbitExchange] = {
            exchange: RabbitExchange(
                name=config.name,
                type=config.type,
                durable=config.durable,
            ) for exchange, config in EXCHANGE_CONFIGS.items()
        }

        self.queues: dict[QueueName, RabbitQueue] = {
            queue: RabbitQueue(
                name=config.name,
                routing_key=config.routing_key,
                durable=config.durable
            ) for queue, config in QUEUE_CONFIGS.items()
        }

    def __new__(cls, *args, **kwargs):
        if not cls.__instance:
            cls.__instance = super(BrokerManager, cls).__new__(cls, *args, **kwargs)
            cls.__instance.__init__()

        return cls.__instance

    @property
    def broker(self):
        if not self._broker:
            LOGGER.info(f"Инициализация брокера: {self._host}:{self._port}")
            self._broker = RabbitBroker(
                url=f"amqp://{self.__user}:{self.__pass.get_secret_value()}@{self._host}:{self._port}/" 
            )

        return self._broker

    def _get_exchange(self, name: ExchangeName) -> RabbitExchange:
        return self.exchanges[name]

    def _get_queue(self, name: QueueName) -> RabbitQueue:
        return self.queues[name]

    def subscriber(self, queue: QueueName, exchange: ExchangeName, *args: Any, **kwargs: Any) -> Callable:
        rabbit_queue = self._get_queue(queue)
        rabbit_exchange = self._get_exchange(exchange)
        LOGGER.info(f"Регистрация подписчика: exchange='{rabbit_exchange.name}', queue='{rabbit_queue.name}', routing_key='{rabbit_queue.routing_key}'")
        return self.broker.subscriber(queue=rabbit_queue, exchange=rabbit_exchange, *args, **kwargs)

    async def publish(self, message: Any, routing_key: RoutingKey, exchange: ExchangeName, *args: Any, **kwargs: Any) -> Coroutine:
        rabbit_exchange = self._get_exchange(exchange)
        LOGGER.debug(f"Публикация сообщения: exchange='{rabbit_exchange.name}', routing_key='{routing_key.value}', message={message.__repr__()}")
        return await self.broker.publish(
            message=message, routing_key=routing_key.value, exchange=rabbit_exchange, *args, **kwargs
        )

@lru_cache(maxsize=1)
def get_broker_manager():
    LOGGER.info("Инициализация BrokerManager...")
    return BrokerManager()

broker_manager = get_broker_manager()
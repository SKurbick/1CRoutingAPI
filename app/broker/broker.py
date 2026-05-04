from functools import lru_cache
from typing import Any, Callable, Self

from faststream.rabbit import RabbitBroker, RabbitExchange, RabbitQueue


from app.broker.topology import EXCHANGE_CONFIGS, ExchangeName, QueueName, RoutingKey, QUEUE_CONFIGS
from app.dependencies.config import SETTINGS


class BrokerManager:
    __instance: Self | None = None
    def __init__(self):
        self._broker: RabbitBroker | None = None

        self.exchanges: dict[ExchangeName, RabbitExchange] = {
            exchange: RabbitExchange(
                name=config.name,
                type=config.type,
                durable=config.durable,
            )
            for exchange, config in EXCHANGE_CONFIGS.items()
        }
        self.queues: dict[QueueName, RabbitQueue] = {
            queue: RabbitQueue(
                name=config.name,
                routing_key=config.routing_key,
                durable=config.durable
            ) for queue, config in QUEUE_CONFIGS.items()
        }

    @property
    def broker(self) -> RabbitBroker:
        if self._broker is None:
            password = SETTINGS.RABBIT_PASS.get_secret_value()
            self._broker = RabbitBroker(
                url=(
                    f"amqp://{SETTINGS.RABBIT_USER}:"
                    f"{password}@"
                    f"{SETTINGS.RABBIT_HOST}:"
                    f"{SETTINGS.RABBIT_PORT}/{SETTINGS.RABBIT_VHOST}"
                )
            )

            
        return self._broker
    
    def __new__(cls, *args, **kwargs):
        if not cls.__instance:
            cls.__instance = super(BrokerManager, cls).__new__(cls, *args, **kwargs)
            cls.__instance.__init__()

        return cls.__instance

    def get_exchange(self, name: ExchangeName) -> RabbitExchange:
        return self.exchanges[name]

    async def publish(self, message: Any, routing_key: RoutingKey, exchange: ExchangeName) -> None:
        await self.broker.publish(
            message=message,
            routing_key=routing_key.value,
            exchange=self.get_exchange(exchange),
        )

    def subscriber(self, queue: QueueName, exchange: ExchangeName, *args: Any, **kwargs: Any) -> Callable:
        rabbit_queue = self._get_queue(queue)
        rabbit_exchange = self._get_exchange(exchange)
        print(f"Регистрация подписчика: exchange='{rabbit_exchange.name}', queue='{rabbit_queue.name}', routing_key='{rabbit_queue.routing_key}'")
        return self.broker.subscriber(queue=rabbit_queue, exchange=rabbit_exchange, *args, **kwargs)
    
    def _get_queue(self, name: QueueName) -> RabbitQueue:
        return self.queues[name]
    
    def _get_exchange(self, name: ExchangeName) -> RabbitExchange:
        return self.exchanges[name]

    async def connect(self) -> None:
        await self.broker.connect()
        print("RabbitMQ connected")

    async def close(self) -> None:
        await self.broker.close()
        print("RabbitMQ closed")


# @lru_cache(maxsize=1)
def get_broker_manager() -> BrokerManager:
    return BrokerManager()


broker_manager = get_broker_manager()
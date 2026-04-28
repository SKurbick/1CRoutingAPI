from functools import lru_cache
from typing import Any, Self

from faststream.rabbit import RabbitBroker, RabbitExchange


from app.broker.topology import EXCHANGE_CONFIGS, ExchangeName, RoutingKey
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

    @property
    def broker(self) -> RabbitBroker:
        if self._broker is None:
            self._broker = RabbitBroker(
                url=(
                    f"amqp://{SETTINGS.RABBIT_USER}:"
                    f"{SETTINGS.RABBIT_PASS}@"
                    f"{SETTINGS.RABBIT_HOST}:"
                    f"{SETTINGS.RABBIT_PORT}/"
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


@lru_cache(maxsize=1)
def get_broker_manager() -> BrokerManager:
    return BrokerManager()


broker_manager = get_broker_manager()
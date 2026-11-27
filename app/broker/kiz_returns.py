import asyncio
import json

import aio_pika
from pamqp.commands import Basic


class KizReturnsPublisher:
    """Independent connection; never declares or changes the WMS topology."""

    def __init__(self, url: str, exchange: str, routing_key: str, timeout: float):
        self.url = url
        self.exchange_name = exchange
        self.routing_key = routing_key
        self.timeout = timeout
        self.connection = None
        self.channel = None
        self.exchange = None

    async def publish(self, event_id: int, payload: dict) -> None:
        # Bound connect, passive lookup and publisher confirmation together.
        async with asyncio.timeout(self.timeout):
            if (
                self.connection is None or self.connection.is_closed
                or self.channel is None or self.channel.is_closed
                or self.exchange is None
            ):
                await self.close()
                self.connection = await aio_pika.connect(self.url, timeout=self.timeout)
                self.channel = await self.connection.channel(
                    publisher_confirms=True, on_return_raises=True,
                )
                self.exchange = await self.channel.get_exchange(
                    self.exchange_name, ensure=True,
                )
            confirmation = await self.exchange.publish(
                aio_pika.Message(
                    body=json.dumps(payload, ensure_ascii=False).encode("utf-8"),
                    content_type="application/json",
                    delivery_mode=aio_pika.DeliveryMode.PERSISTENT,
                    message_id=f"kiz-returns-{event_id}",
                ),
                routing_key=self.routing_key,
                mandatory=True,
                timeout=self.timeout,
            )
            if not isinstance(confirmation, Basic.Ack):
                raise RuntimeError("KIZ message was not acknowledged by RabbitMQ")

    async def close(self) -> None:
        try:
            if self.connection is not None and not self.connection.is_closed:
                async with asyncio.timeout(self.timeout):
                    await self.connection.close()
        finally:
            self.connection = None
            self.channel = None
            self.exchange = None

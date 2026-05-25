from app.broker.broker import broker_manager
from app.broker.topology import ExchangeName, RoutingKey


async def publish_box_sticker_generation_task(message: dict) -> None:
    """Передает данные по транспортному стикеру в брокер"""
    print(f"Данные, отправленные в брокер: {message}")
    await broker_manager.publish(
        message=message,
        routing_key=RoutingKey.DOC_BOX_LABEL,
        exchange=ExchangeName.DOCGEN_REQUEST,
    )

async def publish_individual_sticker_generation_task(message: dict) -> None:
    """Передает данные по индивидуальному стикеру в брокер"""
    print(f"Данные, отправленные в брокер: {message}")
    await broker_manager.publish(
        message=message,
        routing_key=RoutingKey.DOC_UNIT_LABEL,
        exchange=ExchangeName.DOCGEN_REQUEST,
    )
from app.broker.broker import broker_manager
from app.broker.topology import ExchangeName, RoutingKey


async def publish_box_sticker_generation_task(message: dict) -> None:
    print("отправил ", message)
    await broker_manager.publish(
        message=message,
        routing_key=RoutingKey.DOC_BOX_LABEL,
        exchange=ExchangeName.DOCGEN_REQUEST,
    )

async def publish_individual_sticker_generation_task(message: dict) -> None:
    print("отправил в", RoutingKey.DOC_UNIT_LABEL, message)
    await broker_manager.publish(
        message=message,
        routing_key=RoutingKey.DOC_UNIT_LABEL,
        exchange=ExchangeName.DOCGEN_REQUEST,
    )
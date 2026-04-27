from .broker import broker_manager, RoutingKey, ExchangeName


async def publish_generated_box_label_event(message: str):
    await broker_manager.publish(
        message=message,
        routing_key=RoutingKey.DOC_GENERATED_BOX_LABEL,
        exchange=ExchangeName.DOCGEN_EVENT,
    )


async def publish_generated_unit_label_event(message: str):
    await broker_manager.publish(
        message=message,
        routing_key=RoutingKey.DOC_GENERATED_UNIT_LABEL,
        exchange=ExchangeName.DOCGEN_EVENT,
    )
from app.broker.broker import broker_manager
# from app.broker.broker import BrokerManager
from app.broker.topology import ExchangeName, RoutingKey
from app.dependencies.config import SETTINGS




@broker_manager.subscriber(
        exchange="docgen.event.exchange",
        # routing_key="doc.generated.box_label",
        queue="docgen.box_label.event.queue")
async def handle_responses(data: dict):
    print("-"*25)
    print(f"Получен ответ от брокера: {data}")
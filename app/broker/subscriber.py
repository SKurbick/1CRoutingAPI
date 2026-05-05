from app.broker.broker import broker_manager
# from app.broker.broker import BrokerManager
from app.broker.topology import ExchangeName, RoutingKey
from app.dependencies.config import SETTINGS

from faststream import Context
from app.file_storage import IFileStorage




@broker_manager.subscriber(
        exchange="docgen.event.exchange",
        # routing_key="doc.generated.box_label",
        queue="docgen.box_label.event.queue")
async def handle_responses(data: dict, file_storage: IFileStorage = Context()):
    print("-"*25)
    print(f"Получен ответ от брокера: {data}")
    key = data.get("file_storage_key")
    if key:
        url = await file_storage.get_presigned_url(file_key=key, expires_in=180)
        print(url)
    else:
        print("Ключ не найден.")

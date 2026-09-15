# Карта декомиссии

| Категория/функция | Текущий код/API | Зависимость и перенос |
|---|---|---|
| Можно отключить после проверки usage | monitoring dashboard; deprecated shipment update | сначала telemetry/clients; функциональные аналоги новых shipment routes есть |
| Можно перенести в WMS | остатки, movements брака, add stock, inventory, receipt movements, containers/dimensions | WMS уже имеет movements и schema; ownership/API parity не подтверждены |
| Требует доработки WMS | резервы FBS/FBO, комплектация, пересортица, returns по `srid`, unique units/КИЗ, СЗ | нужны idempotency, statuses, history, mark binding, compatibility |
| Требует изменения frontend | multi-call shipment/acceptance/sticker flows | нужны новые endpoints/orchestrator и rollout |
| Требует изменения 1С | входящие update routes и пять исходящих paths | переключение endpoint, auth, contracts, retries/reconciliation |
| Нельзя отключить без анализа | WB documents, financial feeds, seller tokens, docgen Rabbit/S3/Redis | аналог/consumer неизвестны |

Специальные области: FBO shipment использует `supply_id` и account/INN; return uses `srid`; КИЗ хранится в `goods_returns_mark_list.mark_code`; sticker shipment semantics явно не выделена, sticker subsystem генерирует box/unit labels. Термины «СЗ» и уникальная единица товара не сопоставляются однозначно с конкретной моделью — open question.

Наличие аналога в WMS подтверждено только для HTTP movements и таблиц `wms.inventory/locations/receipt_items`. Остальные аналоги нельзя считать существующими по этому репозиторию.

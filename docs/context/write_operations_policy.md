# Политика операций записи

| Операция | Таблицы/внешний вызов | Transaction/order | Retry/idempotency/compensation |
|---|---|---|---|
| Receipt update | receipt/supply tables -> WMS -> `wms.receipt_items` | local DB commit first; WMS per batch | no retry; marker-based weak dedup; no compensation |
| Incoming receipt | acceptance/receipt tables -> 1С `inc_invoice/` | DB first | none |
| Incoming return | `incoming_returns`, goods return/link/marks -> 1С | one DB tx, then 1С | none |
| Return-to-supplier | two versioned tables | two consecutive transactions | repeat versions data; partial commit possible |
| Financial updates | four financial tables | invalidation then insert, generally no explicit tx | guid versioning only; partial invalidation possible |
| Kit/resorting | command table -> DB processor -> 1С | insert then polling; external after final | repeat creates command; no timeout/compensation |
| Defective movement | two `inventory_transactions` | one transaction | no idempotency |
| Add stock/inventory | inventory transactions/checks | local transaction | no idempotency |
| Shipment/reserve/FBS | reserve/shipment/inventory tables | repository-local tx | no idempotency |
| FBO shipment | same -> 1С commission | DB first; external exception swallowed | no retry/compensation |
| Buyer orders/barcode | buyer orders, acceptance, boxes, barcode tables | repository transactions vary | no request identity |
| Product/container/dimensions | products/containers/products_data | local DB | CRUD only |
| Sticker generate | task/user tables -> Rabbit | task saved then publish | unique-key reuse; no documented publish compensation |
| Sticker response consumer | task result/status | local DB, then Redis | broker delivery semantics/DLQ not configured in code |

## HTTP write operations

Все POST/PUT/DELETE из `api_map.md`, кроме read-like historical/product check. Input — Pydantic body/path/query. Логирование преимущественно `print`; WMS и sticker paths имеют logger/notifications.

## Consumer write operations

`handle_responses_box` и `handle_responses_unit` вызывают `StickerGenerationService.handle_broker_response`, обновляют task result/status и публикуют notice.

## Background jobs

Планировщиков/Celery/cron нет. Единственная встроенная background coroutine — монитор pool. FastStream consumers lifecycle-controlled.

## Интеграционные операции с 1С

Пять исходящих paths перечислены в `integration_map.md`; входящие update routes version data. Outbox, retry queue и журнал attempts не найдены.

## Прямые операции с БД

Все repositories используют raw SQL. Особо опасны busy-wait polling, `ALTER TABLE temp_barcode_data DISABLE TRIGGER ALL`, общий schema access и writes в `wms.receipt_items`.

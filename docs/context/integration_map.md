# Карта интеграций

| Система/направление | Protocol/endpoint | Auth/timeout | Retry/idempotency/error/log |
|---|---|---|---|
| 1CRoutingAPI -> 1С | POST relative `ass_disass/`, `goods_resorting/`, `goods_return/`, `inc_invoice/`, `commission_sales_fbo/` | HTTP Basic; timeout only FBO=60s | no retry/idempotency; text response; print |
| 1С -> API | financial, receipt, buyer order, return-to-supplier `*/update` | API auth absent | guid versioning only |
| API -> WMS | `WMS_API_URL_MOVEMENTS`, single/bulk movements | auth absent in code; 30s | no retry; raises HTTP errors; rotating log |
| API -> WMS DB | `wms.receipt_items/inventory/locations` | shared DB credentials | local SQL only |
| Frontend -> API | operator/CRUD/shipment/return/sticker endpoints | auth absent, CORS * | caller identity mostly `author` body |
| RabbitMQ | direct durable DOCGEN_REQUEST/EVENT exchanges; box/unit routing keys and response queues | broker credentials/settings | no explicit retry/DLQ; task DB dedup |
| API -> S3 | docgen bucket/file URLs | AWS-compatible credentials | SDK behavior; errors propagated |
| API <-> Redis | task notification pub/sub/SSE | password/settings, optional | ephemeral pub/sub |
| API -> Wildberries | Documents list/download endpoints | token from `seller_account`; aiohttp timeout not explicit | no retry; PDF/ZIP parse |

Входящих WMS HTTP routes в этом сервисе нет. Связь WMS -> 1CRoutingAPI по коду не установлена. Других internal services, кроме external docgen worker через RabbitMQ, не идентифицировано.

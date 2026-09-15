# Текущее состояние

`1CRoutingAPI` — FastAPI integration/warehouse service. Он принимает выгрузки документов 1С, обслуживает операции старого складского контура, резервы и отгрузки, возвраты, комплектацию/пересортицу, товары, стикеры и документы Wildberries. Точка запуска — `main.py`.

Основные вызывающие системы по коду: 1С (входящие `*/update`), складской/операторский frontend (CRUD и операционные endpoint), генератор документов через RabbitMQ. Прямого доказательства конкретных экранов frontend нет.

Подсистемы: HTTP API; service/repository; PostgreSQL/`asyncpg`; исходящий Basic Auth HTTP-клиент 1С; WMS receipt bridge; RabbitMQ-задачи стикеров; S3; Redis/SSE; Wildberries Documents API; metrics/rate-limit middleware.

Legacy-признаки: deprecated `POST /api/shipment_of_goods/update`; прямой доступ к общим `public.*` таблицам; зависимость от DB triggers, DDL которых отсутствует; синхронные вызовы 1С после commit; смешение integration и warehouse контуров.

Отключению мешают входящие выгрузки 1С, исходящие `ass_disass/`, `goods_resorting/`, `goods_return/`, `inc_invoice/`, `commission_sales_fbo/`, резервы/FBS/FBO, возвраты по `srid`, документы WB, стикеры и общая БД.

## Краткая схема взаимодействий

```text
1С / Frontend / внутренние клиенты
  -> 1CRoutingAPI
       -> PostgreSQL (public + wms)
       -> 1С HTTP Basic Auth
       -> WMS HTTP /api/movements
       -> RabbitMQ -> docgen worker -> RabbitMQ
       -> S3 + Redis/SSE
       -> Wildberries Documents API
```

Ограничения: открытый CORS; auth к router не применён; нет общего `operation_id`/idempotency key/outbox; неполная схема БД; почти нет tests business logic.

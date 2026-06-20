# Пробелы API

- Авторизация не применяется; закомментированные `Depends(verify_service_token)` не защищают routes.
- Sticker, local barcode, monitoring и DELETE container routes без `response_model`.
- `GET /docs/get_docs` возвращает `List[Dict]`, то есть неформальный внутренний контракт.
- Многие repositories возвращают error-модель со `status=422`, но decorator оставляет HTTP 200/201.
- CORS `allow_origins=["*"]` вместе с credentials — чрезмерно широкая граница.
- Write routes не принимают idempotency key; повтор может создать движения/внешние документы.
- Router часто переводит exception в generic 500/422; WMS partial success отражается только строкой `details`, FBO/1С partial success может вообще не отражаться.
- `POST get_historical_stocks` является read-operation, но назван/смоделирован как POST.
- Deprecated shipment update остаётся активным рядом с новыми составными endpoint.
- Бизнес-логика ожидания результата и внешних вызовов находится в service/repository; границы недостаточно явны.

## Кандидаты для Orchestrated Saga

1. Receipt 1С -> local DB -> WMS movements -> marker.
2. Incoming return -> local DB -> 1С goods return.
3. Incoming receipt -> local DB -> 1С invoice.
4. Kit/resorting -> DB-side operation -> 1С.
5. FBO shipment/reserve update -> DB -> 1С commission sales.

Frontend-код отсутствует, поэтому утверждать, что frontend сам вызывает два микросервиса, нельзя. Подтверждён только server-side вызов WMS и разделённые reserve/shipment endpoint, которые frontend может комбинировать.

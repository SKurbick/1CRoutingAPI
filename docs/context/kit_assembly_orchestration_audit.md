# Аудит операции комплектации для Saga/Orchestration

Объект аудита: `POST /api/warehouse_and_balances/assembly_or_disassembly_metawild`.

Ключевой вывод: endpoint действительно выглядит как основной endpoint комплектации/разукомплектации старой складской схемы, но сейчас это небезопасный контракт для Saga/Orchestration: нет идемпотентности, нет bounded timeout, нет подтверждаемого статуса 1С, а фактическая мутация остатков скрыта в DB-side механизме, DDL которого отсутствует в репозитории.

## A. Найденные endpoint'ы

### POST `/api/warehouse_and_balances/assembly_or_disassembly_metawild`

- Файл: `app/api/v1/endpoints/warehouse_and_balances.py`
- Router: `APIRouter(prefix="/warehouse_and_balances", tags=["Склады и остатки"])`
- Handler: `assembly_or_disassembly_metawild`
- Request schema: `AssemblyOrDisassemblyMetawildData`
- Response schema: `AssemblyMetawildResponse`
- HTTP status в decorator: `201 Created`
- Назначение: создать операцию сборки/разборки metawild-комплекта.

Required body fields:

- `author: str`
- `warehouse_id: int`
- `metawild: str`
- `count: int`
- `operation_type: Literal["assembly", "disassembly"]`

Optional body fields:

- Явных optional fields нет.
- Модель использует `ConfigDict(extra='allow')`, но публичный контракт дополнительных полей не описывает.

Response fields:

- `product_id: str`
- `operation_status: str`
- `code_status: int`
- `error_message: Optional[str]`

### GET `/api/inventory_transactions/get_kit_operations`

- Файл: `app/api/v1/endpoints/inventory_transactions.py`
- Handler: `get_kit_operations`
- Request: query params `date_from`, `date_to`
- Response schema: `List[KitOperationsGroupData] | InventoryTransactionsResponse`
- Назначение: дата-диапазонная история строк `kit_operations`.

Required query params:

- `date_from`
- `date_to`

Если один из параметров не передан, endpoint возвращает HTTP `400`.

### GET `/api/inventory_transactions/group_data`

- Файл: `app/api/v1/endpoints/inventory_transactions.py`
- Handler: `group_data`
- Request: query params `date_from`, `date_to`
- Response schema: `List[ITGroupData] | InventoryTransactionsResponse`
- Назначение: агрегированный отчет по `inventory_transactions`.
- Kit-related движения попадают в колонку `"Участие в сборке/разборе"` через `transaction_type IN ('kit_disassembly', 'kit_assembly', 'kit_result')`.

### GET `/api/goods_information/get_metawilds_data`

- Файл: `app/api/v1/endpoints/goods_information.py`
- Handler: `get_metawilds_data`
- Request: без параметров
- Response schema: `List[MetawildsData]`
- Назначение: вернуть активные комплекты/metawilds.
- SQL: `SELECT * FROM products WHERE is_kit = TRUE and is_active = TRUE;`

Response item:

- `id: str`
- `name: str`
- `kit_components: Dict[str, int]`

### GET `/api/goods_information/get_all_products_data`

- Файл: `app/api/v1/endpoints/goods_information.py`
- Handler: `get_all_products_data`
- Response schema: `List[AllProductsData]`
- Назначение: вернуть активные товары, включая обычные товары и комплекты.

### POST `/api/goods_information/add_product`

- Файл: `app/api/v1/endpoints/goods_information.py`
- Handler: `add_product`
- Request schema: `List[AllProductsData]`
- Response schema: `GoodsResponse`
- Назначение: создать товары/комплекты в `products`, включая `kit_components`.
- Это endpoint изменения состава товара/комплекта.

### Смежные endpoint'ы остатков

`GET /api/warehouse_and_balances/get_all_product_current_balances`:

- Читает `current_balances`.
- Основной endpoint комплектации его не вызывает.

`POST /api/warehouse_and_balances/product_quantity_check`:

- Проверяет ожидаемый остаток по данным `get_all_product_current_balances`.
- Основной endpoint комплектации его не вызывает.

## B. Главный endpoint для orchestration

Главный существующий endpoint: `POST /api/warehouse_and_balances/assembly_or_disassembly_metawild`.

Что он делает:

1. Принимает команду assembly/disassembly.
2. Вставляет строку в `kit_operations`.
3. Синхронно ждёт, пока `kit_operations.status` перестанет быть `pending` или `processing`.
4. Возвращает локальный результат из `kit_operations`.
5. Если repository вернул `code_status == 201`, service читает `products.kit_components`.
6. Service формирует payload для 1С и отправляет `POST {ONE_C_BASE_URL}ass_disass/`.

Можно ли безопасно вызывать извне как атомарную бизнес-операцию:

- Нет.
- Локальная DB-операция и вызов 1С не объединены транзакцией.
- Результат 1С не сохраняется.
- HTTP status 1С не проверяется через `raise_for_status()`.
- Повторный вызов того же body создаст новую строку `kit_operations`.

Бизнес-проверки в Python-коде:

- `operation_type` валидируется Pydantic как `"assembly"` или `"disassembly"`.
- Типы `author`, `warehouse_id`, `metawild`, `count` валидируются Pydantic.
- Проверки `count > 0`, существования `warehouse_id`, существования `metawild`, `is_kit = true`, достаточности остатка в Python-коде нет.
- Проверка остатков, если она существует, находится в неизвестном DB-side processor.

Ошибки:

- Pydantic validation error: HTTP `422`.
- Если repository поймал `asyncpg.PostgresError`, он возвращает `AssemblyMetawildResponse(code_status=422, operation_status="PostgresError", error_message=str(e))`; endpoint преобразует это в `HTTPException` с HTTP `422`.
- Если DB-side processor поставил `status = failed`, но SQL exception не было, endpoint всё равно вернет HTTP `201`, потому что `code_status` выставляется `201`.
- Если 1С вернула HTTP 4xx/5xx, endpoint всё равно может вернуть success: status и body 1С только печатаются.
- Если вызов 1С выбросил exception, endpoint может вернуть HTTP `500` уже после локальных DB side effects.
- Если polling завис в `pending/processing`, request висит без timeout и sleep.

Возможные HTTP-коды:

- `201`: decorator success; также возможен при business-failed `operation_status`.
- `422`: Pydantic validation или пойманный `PostgresError`.
- `500`: uncaught exceptions, например `IndexError` при отсутствии `products` строки в `kit_components_by_product_id`, сетевые ошибки 1С, другие runtime errors.
- `429`: для этого конкретного endpoint rate limiter не подключен.

Риск частичного выполнения:

- Да.
- Локальная DB-часть может выполниться, а 1С не выполниться.
- 1С может выполниться, а HTTP response клиенту не вернуться.
- Retry клиента может создать дубль.

## C. Request/response examples

### Комплектация

```bash
curl -X POST 'http://localhost:8302/api/warehouse_and_balances/assembly_or_disassembly_metawild' \
  -H 'Content-Type: application/json' \
  -d '{
    "metawild": "metawild_test",
    "count": 3,
    "author": "orchestrator",
    "warehouse_id": 1,
    "operation_type": "assembly"
  }'
```

### Разукомплектация

```bash
curl -X POST 'http://localhost:8302/api/warehouse_and_balances/assembly_or_disassembly_metawild' \
  -H 'Content-Type: application/json' \
  -d '{
    "metawild": "metawild_test",
    "count": 3,
    "author": "orchestrator",
    "warehouse_id": 1,
    "operation_type": "disassembly"
  }'
```

### Успешный локальный ответ

```json
{
  "product_id": "metawild_test",
  "operation_status": "completed",
  "code_status": 201,
  "error_message": null
}
```

### PostgreSQL error response

```json
{
  "detail": {
    "message": "...postgres error...",
    "details": "HTTPException"
  }
}
```

## D. Code path

### Endpoint/router

- File: `app/api/v1/endpoints/warehouse_and_balances.py`
- Function: `assembly_or_disassembly_metawild`
- Action: receives `AssemblyOrDisassemblyMetawildData`, calls `WarehouseAndBalancesService.assembly_or_disassembly_metawild`.
- If `result.code_status >= 400`, raises `HTTPException(status_code=result.code_status)`.

### Service/use case

- File: `app/service/warehouse_and_balances.py`
- Class: `WarehouseAndBalancesService`
- Function: `assembly_or_disassembly_metawild`

Behavior:

1. Calls repository.
2. If `result.code_status == 201`, reads kit components by `data.metawild`.
3. Mutates Pydantic model with `data.kit_komponents = kit_components`.
4. Dumps body excluding `warehouse_id`.
5. Converts `kit_komponents` dict to list of `{product_id, quantity}`.
6. Calls 1С client.
7. Ignores 1С response value.

### Repository

- File: `app/database/repositories/warehouse_and_balances.py`
- Class: `WarehouseAndBalancesRepository`
- Function: `assembly_or_disassembly_metawild`

SQL:

```sql
INSERT INTO kit_operations
    (warehouse_id, kit_product_id, operation_type, quantity, author)
VALUES
    ($1, $2, $3, $4, $5)
RETURNING id;
```

Then loop:

```sql
SELECT kit_product_id AS product_id, status AS operation_status, error_message
FROM kit_operations
WHERE id = $1;
```

Loop exits when `operation_status NOT IN ('pending', 'processing')`.

### Kit composition lookup

- File: `app/database/repositories/warehouse_and_balances.py`
- Function: `kit_components_by_product_id`

SQL:

```sql
SELECT kit_components FROM products WHERE id = $1;
```

The function parses `result[0]['kit_components']` as JSON. If product row is missing, `IndexError` is not caught.

### 1С HTTP client

- File: `app/infrastructure/ONE_C/routing.py`
- Class: `ONECRouting`
- Function: `assembly_or_disassembly_metawild`

HTTP:

- Method: `POST`
- URL: `ONE_C_BASE_URL + "ass_disass/"`
- Auth: Basic Auth using `ONE_C_LOGIN` and `ONE_C_PASSWORD`
- Timeout: no explicit timeout
- Response handling: prints `response.status` and body text, returns body text.
- No `raise_for_status`.
- No retry.
- No persistence of response.

## E. DB tables and side effects

Production DDL for the relevant tables/views/triggers/functions is not present in the repository. The fields below are inferred from application SQL.

### `public.kit_operations`

Read/write in main operation.

Inserted fields:

- `warehouse_id`
- `kit_product_id`
- `operation_type`
- `quantity`
- `author`

Read fields:

- `id`
- `kit_product_id`
- `warehouse_id`
- `operation_type`
- `quantity`
- `status`
- `error_message`
- `author`
- `created_at`

Records created on success:

- One command row in `kit_operations`.

Records created on error:

- If insert fails, repository returns error response and no row should be created.
- If DB-side processor later marks operation failed, row remains in `kit_operations` with final status and `error_message`.

Unique constraints:

- Not confirmed.
- No idempotency unique key is visible in code.

Foreign keys:

- Not confirmed.

Triggers:

- Not confirmed.
- Python code expects some DB-side mechanism to change `status` from `pending/processing`.

### `public.products`

Read by main operation to get composition.

Used fields:

- `id`
- `name`
- `is_kit`
- `share_of_kit`
- `kit_components`
- `photo_link`
- `is_active`

Modified by `POST /api/goods_information/add_product`, not by main assembly endpoint.

Composition:

- Stored in `products.kit_components`.
- Parsed as JSON dict, example: `{"testwild": 2, "testwild2": 1}`.

Unique constraints/FK/triggers:

- Not confirmed by repository DDL.
- `migrations/return_to_supplier.sql` references `public.products(id)`, implying `products.id` is a referenced key in production.

### `public.inventory_transactions`

Main endpoint does not directly write it.

Related report reads it:

- `transaction_type IN ('kit_disassembly', 'kit_assembly', 'kit_result')`.

Used fields in reports:

- `product_id`
- `quantity`
- `warehouse_id`
- `transaction_type`
- `delivery_type`
- `document_guid`
- `created_at`
- `status_id`
- `author`
- `correction_comment`

Whether assembly/disassembly creates rows here:

- Not confirmed in Python code.
- Likely done by unknown DB-side processor if old stock schema is implemented through triggers/functions/workers.

### `public.current_balances`

Read by `get_all_product_current_balances`.

Fields:

- `product_id`
- `warehouse_id`
- `physical_quantity`
- `reserved_quantity`
- `available_quantity`

Main endpoint does not call it.

It may be a table, view, or materialized view. Not confirmed.

### `public.product_availability`

Read by `get_valid_stock_data`, which is commented out at API level.

Fields:

- `product_id`
- `name`
- `is_kit`
- `available_stock`
- `components_info`

Main endpoint does not call it.

### `public.warehouses`

Read by `get_warehouses`.

Fields:

- `id`
- `name`
- `address`

Main endpoint stores `warehouse_id` in `kit_operations`, but Python code does not explicitly validate it.

## F. Transaction behavior

Application-level transaction:

- No explicit `async with conn.transaction()` in `WarehouseAndBalancesRepository.assembly_or_disassembly_metawild`.
- Insert is a single PostgreSQL statement.
- Polling is done after insert.
- Kit composition lookup is a separate query.
- 1С call happens after repository returns.

Commit:

- For the Python code, commit of insert is handled by asyncpg/PostgreSQL statement behavior, not an explicit transaction block.

Rollback:

- No explicit rollback block.
- If insert statement fails, PostgreSQL rejects it and repository returns `code_status=422`.
- If failure occurs after insert, local DB changes may remain.

External calls inside transaction:

- No explicit DB transaction wraps the 1С call.

Can endpoint return error with saved changes:

- Yes. Example: local DB operation finished, then 1С network exception causes HTTP 500.

Can endpoint return success while external part failed:

- Yes. If 1С returns HTTP 4xx/5xx without network exception, code only prints status/body and returns local success.

## G. Idempotency status

Current status: no idempotency.

Endpoint does not accept:

- `operation_id`
- `idempotency_key`
- `external_id`
- `saga_id`

Retry behavior:

- Repeating the same request creates a new `kit_operations` row.
- Duplicate protection is not visible in code.

Possible duplicate detection today:

- Only heuristic: same `kit_product_id`, `warehouse_id`, `operation_type`, `quantity`, `author`, close `created_at`.
- This is not safe for business idempotency.

Status lookup:

- No endpoint by `operation_id`.
- Only `GET /api/inventory_transactions/get_kit_operations?date_from=...&date_to=...`.
- Main endpoint does not return `kit_operations.id`.

## H. Compensation possibilities

Can assembly be rolled back by disassembly:

- Only approximately.
- It would be a new independent operation, not an exact rollback.

Needed data:

- `metawild`
- `count`
- `warehouse_id`
- `author`
- original `operation_type`
- preferably original kit composition snapshot

Can compensate by `operation_id` only:

- No.
- Existing endpoint does not accept operation id and main response does not expose `kit_operations.id`.

Risks:

- If `products.kit_components` changed after original operation, reverse operation may use a different composition.
- No party/batch/location/container constraints are represented.
- No user authorization context is represented except free-form `author`.
- No check that the reverse operation corresponds to a previous operation.
- No idempotency for compensation.

## I. Risks for orchestration

- Local DB and 1С can diverge.
- Retry can double-write stock effects.
- Unknown DB-side processor owns actual stock mutation.
- No timeout/backoff in polling loop.
- No `SELECT FOR UPDATE` or row lock visible in Python code.
- No explicit sufficient-stock check in Python code.
- Unknown whether stock can go negative.
- `operation_status` is not mapped to HTTP error.
- 1С result is not persisted or interpreted.
- No operation status endpoint by orchestrator key.
- No operation id in outbound 1С payload.
- `warehouse_id` is excluded from 1С payload.
- Component quantities sent to 1С are per-kit quantities from `products.kit_components`; code does not multiply them by `count`.
- No versioned kit composition.

## J. What to improve for safer orchestration

- Add an internal authenticated endpoint for orchestrator.
- Accept `operation_id`, `saga_id`, `idempotency_key`.
- Store canonical request hash.
- Add unique constraint on idempotency key.
- Return existing result for same key + same request hash.
- Reject same key + different request hash.
- Return local `kit_operations.id`.
- Add status endpoint: `GET /internal/operations/{operation_id}`.
- Add explicit operation ledger statuses:
  - `LOCAL_PENDING`
  - `LOCAL_COMPLETED`
  - `ONE_C_PENDING`
  - `ONE_C_SENT`
  - `COMPLETED`
  - `FAILED`
  - `UNKNOWN`
  - `COMPENSATING`
  - `COMPENSATED`
- Add bounded polling with sleep and timeout.
- Validate `count > 0`.
- Validate `warehouse_id`.
- Validate `metawild` exists and `is_kit = true`.
- Validate `kit_components` is non-empty.
- Snapshot kit composition in operation row.
- Make stock mutation explicit or document production trigger/function.
- Add row-level locks in the actual stock mutation path.
- Persist 1С dispatch attempts and responses.
- Check HTTP status and business response from 1С.
- Add retry/outbox for 1С.
- Include stable external `operation_id` in 1С payload.
- Add idempotent compensation endpoint.
- Add tests for concurrent assembly/disassembly and duplicate retries.

## K. Minimal payload for future orchestrator

Current minimal payload for existing endpoint:

```json
{
  "metawild": "metawild_test",
  "count": 3,
  "author": "orchestrator",
  "warehouse_id": 1,
  "operation_type": "assembly"
}
```

Recommended safer payload:

```json
{
  "operation_id": "uuid-from-orchestrator",
  "saga_id": "uuid-from-orchestrator",
  "idempotency_key": "1crouting-kit-assembly-uuid",
  "metawild": "metawild_test",
  "count": 3,
  "warehouse_id": 1,
  "operation_type": "assembly",
  "author": "orchestrator",
  "expected_kit_components": {
    "testwild": 2,
    "testwild2": 1
  }
}
```

## L. Open questions / manual checks

- What is the production DDL for `kit_operations`?
- What is the production DDL for `inventory_transactions`?
- Is `current_balances` a table, view, or materialized view?
- What trigger/function/worker changes `kit_operations.status`?
- What are all possible final statuses of `kit_operations.status`?
- Which final statuses mean business success?
- Does the DB-side processor create `inventory_transactions` rows for assembly/disassembly?
- What are the exact signs for component write-off and kit receipt?
- Can old-schema stock go negative?
- Are rows locked during stock mutation?
- Are there unique constraints preventing duplicate kit operations?
- Does 1С support external operation id, idempotency, status lookup, or cancel/reversal?
- Should `warehouse_id` be sent to 1С? Current code excludes it.
- Should component quantities in 1С payload be per-kit or multiplied by `count`?
- Is kit composition allowed to change while operations are pending?

## Auth, headers, and middleware

Authorization:

- Security helpers exist in `app/dependencies/security.py`.
- The relevant routers do not attach `verify_service_token` or `verify_token`.
- No auth header is required for the discovered endpoints.

Headers:

- Required request header: `Content-Type: application/json` for POST body.
- No required `X-Service-Token` on these routes.
- `MetricsMiddleware` adds response header `X-Response-Time`.

User/author:

- `author` comes from request body.
- No token-derived user is used.

Correlation/request id:

- No request/correlation id middleware was found.

Middleware:

- `MetricsMiddleware` records method/path/duration/status.
- `SlowAPIMiddleware` is enabled.
- CORS allows all origins, methods, and headers.

## External dependencies

Operation-specific dependency:

- 1С HTTP endpoint: `POST {ONE_C_BASE_URL}ass_disass/`
- Auth: HTTP Basic using `ONE_C_LOGIN` and `ONE_C_PASSWORD`.
- Called after local DB flow returns `code_status == 201`.
- No explicit timeout.
- No retry.
- No response validation.
- Response body is printed and ignored.

Application startup dependencies:

- PostgreSQL pool.
- RabbitMQ connection/FastStream, depending on `CONSUMERS_START`.
- Redis if `REDIS_ENABLED=True`.
- S3 storage manager.

The assembly endpoint itself does not publish RabbitMQ messages, use Redis, call WMS, Celery, cron, or task queue.

## Environment/config

Relevant settings from `app/dependencies/config.py`:

- `APP_NAME`
- `APP_IP_ADDRESS`
- `APP_PORT`
- `INITIAL_SERVICE_TOKEN`
- `TOKEN_HEADER`
- `CONSUMERS_START`
- `POSTGRES_USER`
- `POSTGRES_PASSWORD`
- `POSTGRES_DB`
- `POSTGRES_HOST`
- `POSTGRES_PORT`
- `POSTGRES_MIN_CONN_COUNT`
- `POSTGRES_MAX_CONN_COUNT`
- `POSTGRES_MAX_CONN_INACTIVE_LIFETIME`
- `ONE_C_LOGIN`
- `ONE_C_PASSWORD`
- `ONE_C_BASE_URL`
- `WMS_API_URL_MOVEMENTS`
- RabbitMQ settings
- Redis settings
- S3 settings

`WMS_API_URL_MOVEMENTS` is present but not used by assembly/disassembly flow.

## Docker / local run

Dockerfile:

- Base image: `python:3.12-slim`
- Installs requirements.
- Runs `python main.py`.

docker-compose:

- Service `1c_routing_api`
- Port mapping: `8302:8002`
- Service `rabbitmq`
- RabbitMQ management and AMQP ports use env values.

API local URL with compose:

- `http://localhost:8302`

Healthcheck endpoint:

- `GET /api/health`

Migrations:

- Repository contains `migrations/return_to_supplier.sql`.
- No migration runner configuration was found.
- Production DDL for kit assembly tables/triggers is absent.

## OpenAPI

Local Swagger UI:

- `http://localhost:8302/docs`

OpenAPI JSON:

- `http://localhost:8302/openapi.json`

Relevant schema fragment conceptually:

```json
{
  "path": "/api/warehouse_and_balances/assembly_or_disassembly_metawild",
  "method": "post",
  "requestBody": {
    "author": "string",
    "warehouse_id": "integer",
    "metawild": "string",
    "count": "integer",
    "operation_type": "assembly | disassembly"
  },
  "response": {
    "product_id": "string",
    "operation_status": "string",
    "code_status": "integer",
    "error_message": "string | null"
  }
}
```

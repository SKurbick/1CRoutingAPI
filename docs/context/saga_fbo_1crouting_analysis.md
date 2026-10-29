# Анализ Saga participant: FBO shipment в 1CRoutingAPI

Дата анализа: 2026-06-20. Базовый commit: `8d0661b4eed96f6b52eb841aa60f0f34ca518926`.

Объект анализа: `POST /api/shipment_of_goods/shipment_with_reserve_updating`. Код не изменялся. Выводы основаны на repository-коде; DDL `product_reserves`/`shipment_of_goods` и production triggers/functions в репозитории отсутствуют, поэтому свойства ограничений, FK и скрытых DB-side effects отмечены как неизвестные.

## 1. Точка входа и контракт

### Регистрация и реализация

- Итоговый path образуется из `/api` в `main.py:110`, router prefix `/shipment_of_goods` в `app/api/v1/endpoints/shipment_of_goods.py:13` и path `/shipment_with_reserve_updating` в строке 16.
- Router: `app/api/v1/endpoints/shipment_of_goods.py:13-23`.
- Endpoint-функция: `shipment_with_reserve_updating`, строки 17-23.
- DI: `get_shipment_of_goods_service` -> `ShipmentOfGoodsRepository`, `app/dependencies/shipment_of_goods.py:9-19`.
- Request body: `List[ShipmentWithReserveUpdating]`, endpoint строки 17-20.
- Response: `ShipmentOfGoodsResponse`, decorator строка 16; модель `app/models/shipment_of_goods.py:28-32`.
- Декларируемый успешный HTTP status: 201, endpoint строка 16.

### Авторизация

Авторизации нет. Router не содержит `dependencies=[Depends(...)]`, endpoint не зависит от `verify_service_token` или `verify_token` (`app/api/v1/endpoints/shipment_of_goods.py:13-23`). Реализации обеих проверок существуют в `app/dependencies/security.py:21-42`, но не подключены. `main.py:110` включает router без dependencies.

### Параметры request

`ShipmentWithReserveUpdating` наследует все поля `ShipmentOfGoodsUpdate` и добавляет `is_fulfilled` (`app/models/shipment_of_goods.py:35-45,157-158`).

| Параметр | Где | Обязателен | Назначение/ограничение |
|---|---|---:|---|
| `delivery_type` | query | да | Enum `ФБС`/`ФБО`, строки 23-25; определяет только вызов 1С в service |
| body | JSON array | да | пустой массив валиден |
| `author` | item | да | сохраняется в shipment |
| `supply_id` | item | да | поставка; сохраняется и передаётся в 1С |
| `product_id` | item | да | товар; сохраняется и передаётся как `wild_code` |
| `warehouse_id` | item | да | ID старого склада; только shipment row |
| `delivery_type` | item | да | произвольная строка, сохраняется в БД; не обязана совпадать с query |
| `wb_warehouse` | item | нет | склад WB, default `null` |
| `account` | item | да | seller account; группировка payload 1С |
| `quantity` | item | да | прибавляется к `product_reserves.shipped`; нет `gt=0` |
| `shipment_date` | item | нет | дата отгрузки, default `null` |
| `product_reserves_id` | item | нет по schema | фактически ключ обновляемого резерва; default `null` |
| `is_fulfilled` | item | да | полностью перезаписывает флаг резерва |

Критическое расхождение контракта: `product_reserves_id` объявлен optional (`app/models/shipment_of_goods.py:45`), хотя SQL использует его как `WHERE product_reserves.id=$1` (`app/database/repositories/shipment_of_goods.py:199-204,221-225`).

### Пример фактического request

```http
POST /api/shipment_of_goods/shipment_with_reserve_updating?delivery_type=ФБО
Content-Type: application/json

[
  {
    "author": "warehouse.operator",
    "supply_id": "WB-GI-166715280",
    "product_id": "wild123",
    "warehouse_id": 1,
    "delivery_type": "ФБО",
    "wb_warehouse": "Коледино",
    "account": "seller-account",
    "quantity": 5,
    "shipment_date": "2026-06-20",
    "product_reserves_id": 11,
    "is_fulfilled": true
  }
]
```

Поля подтверждены моделью; значения иллюстративны и не являются production data. Репозиторий содержит близкий пример для базовой shipment schema в `app/models/shipment_of_goods.py:7-20`.

### Успешный response

Repository возвращает (`app/database/repositories/shipment_of_goods.py:253-256`):

```json
{
  "status": 201,
  "message": "Успешно обновлены резервы и созданы записи об отгрузке",
  "details": null,
  "data": null
}
```

Response не содержит shipment ID, reserve ID, supply ID, operation ID или результат 1С.

### Фактические HTTP-коды

- `201`: успешная локальная транзакция; также DB error, преобразованная repository в body `status=422`, потому что endpoint не вызывает `HTTPException` (`endpoint:16-23`, repository:258-263).
- `422`: FastAPI/Pydantic validation error: отсутствующие required fields, неверный query enum, неверные типы.
- `500`: необработанная ошибка endpoint/DI/serialization или исключение, не являющееся `asyncpg.PostgresError` и не подавленное service. Исключения 1С подавляются (`service:34-41`), поэтому сами по себе не дают 500.

HTTP 400/404/409 этим handler явно не формируются. Указанное в response body поле `status` не равно HTTP status.

### Идентификаторы

- `product_reserves_id`: технический PK резерва, основной local key.
- `supply_id`: бизнес-ID поставки, используется в shipment и payload 1С.
- `product_id`: товар/`wild_code` 1С.
- `warehouse_id`: старый склад; в 1С payload не входит.
- `account`: seller account; для 1С сопоставляется с INN.
- Отдельных `shipment_id`, document ID, operation ID, saga ID или request ID в контракте нет.

## 2. Бизнес-смысл endpoint

Обычным языком: для каждого элемента request сервис увеличивает уже отгруженное количество конкретного резерва, устанавливает переданный признак исполнения и создаёт строку истории/факта отгрузки. Для query `delivery_type=ФБО` после commit формируется агрегированный payload и синхронно отправляется в 1С как комиссионная продажа FBO.

1. `shipment_of_goods` — таблица фактов отгрузки: author, supply, product, warehouse, delivery type, account, quantity, date и ссылка на reserve (`repository:207-212,227-241`).
2. Обновляется строка `product_reserves` с `id == product_reserves_id` (`repository:199-204`).
3. Резерв не создаётся, не удаляется и не уменьшается физически. Увеличивается accumulator `shipped` на `quantity`; `is_fulfilled` заменяется входным значением. Доступный резерв в отчёте вычисляется как `ordered - shipped` (`repository:458-465`).
4. Да, код оформляет shipment insert и reserve update как одну DB-транзакцию (`repository:243-251`).
5. Один endpoint нужен для атомарности этих двух local writes; это прямо заявлено docstring (`repository:195-197`). Историческая причина не документирована.
6. Endpoint технически принимает и `ФБС`, и `ФБО`: query — `DeliveryType`, endpoint строки 18-20. Специальный FBS endpoint существует отдельно (`endpoint:41-61`), но запрета FBS здесь нет.
7. FBO определяется **только query-параметром** `delivery_type` в service (`app/service/shipment_of_goods.py:28-33`). Body `item.delivery_type` сохраняется отдельно и не проверяется на совпадение.
8. Отдельная FBO-ветка есть: `case DeliveryType.FBO`, затем 1С (`service:31-39`). DB-ветка для FBO/FBS одинаковая.

Следствие: query `ФБО` + body `ФБС` всё равно вызовет 1С, сохранив shipment как ФБС; query `ФБС` + body `ФБО` сохранит FBO shipment без отправки в 1С.

## 3. Полная цепочка вызовов

1. FastAPI router принимает array и required query enum (`endpoint:16-20`).
2. DI берёт pool из `request.app.state.pool`, создаёт repository и service (`app/dependencies/shipment_of_goods.py:9-19`).
3. Handler вызывает `ShipmentOfGoodsService.shipment_with_reserve_updating` (`endpoint:22`).
4. Service вызывает одноимённый repository (`service:28-30`).
5. Repository готовит для каждого item reserve update и shipment insert (`repository:198-241`).
6. Открывает connection и transaction (`repository:243-245`).
7. Сначала выполняет `executemany UPDATE product_reserves` (`repository:246-249`).
8. Затем `executemany INSERT shipment_of_goods` (`repository:250-251`).
9. Возвращает response внутри transaction block; commit происходит при успешном выходе из `conn.transaction()` и connection context до возврата coroutine вызывающему service (`repository:243-256`).
10. Service проверяет только `result.status == 201` (`service:31`).
11. Если query enum FBO, преобразует items: group by `account` -> `supply_id`, sum quantity by product (`app/infrastructure/ONE_C/routing.py:74-113`).
12. Выполняет synchronous HTTP POST `${ONE_C_BASE_URL}commission_sales_fbo/`, Basic Auth, timeout 60 seconds (`routing.py:65-72`).
13. Любое exception 1С печатается и подавляется (`service:34-41`). HTTP 4xx/5xx не вызывает exception: `raise_for_status()` отсутствует.
14. Service возвращает исходный local DB response (`service:42`), handler отдаёт HTTP 201.

Не обнаружены в этой цепочке: ORM/hooks (ORM нет), RabbitMQ publisher, Celery, cron/job, WMS HTTP, Redis/SSE, S3, callback или integration log. Поиск по repository, broker и service не выявил indirect publish. SQL DDL `product_reserves`/`shipment_of_goods`, trigger definitions и functions отсутствуют; единственная migration `migrations/return_to_supplier.sql` относится к возвратам поставщику. Поэтому дополнительные trigger side effects исключить нельзя.

```text
ROUTING-FBO-1  FastAPI validation
-> ROUTING-FBO-2  local DB transaction begins
-> ROUTING-FBO-3  product_reserves.shipped += quantity; is_fulfilled = input
-> ROUTING-FBO-4  INSERT shipment_of_goods
-> ROUTING-FBO-5  COMMIT
-> ROUTING-FBO-6  if query delivery_type == ФБО: aggregate account/supply/product
-> ROUTING-FBO-7  synchronous POST 1С commission_sales_fbo/
-> ROUTING-FBO-8  suppress 1С exception / ignore HTTP status
-> ROUTING-FBO-9  return local result as HTTP 201
```

## 4. Изменения состояния

| Объект | Изменение | Бизнес-ID | Unique/дубликат |
|---|---|---|---|
| `product_reserves` | `shipped = shipped + quantity`; `is_fulfilled = input` | PK `product_reserves_id` | PK предполагается SQL usage, DDL отсутствует; повтор увеличивает снова |
| `shipment_of_goods` | одна insert-строка на каждый item | supply+product+reserve/date не формализованы как key | unique constraint неизвестен; код duplicate check не делает |
| 1С commission sale | aggregated POST by account/supply/product | account, mapped INN, supply_id, wild_code | external operation ID отсутствует; duplicate policy 1С неизвестна |

`shipment_of_goods` fields: `author`, `supply_id`, `product_id`, `warehouse_id`, body `delivery_type`, `wb_warehouse`, `account`, `quantity`, `shipment_date`, fixed `share_of_kit=false`, fixed `metawild=null`, `product_reserves_id` (`repository:207-212,227-241`).

Не создаются явно: stock movements, documents, status history, audit rows, integration request record, background task или broker message. Возможные DB triggers неизвестны.

Критические edge cases:

- `product_reserves_id=null` или несуществующий ID: UPDATE затронет 0 строк; row count не проверяется. Shipment insert всё равно выполняется. Если DB FK/NOT NULL не отклонит его, операция вернёт 201 с shipment без reserve change.
- Один reserve ID в нескольких items: `shipped` увеличится несколько раз, `is_fulfilled` примет значение последнего UPDATE.
- `quantity=0` или отрицательное значение принимается schema. Отрицательное значение уменьшит `shipped` и одновременно создаст shipment с отрицательным quantity, если DB CHECK отсутствует.
- Пустой array: оба списka пусты, SQL пропускается, возвращается 201 (`repository:246-256`). Для FBO затем в 1С отправляется пустой list.

## 5. Транзакционная граница

- Начало: `async with conn.transaction()` (`repository:245`).
- Порядок: все reserve updates, затем все shipment inserts (`repository:246-251`).
- Commit: автоматический после выхода из transaction context; service и 1С вызываются после завершения repository.
- Reserve update и shipment insert находятся в одной transaction.
- Внешних вызовов внутри transaction нет.
- Вызов 1С происходит после commit (`service:30-38`).

Сценарии:

- Shipment insert SQL fails после успешных UPDATE: PostgreSQL transaction rollback должна откатить оба действия.
- Reserve UPDATE не находит row: это не SQL exception; shipment может commit. Поэтому логически возможна «отгрузка создана, резерв не обновлён».
- «Резерв обновлён, shipment не создан» при обычной SQL error не должен commit благодаря transaction. Возможен только неизвестный trigger/commit anomaly, не подтверждённый кодом.
- DB committed, 1С exception/timeout: local changes остаются; endpoint всё равно 201, exception suppressed.
- 1С приняла request, frontend/orchestrator не получил response: local DB и 1С могут быть успешны, но caller outcome unknown. Retry небезопасен.
- 1С вернула HTTP 4xx/5xx: код читает text и считает вызов завершённым; endpoint возвращает local 201.

## 6. Идемпотентность

Текущая операция не идемпотентна.

1. Повтор создаёт новые `shipment_of_goods` rows, если неизвестный DB constraint не запретит.
2. `product_reserves.shipped` повторно увеличивается.
3. Для query FBO payload повторно отправляется в 1С.
4. Broker публикации нет.
5. Unique constraints для бизнес-ключа не представлены migrations/schema; код на них не опирается.
6. Проверки «уже выполнено» нет.
7. После timeout безопасно повторять нельзя.

Поиск не нашёл `saga_id`, request/transaction ID, idempotency key, shipment operation ID, external document ID, outbox/integration-request table. `product_reserves_id` идентифицирует reserve, но не request; `supply_id` не подходит, потому что одна supply содержит несколько products и может отгружаться частями.

### Минимальная схема

Рекомендуется отдельная owned table, например `saga_participant_operations`:

```text
operation_id UUID PRIMARY KEY
saga_id UUID NOT NULL
participant VARCHAR NOT NULL
idempotency_key VARCHAR NOT NULL UNIQUE
request_hash VARCHAR NOT NULL
status VARCHAR NOT NULL
request_payload JSONB NOT NULL
response_payload JSONB
shipment_ids BIGINT[]
reserve_ids BIGINT[]
one_c_status VARCHAR
one_c_attempts INTEGER
error_code VARCHAR
retryable BOOLEAN
created_at/completed_at/updated_at TIMESTAMPTZ
```

- `operation_id`: уникальный ID participant command, генерируется orchestrator и является основным unique key.
- `saga_id`: correlation, не обязательно unique: Saga может иметь несколько participant operations.
- `idempotency_key`: можно сделать равным `operation_id` либо unique `(participant, idempotency_key)`.
- Request hash обязателен. Same key + same canonical payload возвращает сохранённый status/response без повторных SQL/1С effects.
- Same key + different payload: HTTP 409 `IDEMPOTENCY_KEY_REUSED`.
- Operation record и local shipment/reserve writes должны фиксироваться в одной transaction.
- Для 1С нужен outbox/dispatch status. Не считать operation полностью завершённой до подтверждаемого результата 1С либо явно разделить `LOCAL_COMPLETED` и `ONE_C_*`.

## 7. Интеграция с 1С

- Да, для query `delivery_type=ФБО` выполняется synchronous HTTP POST (`service:31-39`, `routing.py:65-72`).
- Queue/background record нет.
- Basic Auth; timeout 60 seconds.
- Payload группируется по account и supply, quantities суммируются по product (`routing.py:79-113`).
- Если account отсутствует в `account_inn_map`, отправляется placeholder INN `000000000000` (`routing.py:88-90`).
- Response status печатается, body возвращается как text, но service его не анализирует.
- `raise_for_status`, retry, persistence attempts и result lookup отсутствуют.
- Exception подавляется; HTTP error status не считается exception.
- Повторная отправка возможна при любом повторе API.
- Поддержка 1С external operation ID и отмены не видна в контракте: payload не содержит operation/saga/idempotency ID.

Успешный endpoint response означает только `result.status==201` локального repository. Он **не доказывает**, что 1С приняла, провела или даже успешно обработала документ.

## 8. Ошибки и retry

| Ошибка | Причина | HTTP | Retryable | Outcome известен | Действие orchestrator |
|---|---|---:|---|---|---|
| Validation | bad/missing field/query enum | 422 | после исправления | да, writes не начаты | fail command |
| Empty array | валидный no-op | 201 | нет смысла | да, ничего не сделано; возможен пустой POST 1С | считать contract error у orchestrator |
| Missing reserve ID | null/nonexistent | 201 либо DB-dependent error | нет до status lookup | reserve update 0; shipment may exist | MANUAL/lookup; не blind retry |
| FK/NOT NULL/CHECK violation | production constraint | HTTP 201 + body `status=422` | зависит | transaction rollback ожидается | parse body; исправить mapping/payload |
| Transient PostgreSQL error | connection/deadlock/serialization | HTTP 201 body 422 либо 500 | да, только с idempotency | обычно rollback, но transport ambiguity остаётся | status lookup then retry |
| Unexpected local exception | code/DI | 500 | зависит | если transaction exception — rollback; caller не может доказать | lookup operation |
| 1С connect failure | network/DNS | 201 | да, но не повтором всей local command | local committed, 1С not reached likely | retry outbox dispatch only |
| 1С timeout | timeout after send | 201 | outcome-sensitive | нет: 1С могла принять | query/reconcile by external operation ID |
| 1С HTTP 4xx | contract/business rejection | 201 | обычно terminal | 1С response был, но discarded semantically | mark failed/manual; do not repeat local |
| 1С HTTP 5xx | temporary server error | 201 | external dispatch retry | local committed; remote likely failed, not guaranteed | retry idempotent 1С dispatch |
| Response lost | gateway/client timeout | none/timeout | только после lookup | неизвестен | GET operation; never blind retry |
| Query/body delivery mismatch | client contract error | 201 | terminal | wrong local/external branch committed | manual reconciliation |

Текущий response-loss сценарий: первый request увеличивает `shipped`, вставляет shipment и может отправить 1С. Повтор делает всё ещё раз. Риск — double shipped quantity, duplicate shipment и duplicate 1С document.

## 9. Проверка результата

Подходящего status method нет.

- `GET /api/shipment_of_goods/get_reserved_data` позволяет фильтровать `is_fulfilled`, `begin_date`, `delivery_type`, но не operation/saga/supply/reserve ID (`endpoint:113-120`; repository:538-576).
- `GET /summ_reserve_data` возвращает aggregate, не operation result (`endpoint:141-146`; repository:425-499).
- Нет active GET shipment by ID/supply. Закомментированный `get_shipment_data` не является route (`endpoint:148-160`).
- Repository не возвращает inserted shipment IDs.

Минимальный internal contract:

```http
GET /internal/operations/{operation_id}
```

```json
{
  "operation_id": "uuid",
  "saga_id": "uuid",
  "status": "LOCAL_COMPLETED|ONE_C_PENDING|COMPLETED|FAILED|UNKNOWN|COMPENSATED",
  "shipment_ids": [101],
  "affected_entities": {
    "reserve_ids": [11],
    "supply_ids": ["WB-GI-166715280"],
    "product_ids": ["wild123"]
  },
  "created_at": "...",
  "completed_at": "...",
  "error_code": null,
  "retryable": false,
  "response_payload": {"status": 201, "message": "..."}
}
```

Endpoint должен быть защищён service auth, возвращать 404 только если operation действительно не зарегистрирована, и различать `UNKNOWN` от `FAILED`.

## 10. Компенсация

Штатной компенсации нет: router/repository не имеют delete/storno shipment, decrement reserve, reverse document или cancel 1С endpoint.

Логический откат потребовал бы:

1. точно найти созданные этой operation shipment IDs;
2. заблокировать operation/reserve rows;
3. проверить, что последующие shipments/adjustments не сделали rollback unsafe;
4. создать append-only сторно shipment либо пометить исходные rows cancelled; физическое DELETE нежелательно;
5. атомарно уменьшить `product_reserves.shipped` на исходную quantity и корректно пересчитать `is_fulfilled`;
6. создать audit/compensation record с unique operation ID;
7. отменить/сторнировать commission document в 1С или создать reverse document — возможность и contract неизвестны;
8. сделать compensation idempotent.

Использовать отрицательный `quantity` через текущий endpoint как компенсацию небезопасно: это создаст новую «отгрузку» с отрицательным количеством, повторно вызовет 1С и не связывает reversal с original operation.

Автоматическая compensation сейчас небезопасна. До появления operation ledger, state/version checks и подтверждённого reversal contract 1С failure должен переводить Saga в `MANUAL_REVIEW`. Если участники Saga включают WMS и 1CRoutingAPI, этот endpoint из-за внешнего необратимого side effect 1С предпочтительно выполнять последним либо отделить 1С dispatch.

## 11. Пригодность endpoint для Saga

**Нужен отдельный internal endpoint для Saga.**

Причины:

- текущий endpoint не идемпотентен;
- не принимает/не сохраняет operation ID;
- не возвращает shipment IDs;
- отсутствует status lookup;
- local commit и 1С неатомарны;
- ошибки 1С скрываются;
- query/body delivery type могут расходиться;
- optional reserve ID и отсутствие row-count check допускают logical partial success;
- компенсации нет;
- HTTP codes не отражают body outcome.

Просто добавить header idempotency недостаточно, если сохранить synchronous untracked 1С call. Рекомендуемый internal endpoint должен регистрировать participant operation, атомарно выполнять local writes, а 1С отправлять через durable outbox или выделенный idempotent dispatch step. Если 1С нельзя сделать idempotent/компенсируемой, этот side effect должен выполняться последним.

## 12. Минимальные изменения Saga Participant

1. Новый authenticated `POST /internal/fbo-shipments` с `saga_id`, `operation_id`, `idempotency_key`, одним authoritative `delivery_type=ФБО` и required `product_reserves_id`.
2. Canonical request hash; 409 при reuse key с другим payload.
3. Operation ledger + unique operation/idempotency key.
4. `SELECT ... FOR UPDATE` reserves; проверить existence, product/supply/account/warehouse consistency, `quantity > 0`, `shipped + quantity <= ordered`, expected current version/status.
5. UPDATE с checked affected-row count; shipment INSERT `RETURNING id`.
6. Operation row, reserve updates, shipment rows и outbox event — одна local transaction.
7. Разделить statuses `LOCAL_PENDING`, `LOCAL_COMPLETED`, `ONE_C_PENDING`, `ONE_C_SENT`, `COMPLETED`, `FAILED`, `UNKNOWN`, `COMPENSATING`, `COMPENSATED`, `MANUAL_REVIEW`.
8. 1С payload должен включать stable external `operation_id`; retry только external dispatch, не local shipment.
9. Проверять HTTP status и business response 1С; сохранять sanitized response/attempts/timestamps.
10. Status GET и idempotent compensation endpoint.
11. Единый error format: `code`, `message`, `retryable`, `operation_id`, `details`; правильные 400/404/409/422/503/504.
12. Propagate correlation ID in HTTP/log/1С; structured logs without payload secrets.
13. Tests: duplicate same payload, same key different payload, missing reserve, concurrent operations on reserve, rollback insert failure, response loss, 1С timeout/4xx/5xx, outbox retry, compensation repeat.

## 13. Противоречия и пробелы источников

### Документация против кода

- `docs/context/api_map.md` и `business_rules.md` корректно указывают DB + FBO->1С, но не фиксируют отдельные query/body `delivery_type` и возможность их расхождения.
- `docs/context/write_operations_policy.md` корректно указывает no idempotency/compensation, но не описывает optional `product_reserves_id`, unchecked UPDATE и фактический HTTP 201 для repository body error.
- `docs/context/domain_model.md` объединяет `fbs_reserves`, `fbo_reserves`, `product_reserves`; конкретный endpoint работает только с `product_reserves` и `shipment_of_goods`.
- `docs/context/current_state.md` говорит о зависимости от DB triggers в общем. Для данного endpoint local reserve/shipment writes полностью видны в SQL; необходимость trigger для основной операции не подтверждена.
- `docs/context/saga_candidates.md` правильно описывает DB -> 1С, но не отмечает, что HTTP success не содержит результат 1С и exception подавляется.
- `docs/context/api_gap_analysis.md` говорит, что partial 1С success «может не отражаться»; для этого endpoint он гарантированно не отражается в response model.

### Недоступные подтверждения

- В migrations нет DDL `product_reserves` и `shipment_of_goods`; нельзя подтвердить PK/FK/unique/check/not-null/indexes.
- Trigger/function definitions для этих таблиц отсутствуют; production catalog/dump не предоставлен.
- Тестов shipment/reserve/FBO нет: единственный `tests/test_docs_parser.py` тестирует парсер документов.
- Frontend/WMS/1С contracts и tests находятся вне репозитория.
- Нельзя установить, существует ли 1С document uniqueness/cancellation/status query.

## 14. Итоговая карточка участника

### 1CRoutingAPI FBO Participant

- **Endpoint:** `POST /api/shipment_of_goods/shipment_with_reserve_updating?delivery_type=ФБО`
- **Request schema:** `List[ShipmentWithReserveUpdating]`
- **Response schema:** `ShipmentOfGoodsResponse`
- **Business operation key:** отсутствует; ближайший составной контекст — account+supply+product+reserve, но он не уникален для partial shipments
- **Existing idempotency:** отсутствует
- **Recommended idempotency key:** orchestrator-generated immutable `operation_id`/`idempotency_key`, unique per participant command
- **Transaction boundary:** all `product_reserves` UPDATEs + all `shipment_of_goods` INSERTs in one PostgreSQL transaction
- **Main side effects:** increment `shipped`, overwrite `is_fulfilled`, insert shipment rows
- **External side effects:** synchronous commission-sale POST to 1С after commit
- **1C integration:** Basic Auth, 60s timeout, no status validation, persistence, retry or external operation ID; exceptions suppressed
- **Retryable errors:** transient DB before confirmed commit; 1С network/5xx only as separate idempotent dispatch
- **Terminal errors:** invalid payload, missing/inconsistent reserve, insufficient quantity, 1С business rejection
- **Unknown-result errors:** lost API response; 1С timeout; connection loss around commit; untracked 1С response
- **Status check method:** отсутствует; рекомендуется `GET /internal/operations/{operation_id}`
- **Compensation method:** отсутствует; требуется idempotent storno + reserve restoration + 1С reversal
- **Safe automatic compensation:** нет, сейчас `MANUAL_REVIEW`
- **Recommended execution order:** после reversible WMS steps; 1С dispatch последним либо отдельным outbox step
- **Required code changes:** internal Saga contract, idempotency ledger/hash, row locks/validation, returning IDs, outbox, status GET, compensation, auth, correct HTTP/errors/correlation
- **Documentation/code conflicts:** неполно описаны dual delivery type, unchecked reserve update, HTTP/body status mismatch и suppressed 1С outcome
- **Open questions:** production DDL/triggers; reserve ownership; 1С idempotency/status/cancel contract; WMS compensation; допустимость partial shipment; authoritative operation key; final business owner of FBO process

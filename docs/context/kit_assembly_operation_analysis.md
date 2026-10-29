# Анализ операции комплектации / разукомплектации

## Краткое резюме

Объект анализа: `POST /api/warehouse_and_balances/assembly_or_disassembly_metawild`.

Операция принимает команду сборки/разборки metawild-комплекта, вставляет строку в `kit_operations`, синхронно ждёт, пока `kit_operations.status` перестанет быть `pending` или `processing`, затем при `code_status == 201` отправляет payload в 1С на `${ONE_C_BASE_URL}ass_disass/`.

Код Python не содержит SQL, который напрямую меняет остатки при этой операции. Изменение остатков подтверждается только косвенно: репозиторий ждёт изменения на стороне БД `kit_operations.status`, а отчёт `group_data` читает движения комплектации из `inventory_transactions.transaction_type IN ('kit_disassembly', 'kit_assembly', 'kit_result')`. DDL триггеров/функций для этого в репозитории отсутствуют.

Критичный вывод: сервис отправляет данные в 1С при `code_status == 201` независимо от фактического `operation_status`. Если обработчик на стороне БД вернул финальный статус ошибки, но SQL-запрос успешно отработал, 1С всё равно будет вызвана. Это следует из `WarehouseAndBalancesService.assembly_or_disassembly_metawild` и `WarehouseAndBalancesRepository.assembly_or_disassembly_metawild`.

## Точка входа / endpoint

- Регистрация router: `main.py:113` подключает `warehouse_and_balances_router` с prefix `/api`.
- Prefix router: `app/api/v1/endpoints/warehouse_and_balances.py` объявляет `APIRouter(prefix="/warehouse_and_balances")`.
- Endpoint: `app/api/v1/endpoints/warehouse_and_balances.py:71-84`.
- HTTP-метод: `POST`.
- Путь: `/api/warehouse_and_balances/assembly_or_disassembly_metawild`.
- Query-параметры: нет.
- Тело запроса: `AssemblyOrDisassemblyMetawildData`, передаётся через `Body(examples=[example_assembly_metawild_data])`.
- Тело ответа: `AssemblyMetawildResponse`.
- Заявленный HTTP-статус успешного ответа: `201`.
- Маппинг ошибок: endpoint поднимает `HTTPException` только если `result.code_status >= 400`; detail содержит `message=result.error_message` и `details="HTTPException"`.

## Схемы запроса/ответа

Источник: `app/models/warehouse_and_balances.py:119-134`.

Базовая схема запроса `AssemblyMetawild`:

```python
author: str
warehouse_id: int
metawild: str
count: int
```

Схема запроса `AssemblyOrDisassemblyMetawildData`:

```python
model_config = ConfigDict(extra='allow')
operation_type: Literal["assembly", "disassembly"]
```

`extra='allow'` важен, потому что service позже добавляет `data.kit_komponents`.

Схема ответа `AssemblyMetawildResponse`:

```python
product_id: str
operation_status: str
code_status: int
error_message: Optional[str] = None
```

Описание OpenAPI говорит: `operation_type = 'assembly'` означает собрать комплект из компонентов, `operation_type = 'disassembly'` означает разобрать комплект на компоненты (`app/models/warehouse_and_balances.py:37`).

Пример запроса в коде: `app/models/warehouse_and_balances.py:52-58`.

## Цепочка вызовов

1. `POST /api/warehouse_and_balances/assembly_or_disassembly_metawild` попадает в endpoint `assembly_or_disassembly_metawild` (`app/api/v1/endpoints/warehouse_and_balances.py:71-84`).
2. Endpoint вызывает `WarehouseAndBalancesService.assembly_or_disassembly_metawild(data)` (`app/api/v1/endpoints/warehouse_and_balances.py:77`).
3. Service вызывает `WarehouseAndBalancesRepository.assembly_or_disassembly_metawild(data)` (`app/service/warehouse_and_balances.py:45-46`).
4. Repository вставляет команду в `kit_operations`:

```sql
INSERT INTO kit_operations
(warehouse_id, kit_product_id, operation_type, quantity, author)
VALUES
($1, $2, $3, $4, $5)
RETURNING id;
```

Источник: `app/database/repositories/warehouse_and_balances.py:345-354`.

5. Repository в цикле читает ту же строку:

```sql
SELECT kit_product_id AS product_id, status AS operation_status, error_message
FROM kit_operations
WHERE id = $1;
```

Источник: `app/database/repositories/warehouse_and_balances.py:355-357`.

6. Цикл завершается, когда `operation_status NOT IN ('pending', 'processing')` (`app/database/repositories/warehouse_and_balances.py:361-365`).
7. Repository возвращает `AssemblyMetawildResponse(**check_status, code_status=201)` (`app/database/repositories/warehouse_and_balances.py:365`).
8. Если insert/select выбрасывает `asyncpg.PostgresError`, repository возвращает `code_status=422`, `operation_status="PostgresError"`, `error_message=str(e)` (`app/database/repositories/warehouse_and_balances.py:366-371`).
9. Service проверяет только `result.code_status == 201`, а не `operation_status` (`app/service/warehouse_and_balances.py:48`).
10. Service загружает состав комплекта из `products.kit_components`:

```sql
SELECT kit_components FROM products WHERE id = $1
```

Источник: `app/database/repositories/warehouse_and_balances.py:94-108`.

11. Service добавляет `data.kit_komponents = kit_components`, делает dump запроса без `warehouse_id`, преобразует словарь компонентов в список `{product_id, quantity}` и печатает payload (`app/service/warehouse_and_balances.py:49-54`, `app/service/warehouse_and_balances.py:61-78`).
12. Service создаёт `ONECRouting(base_url=settings.ONE_C_BASE_URL, password=settings.ONE_C_PASSWORD, login=settings.ONE_C_LOGIN)` и вызывает `assembly_or_disassembly_metawild` (`app/service/warehouse_and_balances.py:55-56`).
13. Клиент 1С отправляет `POST` на `self.base_url + "ass_disass/"` с JSON payload и HTTP Basic Auth (`app/infrastructure/ONE_C/routing.py:20-28`).
14. HTTP-статус и текст ответа 1С печатаются; текст ответа возвращается клиентом, но игнорируется service (`app/infrastructure/ONE_C/routing.py:25-28`, `app/service/warehouse_and_balances.py:56`).
15. Service возвращает исходный DB-ответ в endpoint (`app/service/warehouse_and_balances.py:58`).

## Таблицы БД

Подтверждено кодом:

- `kit_operations`: таблица команд и статусов операций комплектации. Записывается repository endpoint, читается endpoint истории.
- `products`: хранит справочник товаров и состав комплекта в `kit_components`; комплекты определяются по `is_kit = TRUE`.
- `inventory_transactions`: таблица истории/отчёта; `group_data` считает transaction types `kit_disassembly`, `kit_assembly`, `kit_result` участием в комплектации/разукомплектации.
- `current_balances`: читается endpoint остатков. Связана с остатками, но Python flow операции комплектации напрямую её не читает и не пишет.
- `product_availability`: читается endpoint валидного остатка. Похоже, раскрывает доступность компонентов для комплектов, но flow операции комплектации её не вызывает.
- `warehouses`: на неё указывает `warehouse_id`; читается отдельным warehouse endpoint.

Статус DDL:

- `docs/context/database_schema.sql:1-4` говорит, что DDL репозитория неполный и содержит только DDL return-to-supplier.
- `docs/context/database_map.md:20` говорит, что `current_balances` и `product_availability` могут быть table/view/materialized view; код не позволяет определить точно.

## SQL-операции

### Запись операции и ожидание статуса

Файл/функция: `app/database/repositories/warehouse_and_balances.py:345`, `WarehouseAndBalancesRepository.assembly_or_disassembly_metawild`.

Параметры:

- `$1 = data.warehouse_id`
- `$2 = data.metawild`
- `$3 = data.operation_type`
- `$4 = data.count`
- `$5 = data.author`

Таблицы:

- Пишет `kit_operations`.
- Читает `kit_operations`.

Влияние на остатки:

- Прямого влияния в Python SQL нет.
- Влияние на остатки этим SQL не доказано. Вероятно, оно происходит на стороне БД, потому что код ждёт статус, но DDL триггера/worker отсутствует.

Транзакция:

- Insert выполняется до polling. При стандартном поведении asyncpg каждое выражение выполняется в собственной транзакции, если явно не открыт transaction. Это вывод из отсутствия `conn.transaction()` в `app/database/repositories/warehouse_and_balances.py:345-365`.

### Чтение состава комплекта

Файл/функция: `app/database/repositories/warehouse_and_balances.py:94`, `kit_components_by_product_id`.

SQL:

```sql
SELECT kit_components FROM products WHERE id = $1
```

Параметры:

- `$1 = product_id`, вызывается как `data.metawild`.

Таблицы:

- Читает `products`.

Влияние на остатки: нет.

Транзакция: явной транзакции нет.

### История операций комплектации

Файл/функция: `app/database/repositories/inventory_transactions.py:185`, `get_kit_operations`.

SQL читает `kit_operations` по `created_at BETWEEN $1 AND $2`, возвращает `id`, `kit_product_id`, `warehouse_id`, `operation_type`, `quantity`, `status`, `author`, `created_at`, `DATE(created_at)`.

Параметры:

- `$1 = datetime_from`
- `$2 = datetime_to`

Влияние на остатки: нет; read-only история.

Транзакция: явной транзакции нет.

### Агрегированный отчёт по остаткам

Файл/функция: `app/database/repositories/inventory_transactions.py:300-389`, `group_data`.

Релевантный SQL-фрагмент: `transaction_type IN ('kit_disassembly', 'kit_assembly', 'kit_result')` попадает в `"Участие в сборке/разборе"` (`app/database/repositories/inventory_transactions.py:333-337`).

Таблицы:

- Читает `inventory_transactions`.

Влияние на остатки: нет; read-only отчёт.

### Чтение справочника товаров/комплектов

Файл/функция: `app/database/repositories/goods_information.py:15`, `get_metawilds_data`.

SQL:

```sql
SELECT * FROM products WHERE is_kit = TRUE and is_active = TRUE;
```

Назначение: возвращает активные комплекты/metawilds и парсит `kit_components`.

Файл/функция: `app/database/repositories/goods_information.py:40`, `get_all_products_data`.

SQL:

```sql
SELECT * FROM products WHERE is_active = TRUE;
```

Назначение: возвращает активные товары с `is_kit`, `share_of_kit`, `kit_components`.

## Изменения остатков

Подтверждено:

- API operation вставляет только строку в `kit_operations`.
- API operation напрямую не вставляет строки в `inventory_transactions`.
- API operation напрямую не обновляет `current_balances`.
- Агрегированный inventory report распознаёт kit-related строки в `inventory_transactions` с types `kit_disassembly`, `kit_assembly`, `kit_result`.

не подтверждено:

- Точные строки, вставляемые в `inventory_transactions` для assembly/disassembly.
- Точное правило знаков для уменьшения/увеличения компонентов и комплекта.
- Точный механизм обновления `current_balances`.
- Является ли `current_balances` table, view или materialized view.
- Выполняется ли проверка остатков перед decrement.
- Запрещены ли отрицательные остатки.

Бизнес-смысл по описанию endpoint:

- Assembly: собрать комплект из компонентов.
- Disassembly: разобрать комплект на компоненты.

Определение товара-комплекта:

- Catalog endpoint определяет комплекты как `products.is_kit = TRUE AND products.is_active = TRUE` (`app/database/repositories/goods_information.py:17`).
- Состав комплекта хранится в `products.kit_components`, парсится из JSON (`app/database/repositories/goods_information.py:24-28`).
- Operation использует `data.metawild` как `kit_product_id` в `kit_operations` и как `products.id` для чтения компонентов.

Количество:

- Поле запроса `count`.
- Хранится как `kit_operations.quantity`.
- Отправляется в 1С как `count`.
- Количества компонентов в payload 1С являются per-kit quantities из `products.kit_components`; код не умножает их на `count` перед отправкой.

Склад/аккаунт/организация:

- `warehouse_id` хранится в `kit_operations`.
- `warehouse_id` исключается из payload, который отправляется в 1С (`data.model_dump(exclude={"warehouse_id"})`).
- Account или organization отсутствуют в request schema и payload 1С для этой операции.

## Интеграция с 1С

Клиент: `app/infrastructure/ONE_C/routing.py:20-28`.

- URL/path: `self.base_url + "ass_disass/"`.
- HTTP-метод: `POST`.
- Auth: `aiohttp.BasicAuth(self.login, self.password)`.
- Config/env переменные: `ONE_C_LOGIN`, `ONE_C_PASSWORD`, `ONE_C_BASE_URL` (`app/dependencies/config.py:47-49`). Значения должны быть замаскированы.
- Timeout: явный timeout для `ass_disass/` не задан. В том же клиенте timeout есть только у `commission_sales_fbo_add`: `timeout=60` (`app/infrastructure/ONE_C/routing.py:68`).
- Retry: в коде нет.
- Payload запроса: dict, который service формирует после исключения `warehouse_id` и преобразования `kit_komponents` из dict в list.
- Обработка ответа: печатает HTTP-статус, читает текст ответа, печатает текст ответа, возвращает текст.
- Обработка ошибок: ветвления по status-code нет; текст ответа HTTP 4xx/5xx возвращается и игнорируется caller. Network/client exceptions не ловятся в service или endpoint.
- Логирование: `pprint(refactor_kit_components)` в service и `print(response.status)`, `print(json_response)` в client.
- Связь со статусом: response от 1С не записывается обратно в `kit_operations`; `kit_operations.status` определяется до вызова 1С DB-side процессом.

Форма payload, который уходит в 1С, по коду:

```json
{
  "author": "Ваня который соска",
  "metawild": "metawild_test",
  "count": 3,
  "operation_type": "assembly",
  "kit_komponents": [
    {"product_id": "testwild", "quantity": 2},
    {"product_id": "testwild2", "quantity": 1}
  ]
}
```

Примечание: имя ключа в коде — `kit_komponents`, не `kit_components`.

## Границы транзакций

- Явной транзакции вокруг insert/polling `kit_operations` нет.
- Явной транзакции вокруг чтения `products` также нет.
- Вызов 1С происходит после того, как repository вернул финальный DB status и после завершения insert statement в `kit_operations`.
- Вызов 1С не находится внутри application-level DB transaction.
- Границы транзакций DB-side обработчика остатков/статуса отсутствуют в repository code и не подтверждено.

Отказные сценарии:

- Если DB insert/select выбрасывает `asyncpg.PostgresError`, service не вызывает 1С, потому что `code_status=422`.
- Если DB-side status становится финальным failure status, но сам SQL успешен, service всё равно вызывает 1С, потому что проверяет только `code_status == 201`.
- Если БД обновилась, а 1С вернула HTTP error status, client не делает raise по status, service игнорирует response text; endpoint всё равно возвращает DB response.
- Если БД обновилась, а network call в 1С выбрасывает exception, catch в service/endpoint отсутствует; HTTP request, вероятно, завершится ошибкой после уже выполненной локальной DB work.
- Если 1С приняла запрос, а service упал до возврата HTTP-ответа, в application code нет ожидающего дополнительного DB update. Client может повторить API-запрос и создать вторую строку `kit_operations`, потому что идемпотентность отсутствует.
- Если service упал во время busy-wait repository, DB-side процесс всё ещё может завершиться; API response потерян. Явной обработки этого сценария нет.

## Идемпотентность/retry

Не найдено:

- idempotency key;
- external operation id в request;
- unique client request key;
- outbox table;
- integration log table;
- retry worker для `ass_disass/`;
- endpoint ручной переотправки;
- reconciliation endpoint для статуса 1С.

`kit_operations.id` генерируется БД и используется только для polling вставленной строки. В 1С он не отправляется.

## Сценарии ошибок

Подтверждено кодом:

- Некорректный `operation_type` отклоняется Pydantic, потому что это `Literal["assembly", "disassembly"]`.
- PostgreSQL errors в repository возвращают application response `code_status=422`.
- Endpoint преобразует `code_status >= 400` в HTTP error.
- Busy wait не имеет sleep, timeout или max attempts.
- `kit_components_by_product_id` может выбросить uncaught `IndexError`, если `products` не вернул строк; код ловит только JSON decode/type errors после `result[0]`.
- Некорректный/null `kit_components` превращается в `{}` при JSON decode/type errors; payload в 1С тогда содержит пустой `kit_komponents`.
- HTTP error statuses от 1С не меняют API response и не сохраняются.

не подтверждено:

- DB-side failure statuses и их имена, кроме waiting statuses `pending` и `processing`.
- Используются ли final statuses `success`, `completed`, `error`, `failed` и т.п.
- Пишет ли DB-side processing поле `error_message`.

## Открытые вопросы

- Какой production DDL у `kit_operations`, `inventory_transactions`, `current_balances`, `products`, `product_availability` и связанных triggers/functions?
- Какой именно DB-side процесс меняет `kit_operations.status`?
- Какие все допустимые statuses есть у `kit_operations.status`?
- Какие точные строки `inventory_transactions` создаются для assembly и disassembly?
- Умножаются ли количества компонентов на `count` в DB-side logic, в 1С, в обоих местах или нигде?
- Нужно ли вызывать 1С только для успешного DB-side operation status?
- Требует ли 1С operation id/idempotency key?
- Ожидает ли 1С написание `kit_komponents`?
- Какой warehouse/account/organization должна использовать 1С, если `warehouse_id` исключается из payload?

## Риски для миграции в WMS

- Скрытое DB-side поведение: основная мутация остатков не находится в Python code, DDL/triggers отсутствуют.
- Неатомарная интеграция БД и 1С: локальное завершение в БД и приёмка в 1С не являются одной транзакцией.
- Нет идемпотентности: повторные client retries могут создать дублирующие операции комплектации.
- Нет outbox/retry: ошибки 1С могут быть молча проигнорированы или оставить расхождение между локальной БД и 1С.
- Busy-wait жизненный цикл request: request может зависнуть без ограничения и потреблять CPU/DB.
- Неоднозначная семантика успеха: endpoint возвращает `201` для любого финального DB status, потому что HTTP-поведение определяется только `code_status`.
- Риск несовпадения payload: `warehouse_id` хранится локально, но не отправляется в 1С; написание `kit_komponents` необычное.
- Отсутствующий production DDL не позволяет доказать constraints, проверки остатков, lifecycle статусов и side effects триггеров.

## Проверенные файлы

- `main.py`: подтверждает регистрацию prefix `/api`.
- `app/api/v1/endpoints/warehouse_and_balances.py`: объявляет operation endpoint.
- `app/models/warehouse_and_balances.py`: схемы запроса/ответа и примеры.
- `app/service/warehouse_and_balances.py`: orchestration в service и вызов 1С.
- `app/database/repositories/warehouse_and_balances.py`: insert/poll `kit_operations` и чтение `products.kit_components`.
- `app/infrastructure/ONE_C/routing.py`: клиент 1С `ass_disass/`.
- `app/dependencies/config.py`: имена env-переменных 1С.
- `app/api/v1/endpoints/inventory_transactions.py`: endpoint истории комплектов.
- `app/service/inventory_transactions.py`: service-слой без дополнительной логики для истории комплектов.
- `app/database/repositories/inventory_transactions.py`: история `kit_operations` и агрегация комплектов из `inventory_transactions`.
- `app/models/inventory_transactions.py`: модели ответов истории комплектов.
- `app/api/v1/endpoints/goods_information.py`: endpoint каталога metawild.
- `app/service/goods_information.py`: service-слой без дополнительной логики для каталога товаров.
- `app/database/repositories/goods_information.py`: читает/пишет `products`, парсит `kit_components`.
- `app/models/goods_information.py`: схемы и примеры product/metawild.
- `docs/context/database_schema.sql`: подтверждает DDL неполный.
- `docs/context/database_triggers.md`: подтверждает отсутствие DDL триггеров и косвенно подтверждённую DB-side обработку.
- `docs/context/database_functions.md`: подтверждает документация функций ограничена.
- `docs/context/database_map.md`: подтверждает карту таблиц stock/catalog/operations и оговорку об отсутствующем DDL.
- `docs/context/integration_map.md`: существующая сводка интеграции для `ass_disass/`.
- `docs/context/known_issues.md`: существующие заметки про отсутствие timeout и логирование через print.

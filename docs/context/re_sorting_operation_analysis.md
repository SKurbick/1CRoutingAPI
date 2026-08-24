# Исследование операции пересортицы

Объект анализа: `POST /api/warehouse_and_balances/re_sorting_operations` в текущем состоянии репозитория. Исследование выполнено без вызова API и без обращения к рабочей БД. Production DDL таблицы `re_sorting_operations`, обработчика её команд и связанных триггеров/функций в репозитории отсутствует; поэтому фактические внутренние действия этого обработчика отделены от доказанного поведения Python-кода.

## 1. Краткий вывод

1. Маршрут подтверждён как `POST /api/warehouse_and_balances/re_sorting_operations`: prefix `/api` задаёт `main.py:113`, prefix `/warehouse_and_balances` — `app/api/v1/endpoints/warehouse_and_balances.py:12`, endpoint — строки 91–108 того же файла.
2. Запрос содержит ровно шесть обязательных полей: исходный товар, итоговый товар, склад, одно общее количество, причина и автор (`app/models/warehouse_and_balances.py:191-197`). Ограничений положительности, запрета одинаковых товаров и пользовательских validators нет.
3. Python-код не изменяет остатки напрямую. Repository вставляет одну команду в `re_sorting_operations`, получает её `id` и без задержки/таймаута опрашивает `operation_status` (`app/database/repositories/warehouse_and_balances.py:182-204`).
4. Какой trigger, function, procedure или внешний worker меняет статус и остатки, по репозиторию установить нельзя: его DDL/код отсутствует (`docs/context/database_triggers.md:3-15`, `docs/context/database_schema.sql:1-4`).
5. Из контракта доказано только намерение заменить `from_product_id` на `to_product_id` в одном `warehouse_id` и с одним `quantity`. Фактическая формула остатков, проверки существования/активности товаров, достаточности остатка, резервов и атомарность скрытого обработчика не подтверждены.
6. После любого финального статуса, отличного от `pending` и `processing`, repository ставит технический `code_status=201`; service поэтому вызывает 1С даже для финального бизнес-статуса ошибки (`app/database/repositories/warehouse_and_balances.py:202-204`, `app/service/warehouse_and_balances.py:81-86`).
7. Вызов 1С — `POST` на относительный path `goods_resorting/`, HTTP Basic Auth, JSON без `warehouse_id`; остальные пять полей передаются (`app/infrastructure/ONE_C/routing.py:30-40`). Явных timeout/retry/`raise_for_status` нет.
8. HTTP 4xx/5xx от 1С не преобразуется в ошибку: тело читается как text, печатается и игнорируется service. Network/timeout-исключения не перехватываются и происходят после локального insert/завершения DB-side обработки.
9. Ответ успешного API не содержит operation ID, новых остатков или ответа 1С; только `operation_status`, всегда `code_status=201` для любого полученного финального DB-статуса и необязательный `error_message` (`app/models/warehouse_and_balances.py:200-203`).
10. Явной транзакции в repository нет. Insert и каждый polling SELECT выполняются отдельными SQL-командами; границы транзакции скрытого обработчика неизвестны.
11. Идемпотентность отсутствует на уровне доступного Python-кода: operation/idempotency key не принимается, каждый повтор делает новый `INSERT`, поиск дубля отсутствует. Наличие неизвестного unique constraint в production БД проверить нельзя.
12. История доступна через отдельный `GET /api/inventory_transactions/get_re_sorting_operations?date_from=...&date_to=...`; он читает command rows и возвращает их ID/поля/статус по датам (`app/api/v1/endpoints/inventory_transactions.py:69-79`, `app/database/repositories/inventory_transactions.py:15-67`).
13. Endpoint не подключает token dependency и не имеет собственного rate limiter; глобального auth middleware в `main.py:86-100` нет. Следовательно, по коду специальные права/авторизация для него не требуются.
14. Тестов, frontend-клиента, Postman collection, Celery/RabbitMQ/background-task вызовов операции в доступных репозиториях не найдено.

## 2. Endpoint и контракт

### Маршрут, dependencies и ошибки

| Свойство | Фактическое значение | Источник |
|---|---|---|
| HTTP method | `POST` | `app/api/v1/endpoints/warehouse_and_balances.py:91` |
| Полный path | `/api/warehouse_and_balances/re_sorting_operations` | `main.py:113`; endpoint router prefix в `app/api/v1/endpoints/warehouse_and_balances.py:12`; route на строке 91 |
| Endpoint function | `re_sorting_operations` | `app/api/v1/endpoints/warehouse_and_balances.py:93-108` |
| Request body | `ReSortingOperation` | там же, строка 94 |
| Response model | `ReSortingOperationResponse` | там же, строка 91 |
| Декларированный success status | HTTP 201 | там же, строка 91 |
| Dependency | `get_warehouse_and_balances_service` | там же, строка 95 |
| Dependency chain | Request `app.state.pool` → repository → service | `app/dependencies/warehouse_and_balances.py:9-19` |
| Авторизация | Не подключена | router на строке 12 и endpoint на строках 91-108 не содержат security dependency; `main.py:86-100` не регистрирует auth middleware |
| Rate limit | Не подключён к этому endpoint | limiter decorators есть у других функций в том же файле, но отсутствует на строках 91-108 |

`get_warehouse_and_balances_service` создаёт новый `WarehouseAndBalancesRepository` на request pool и затем `WarehouseAndBalancesService`; дополнительных бизнес/security dependencies нет (`app/dependencies/warehouse_and_balances.py:9-19`). Реализованные, но не подключённые `verify_service_token` и `verify_token` находятся в `app/dependencies/security.py:21-42` и не влияют на этот маршрут.

Возможные наблюдаемые HTTP-результаты:

- `201`: endpoint вернул любой repository result с `code_status < 400`. Для любого DB-статуса, вышедшего из `pending/processing`, repository принудительно формирует `code_status=201` (`app/database/repositories/warehouse_and_balances.py:202-204`).
- `422` от FastAPI/Pydantic: отсутствующее поле, несовместимый тип или запрещённое Pydantic преобразование; endpoint ещё не вызывается.
- `422` от endpoint: repository поймал `asyncpg.PostgresError`, вернул `code_status=422`, endpoint поднял `HTTPException` с `detail.message=error_message` и `detail.details="HTTPException"` (`app/database/repositories/warehouse_and_balances.py:205-210`, `app/api/v1/endpoints/warehouse_and_balances.py:99-106`).
- `500`/необработанная серверная ошибка: возможна при исключениях вне `asyncpg.PostgresError`, включая ошибки доступа к `check_status`, Pydantic response construction и сетевые исключения 1С. Явного обработчика в цепочке нет.
- Запрос может не завершиться: polling loop не имеет sleep, deadline или max attempts (`app/database/repositories/warehouse_and_balances.py:199-203`).

### Контракт запроса

Все поля объявлены в `ReSortingOperation` (`app/models/warehouse_and_balances.py:191-197`). Model config, aliases, `Field` constraints и validators у модели отсутствуют. Следовательно, все поля обязательны, default отсутствует, а nullable не разрешён типом. Действует стандартная валидация/coercion Pydantic 2 из версии проекта (`requirements.txt:4`). Стандартное поведение extra-полей отдельно моделью не переопределено.

| Поле | Тип | Обязательное | Default | Ограничения/преобразования | Назначение и где используется |
|---|---|---:|---|---|---|
| `from_product_id` | `str` | да | нет | Пользовательских ограничений нет | Исходный товар; вставляется в `re_sorting_operations.from_product_id`, затем передаётся в 1С |
| `to_product_id` | `str` | да | нет | Пользовательских ограничений нет | Итоговый товар; вставляется в `to_product_id`, затем передаётся в 1С |
| `warehouse_id` | `int` | да | нет | Нет `ge`, allow-list или validator | Вставляется в `warehouse_id`; **исключается** из payload 1С |
| `quantity` | `int` | да | нет | Нет `gt/ge`; ноль и отрицательное значение не отвергаются схемой | Одно количество команды; вставляется в БД и передаётся в 1С |
| `reason` | `str` | да | нет | Нет min/max length | Причина; вставляется в БД и передаётся в 1С |
| `author` | `str` | да | нет | Нет min/max length или проверки identity | Автор; вставляется в БД и передаётся в 1С |

Отсутствуют в request schema: account/поставщик, дата, номер документа, GUID/operation/idempotency key, supply/order/task ID, КИЗ, СЗ, SRID, batch/партия, контейнер, location, отдельные количества расхода и прихода, статус резерва. Эти данные не могут быть переданы endpoint штатно через объявленную схему.

Единственный найденный реальный пример взят из OpenAPI example в коде (`app/models/warehouse_and_balances.py:43-50`):

```json
{
  "from_product_id": "testwild",
  "to_product_id": "testwild2",
  "warehouse_id": 1,
  "quantity": 10,
  "reason": "Поставщик перепутал цвет товара",
  "author": "Зина"
}
```

### Контракт ответа

Модель: `app/models/warehouse_and_balances.py:200-203`.

| Поле | Тип | Когда заполняется | Источник значения |
|---|---|---|---|
| `operation_status` | `str` | Всегда | Финальный `re_sorting_operations.operation_status`; при пойманной PostgreSQL error — строка `PostgresError` |
| `code_status` | `int` | Всегда | Вручную `201` после выхода из polling либо `422` в `except asyncpg.PostgresError` |
| `error_message` | `str \| null` | Необязательно | Поле command row либо `str(asyncpg exception)` |

Успехом для orchestration считается только `code_status == 201`, не значение `operation_status` (`app/service/warehouse_and_balances.py:82-85`). Поэтому HTTP 201 возможен при фактическом финальном бизнес-статусе ошибки, если DB processor записал такой статус и `error_message`. Частичные ошибки отдельной структурой не представлены. Не возвращаются: local operation ID, ID/документ 1С, ответ 1С, прежние/новые остатки, две стороны движения.

## 3. Полный call flow

1. FastAPI получает `POST /api/warehouse_and_balances/re_sorting_operations` и валидирует JSON как `ReSortingOperation` (`app/api/v1/endpoints/warehouse_and_balances.py:91-95`). Validation error завершает цепочку HTTP 422 до service.
2. Dependency берёт asyncpg pool из `request.app.state.pool`, создаёт repository и service (`app/dependencies/warehouse_and_balances.py:9-19`). Pool инициализируется при lifespan startup (`main.py:27-35`, `main.py:76-78`).
3. Endpoint вызывает `WarehouseAndBalancesService.re_sorting_operations(data)` (`app/api/v1/endpoints/warehouse_and_balances.py:97`).
4. Service вызывает одноимённый repository method (`app/service/warehouse_and_balances.py:81-82`).
5. Repository собирает tuple из всех шести полей (`app/database/repositories/warehouse_and_balances.py:182-183`).
6. На одном acquired connection выполняется параметризованный `INSERT INTO re_sorting_operations (...) VALUES (...) RETURNING id` (`app/database/repositories/warehouse_and_balances.py:185-198`).
7. Repository немедленно входит в бесконечный loop и выполняет `SELECT operation_status, error_message FROM re_sorting_operations WHERE id=$1` (`app/database/repositories/warehouse_and_balances.py:192-203`). Каждый результат печатается через `pprint`, то есть status/error попадают в stdout.
8. Loop заканчивается только если status не равен `pending` и `processing`. Repository не проверяет семантику и возвращает `ReSortingOperationResponse(..., code_status=201)` (`app/database/repositories/warehouse_and_balances.py:202-204`).
9. Не показанный в Python DB-side компонент должен изменить status, иначе запрос зависает. Его тип, код и side effects в репозитории отсутствуют (`docs/context/database_triggers.md:5-15`).
10. При `asyncpg.PostgresError` repository возвращает response object с `code_status=422`; rollback/compensation к уже committed действиям явно не выполняются (`app/database/repositories/warehouse_and_balances.py:205-210`).
11. Если `code_status == 201`, service создаёт `ONECRouting` из 1С-настроек и синхронно ожидает `re_sorting_operations` (`app/service/warehouse_and_balances.py:83-85`).
12. 1С client исключает `warehouse_id`, печатает payload, выполняет HTTP POST с Basic Auth на `base_url + "goods_resorting/"`, читает response как text, печатает status/text и возвращает text (`app/infrastructure/ONE_C/routing.py:30-40`). Service return value игнорирует.
13. Service возвращает DB response; endpoint при `code_status >= 400` поднимает HTTPException, иначе FastAPI сериализует `ReSortingOperationResponse` с HTTP 201 (`app/api/v1/endpoints/warehouse_and_balances.py:97-108`).

В этой цепочке не найдены ORM, RabbitMQ publish, Celery task, FastAPI BackgroundTasks, WMS HTTP call или integration-log write.

## 4. Бизнес-правила

### Подтверждённые правила

- Одна API-команда задаёт ровно одну пару `from_product_id`/`to_product_id`, один склад и одно количество (`app/models/warehouse_and_balances.py:191-197`). Списки исходных/итоговых товаров отсутствуют.
- Один и тот же `quantity` передаётся вместе с обоими product IDs в command row и в 1С; отдельных X/Y контракт не поддерживает (`app/database/repositories/warehouse_and_balances.py:183-190`, `app/infrastructure/ONE_C/routing.py:32-36`).
- В API-команде один `warehouse_id`; второго склада нет. 1С warehouse ID не получает (`app/models/warehouse_and_balances.py:194`, `app/infrastructure/ONE_C/routing.py:32`).
- Название полей и пример причины подтверждают намерение сменить идентификацию товара (`from` → `to`) из-за ошибки ассортимента, но Python-код не реализует саму складскую мутацию (`app/models/warehouse_and_balances.py:43-50`, repository lines 182-204).
- Команда сохраняет причину и автора; created timestamp не принимается от клиента, но поле `created_at` читается history endpoint, следовательно, оно существует в фактической таблице доступной текущему коду (`app/database/repositories/inventory_transactions.py:20-55`). Источник/default timestamp без DDL неизвестен.

### Формула, которую позволяет выразить контракт

Контракт имеет одно количество `Q`, поэтому предполагаемая командой пара имеет форму:

```text
from_product_id в warehouse_id: изменение на -Q
to_product_id   в warehouse_id: изменение на +Q
```

Это **вывод из названий полей и единого quantity**, а не подтверждённая реализация: SQL/код DB-side обработчика отсутствует. Нельзя подтвердить, что обе стороны реально применяются, применяются в одинаковом количестве или вообще меняют конкретную таблицу остатков.

### Что по доступным исходникам установить нельзя

Не подтверждены: сохранение общего количества склада; возможность увеличения общего остатка; запрет отрицательных остатков; достаточность исходного остатка; существование/активность итогового товара; одинаковый account/поставщик; учёт резервов; работа с агрегированным балансом либо unit-level товаром; партии, контейнеры и locations; порядок расход/приход; создание отсутствующей balance row; удаление нулевой строки. Все эти правила находятся за отсутствующим DB-side processor/DDL либо отсутствуют.

## 5. Изменения базы данных

### Видимые таблицы и SQL

| Таблица | Операция | Поля | Назначение |
|---|---|---|---|
| `re_sorting_operations` | `INSERT` | `from_product_id`, `to_product_id`, `warehouse_id`, `quantity`, `reason`, `author`; `RETURNING id` | Создать command/audit row пересортицы |
| `re_sorting_operations` | повторный `SELECT` | читает `operation_status`, `error_message`; `WHERE id=$1` | Дождаться финального статуса |
| `re_sorting_operations` | history `SELECT` | `id`, оба product ID, warehouse, reason, quantity, author, status, created_at | Read endpoint истории по диапазону дат |

Основной SQL находится в `WarehouseAndBalancesRepository.re_sorting_operations`, `app/database/repositories/warehouse_and_balances.py:182-204`. Insert параметризован, имеет `RETURNING id`, но не проверяет command tag/число строк отдельно. Polling SELECT использует primary-like ID, но наличие PK/unique index DDL не доказано. `SELECT FOR UPDATE`, advisory locks, explicit table/row locks и `RETURNING` изменённых остатков отсутствуют.

History SQL находится в `InventoryTransactionsRepository.get_re_sorting_operations`, `app/database/repositories/inventory_transactions.py:15-67`: `WHERE created_at BETWEEN $1 AND $2`, сортировка по `DATE(created_at), from_product_id`. Он не читает `error_message` и не возвращает баланс.

### DDL, constraints, triggers, indexes

Production DDL `re_sorting_operations`, таблиц текущих остатков, её constraints/indexes/FK/defaults и processor trigger/function отсутствует. `docs/context/database_schema.sql:1-4` прямо фиксирует неполноту DDL; единственная migration в репозитории относится к `return_to_supplier`. `docs/context/database_triggers.md:3-15` фиксирует отсутствие trigger DDL и невозможность отличить trigger от external DB worker. Поэтому нельзя достоверно перечислить таблицы, которые скрытый обработчик читает/изменяет, либо подтвердить DB constraints.

### Фактический псевдокод видимой части

```text
1. INSERT command(from_product_id, to_product_id, warehouse_id, quantity, reason, author)
   RETURNING id.
2. Без sleep и timeout повторять SELECT operation_status, error_message WHERE id=id.
3. Пока status in ('pending', 'processing') — продолжать.
4. При любом другом status вернуть code_status=201.
5. Service при code_status=201 вызывает 1С.
```

Шаги изменения остатков между 1 и 2 по имеющимся исходникам восстановить невозможно.

## 6. Интеграция с 1С

| Свойство | Значение | Источник |
|---|---|---|
| Получатель | 1С | `app/service/warehouse_and_balances.py:83-85` |
| URL | configured base URL + `goods_resorting/` | `app/infrastructure/ONE_C/routing.py:31` |
| Method | POST | строка 36 |
| Client | `aiohttp.ClientSession` | строки 35-36 |
| Auth | HTTP Basic, credentials из settings | строки 36; settings fields в `app/dependencies/config.py:46-49` |
| Headers | Только автоматически формируемые aiohttp для JSON/Auth; пользовательских нет | строки 35-36 |
| Explicit timeout | Нет | строки 35-36 |
| Retry | Нет | весь method 30-40 |
| Payload | `from_product_id`, `to_product_id`, `quantity`, `reason`, `author`; `warehouse_id` исключён | строка 32 |
| Response parsing | `await response.text()` | строка 38 |
| Logging | `print` payload, HTTP status и text body | строки 34, 37-39 |
| Порядок | После финализации локальной DB command | service lines 82-85 |

HTTP status не проверяется через `raise_for_status`; JSON не парсится; бизнес-status внутри HTTP 200 не проверяется. Поэтому 1С HTTP 4xx/5xx или произвольный/невалидный JSON body сами по себе не делают API-вызов ошибочным. Network errors и client timeout могут выбросить исключение; их не ловят ни integration method, ни service, ни endpoint. Реальных паролей/URL отчёт не содержит.

RabbitMQ, Celery, background task и другой internal API в call flow не обнаружены.

## 7. Транзакции и конкурентность

- Ни endpoint, ни service, ни repository не открывают `conn.transaction()` (`app/api/v1/endpoints/warehouse_and_balances.py:91-108`, `app/service/warehouse_and_balances.py:81-86`, `app/database/repositories/warehouse_and_balances.py:197-204`).
- При обычной семантике asyncpg одиночный insert выполняется и фиксируется как отдельный statement до последующих SELECT. Это вывод из отсутствия explicit transaction, а не наличие ручного `commit` в коде.
- Polling выполняется на том же acquired connection, но каждый SELECT не объединён явной транзакцией с insert.
- Вызов 1С точно не входит в локальную DB transaction: repository уже вернул результат и connection context завершён до создания `ONECRouting` (`app/service/warehouse_and_balances.py:82-85`).
- Транзакционность двух сторон складской мутации, журнала `inventory_transactions` и status update неизвестна, потому что handler отсутствует.
- `SELECT FOR UPDATE`, optimistic version, advisory lock и application lock в видимой цепочке отсутствуют.
- Два параллельных API-запроса создают две независимые command rows. Сериализация конфликтующих команд и lost-update safety зависят от неизвестного handler/DB DDL.
- Частичное состояние «исходный списан, итоговый не добавлен» нельзя подтвердить или исключить.
- Состояние «локальная операция завершена, 1С не обновлена» возможно: integration вызывается после DB completion и компенсации нет.

## 8. Идемпотентность

**Вывод: идемпотентность на уровне доступной реализации отсутствует.**

Request не содержит operation ID, GUID, document number или idempotency key (`app/models/warehouse_and_balances.py:191-197`). Repository всегда выполняет новый insert и не ищет прежнюю команду (`app/database/repositories/warehouse_and_balances.py:182-198`). Python-код не задаёт `ON CONFLICT`, unique key или deduplication. Поэтому идентичный повтор потенциально повторяет складское действие и после final status повторно вызывает 1С.

Оговорка: production unique constraints и неизвестный processor могут иметь собственную защиту, но их DDL/код отсутствует; подтвердить её нельзя. Без внешнего знания безопасно повторять запрос после client/1С timeout нельзя. History позволяет увидеть операции по датам и ID, но endpoint не возвращает ID созданной строки, что не даёт клиенту надёжно сопоставить попытку.

## 9. Ошибочные сценарии

| Сценарий сбоя | Состояние локальной БД | Состояние 1С | Что получает клиент |
|---|---|---|---|
| Ошибка Pydantic validation | Command не вставлен | Не вызвана | HTTP 422 validation response |
| Исходный товар не найден | Не определяется Python-кодом; зависит от handler. Возможны final error либо вечный pending | При любом финальном status repository ставит code 201 и service вызывает 1С | HTTP 201 с business status/error, либо зависание, либо необработанная ошибка — зависит от handler |
| Итоговый товар не найден | То же | То же | То же |
| Недостаточно остатка | То же | То же | То же |
| Ошибка `INSERT` command | При statement error command не создан; детали неизвестного trigger rollback зависят от DB | Не вызвана | Repository 422 → endpoint HTTP 422 с error text |
| Ошибка первого balance SQL update | Update не виден в репозитории; atomicity handler неизвестна | Зависит от выставленного status; при финальном status вызовется | Нельзя определить без handler |
| Ошибка второго balance SQL update | Возможность partial local state неизвестна | Зависит от выставленного status; при финальном status вызовется | Нельзя определить без handler |
| Polling SELECT PostgreSQL error | Command мог уже сохраниться/обрабатываться | Не вызвана в этой попытке | HTTP 422 |
| Handler не меняет `pending/processing` | Command сохранён, конечное состояние остатков неизвестно | Не вызвана | HTTP request висит без application timeout |
| Timeout/network error 1С | Локальная command уже final; отката нет | Результат неизвестен | Необработанное исключение, обычно server error/disconnect |
| HTTP 4xx от 1С | Локальная command final | 1С отказала на HTTP уровне | Response body читается и игнорируется; клиент получает HTTP 201 DB response |
| HTTP 5xx от 1С | Локальная command final | Ошибка 1С | Аналогично HTTP 201 DB response |
| Невалидный JSON от 1С | Локальная command final | Ответ неизвестной семантики | JSON не парсится; text принимается, клиент получает HTTP 201 |
| Финальный DB business error | Как записал handler | **1С всё равно вызывается**, поскольку `code_status=201` | HTTP 201 с `operation_status`/`error_message` |
| Повтор идентичного запроса | Новый command insert; повторный эффект возможен | После каждого final status новый вызов | Новый независимый ответ; operation ID не возвращается |
| Два параллельных запроса | Две command rows; порядок/locks handler неизвестны | До двух независимых вызовов после final statuses | Каждый ждёт свой status; lost update/serialization неизвестны |

## 10. Использование и тесты

### История и аудит

Command row сохраняет оба product ID, warehouse ID, quantity, reason и author. History endpoint дополнительно читает `id`, `operation_status`, `created_at` (`app/database/repositories/inventory_transactions.py:20-55`). Таким образом, операцию можно искать по ID прямым DB-запросом, а API истории выдаёт ID в заданном диапазоне дат. Отдельного GET by operation ID не найдено.

Не сохраняются видимым Python-кодом: исходный payload целиком, response/status 1С, integration error, before/after balances, отдельные строки расхода/прихода, связь с документом 1С. Возможно ли их создание неизвестным handler/trigger, определить нельзя.

History endpoint: `GET /api/inventory_transactions/get_re_sorting_operations`, обязательные по runtime-проверке query dates `date_from`/`date_to`; без них HTTP 400 (`app/api/v1/endpoints/inventory_transactions.py:69-79`). Он группирует rows по дате. В repository есть несоответствие: создаётся `IncomingReturnsGroupData`, хотя return annotation/response model ожидают `ReSortingOperationGroupData`; структуры совпадают по полям `date`/`product_group_data`, поэтому текущая сериализация может пройти, но это фактическое противоречие типов (`app/database/repositories/inventory_transactions.py:58-63`, `app/models/inventory_transactions.py:159-178`).

### Клиенты

Поиск `re_sorting_operations`, `goods_resorting`, `get_re_sorting_operations`, `from_product_id`, `to_product_id` выполнен по проекту и доступному `/home/skurbick/PROJECTS`, исключая `.git`, virtualenv и dependency directories. Реальных frontend/backend callers, Postman collections, shell scripts и иных репозиториев-клиентов не найдено. `docs/context/frontend_usage_map.md:3` прямо говорит, что frontend repository/telemetry отсутствуют; строка 11 содержит только вероятную sequence, поэтому она не является доказательством реального вызова.

### Тесты

В `tests` найден только `tests/test_docs_parser.py`; тестов пересортицы нет. Не покрыты success, недостаток остатка, неизвестные товары, DB/1С errors, repeat, concurrency, rollback и authorization. Тесты не запускались: релевантных тестов нет, а endpoint/БД вызывать запрещено условиями исследования.

### Git-история

- `e876383` от 2025-08-08, сообщение `[+] метод по пересорту`: добавил endpoint, неизменившиеся по смыслу request/response schemas, repository insert/polling и service passthrough.
- `7f14f31` от 2025-09-19, `[+] get_re_sorting_operations`: включил read endpoint истории и его SQL.
- `88ff480` от 2025-09-30, `[+] 1c re_sorting_operations`: добавил 1С client с временным URL placeholder и payload со складом.
- `f8ea7c4` от 2025-10-01, `[+] add 1c update data by re-sorting`: подключил 1С call после DB result, заменил path на `goods_resorting/` и исключил `warehouse_id` из payload.
- `git blame` показывает, что основная endpoint/repository/schema логика остаётся от `e876383`; существенное позднее изменение — добавление внешнего вызова. История не показывает удалённых проверок остатков, смены порядка DB/1С или старой альтернативной write implementation.
- Коммиты 2025-10-09 попадают в текстовый `git log -S` из-за общих product dependencies/refactoring, но изученный текущий blame операции не связывает с ними изменение её call flow.

## 11. Факты, важные для переноса в WMS

- Старый контракт выражает пересортицу одной парой from/to, одним warehouse и одним quantity. Это похоже на связанную пару расход/приход, но фактические движения скрыты и должны быть подтверждены production handler.
- Старые сущности `re_sorting_operations` и её DB-side processor не имеют доказанного прямого аналога в доступном WMS-коде/DDL этого репозитория.
- Command row уже играет роль общего заголовка/корреляции пары, но API не возвращает его ID; отдельные movement rows в доступном коде не видны.
- Старый контракт не содержит location, container, batch/lot или unique unit IDs. Для адресного хранения невозможно восстановить выбор location из текущего payload.
- Старый warehouse ID не передаётся в 1С. Это различие локального и внешнего контрактов необходимо сохранить как факт при будущем анализе orchestration.
- В текущем flow локальная финализация предшествует 1С и не компенсируется. Внешний вызов не является частью атомарной операции и должен рассматриваться отдельно от складской мутации.
- Не доказано, что старые правила учитывают reserve/available quantity; их нельзя автоматически переносить на WMS balance semantics.
- Не подтверждена поддержка россыпи, контейнеров, партий, КИЗ/СЗ/SRID и конкретных locations. Их отсутствие в API не доказывает отсутствие в скрытом DB handler.
- Для будущего эквивалента потребуется подтверждённая связь нескольких движений одной бизнес-операцией и аудит before/after; текущий код предоставляет лишь command ID/history, не движение.

Этот раздел фиксирует входные факты и пробелы; он не предлагает WMS tables, endpoint, migration или окончательный design.

## 12. Неподтверждённые предположения

1. **Предположение:** DB-side processor списывает `quantity` у `from_product_id` и приходует такое же количество `to_product_id`. Основание — названия полей и единый quantity; прямого кода нет.
2. **Предположение:** обработчик асинхронный (worker или trigger с отложенной обработкой), поскольку API ожидает переходы `pending`/`processing`. Trigger/worker не найден, поэтому механизм неизвестен.
3. **Предположение:** `operation_status` имеет DB default `pending`, а `created_at` — default current timestamp. Эти поля читаются, но DDL/default отсутствует.
4. **Предположение:** from/to IDs ссылаются на `products.id`, а warehouse ID — на warehouse table. FK и ограничения не доступны.
5. **Предположение:** общий физический остаток при успешной пересортице сохраняется. Контракт с одним quantity это допускает, но handler может иметь иное поведение.
6. **Предположение:** реальный frontend сначала проверяет quantity и затем вызывает пересортицу. Это записано как вероятный сценарий в `docs/context/frontend_usage_map.md:11`, но клиент/telemetry не найдены.

## 13. Вопросы владельцу процесса

1. Как бизнес определяет успешную пересортицу: обязательны ли равные расход и приход, и может ли операция менять общее количество?
2. Что именно обрабатывает строку `re_sorting_operations` в production: PostgreSQL trigger/function, отдельный worker или иной сервис? Нужны его код/DDL и версия.
3. Какие финальные `operation_status` существуют и какие из них означают успех/ошибку? Должна ли 1С вызываться при каждом финальном статусе или только при business success?
4. Какие таблицы/строки остатков фактически меняет processor и делает ли он обе стороны в одной транзакции?
5. Проверяются ли существование/активность from/to товаров, положительность quantity, различие product IDs и достаточность физического/доступного остатка?
6. Учитываются ли резервы и допускается ли отрицательный остаток?
7. Какая конкурентная семантика требуется для двух пересортиц одного товара/склада: serialization, отказ или последовательное применение?
8. Есть ли production unique/idempotency rule вне репозитория, и как клиент должен безопасно повторять запрос после timeout?
9. Почему `warehouse_id` намеренно исключён из payload 1С и как 1С выбирает склад?
10. Каков подтверждённый контракт ответа `goods_resorting/`, включая HTTP/business errors, и должна ли ошибка 1С менять локальный статус или запускать retry/compensation?
11. Нужна ли пересортица для конкретной партии, контейнера, location или маркированной единицы (КИЗ/СЗ/SRID), либо только для агрегированного товара?
12. Какой account/owner/supplier должен владеть обеими сторонами и разрешена ли смена владельца пересортицей?
13. Является ли `author` доверенным отображаемым именем от клиента или должен определяться из авторизации?
14. Требуется ли сохранять документ/основание, before/after balances и связь с документом 1С для аудита?

## 14. Список изученных файлов

- `main.py`
- `requirements.txt`
- `app/api/v1/endpoints/warehouse_and_balances.py`
- `app/api/v1/endpoints/inventory_transactions.py`
- `app/api/v1/endpoints/__init__.py`
- `app/models/warehouse_and_balances.py`
- `app/models/inventory_transactions.py`
- `app/models/__init__.py`
- `app/service/warehouse_and_balances.py`
- `app/service/inventory_transactions.py`
- `app/database/repositories/warehouse_and_balances.py`
- `app/database/repositories/inventory_transactions.py`
- `app/database/repositories/__init__.py`
- `app/dependencies/warehouse_and_balances.py`
- `app/dependencies/security.py`
- `app/dependencies/config.py`
- `app/dependencies/__init__.py`
- `app/infrastructure/ONE_C/routing.py`
- `docs/context/api_map.md`
- `docs/context/business_rules.md`
- `docs/context/current_state.md`
- `docs/context/database_functions.md`
- `docs/context/database_map.md`
- `docs/context/database_schema.sql`
- `docs/context/database_triggers.md`
- `docs/context/domain_model.md`
- `docs/context/frontend_usage_map.md`
- `docs/context/integration_map.md`
- `docs/context/invariants.md`
- `docs/context/known_issues.md`
- `docs/context/open_questions.md`
- `docs/context/saga_candidates.md`
- `docs/context/sql_audit_queries.sql`
- `docs/context/write_operations_policy.md`
- `tests/test_docs_parser.py`
- Git commits `e876383`, `7f14f31`, `88ff480`, `f8ea7c4`; соответствующие `git log`, `git show`, `git blame`.

Варианты поиска: `re_sorting_operations`, `re_sorting`, `resorting`, `re-sorting`, `пересорт`, `пересортица`, `warehouse_and_balances`, `goods_resorting`, `from_product_id`, `to_product_id`. Альтернативная/отключённая write implementation не найдена; найден только отдельный read endpoint истории.

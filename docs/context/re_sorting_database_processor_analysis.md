# Фактический DB-обработчик `re_sorting_operations`

Дата исследования: 2026-07-15. Исследованы PostgreSQL catalogs настроенной БД и доступные репозитории. Все SQL выполнялись внутри `BEGIN READ ONLY`; значение `SHOW transaction_read_only` было `on`, каждая сессия завершена `ROLLBACK`. Application endpoint не вызывался. Product IDs в примерах заменены необратимыми 8-символьными MD5-префиксами, авторы не выбирались. Имена персональных DB-ролей в отчёте обезличены.

## 1. Краткий вывод

1. Фактический обработчик найден в PostgreSQL: enabled `AFTER INSERT FOR EACH ROW` trigger `public.tr_re_sorting_operation_processing` вызывает `public.process_re_sorting_operation()`.
2. Это не внешний worker: trigger исполняется синхронно внутри SQL statement `INSERT INTO re_sorting_operations` и той же PostgreSQL-транзакции.
3. При успехе функция создаёт две строки `inventory_transactions`: `-Q` типа `re_sorting_outgoing` для исходного товара и `+Q` типа `re_sorting_incoming` для итогового товара, обе на одном складе и со ссылкой на operation ID.
4. Второй enabled trigger `public.tr_transactions_balance` на `inventory_transactions` после каждого INSERT/UPDATE/DELETE вызывает `public.update_physical_balances()` и полностью пересчитывает `current_balances.physical_quantity` как сумму журнала по ключу `(product_id, warehouse_id)`.
5. Обе строки движений, оба пересчёта балансов и финальный status выполняются атомарно как часть исходного INSERT. При необработанном SQL exception весь INSERT, включая operation row, откатывается.
6. Функция блокирует существующие строки `current_balances` исходного, затем итогового товара через `SELECT ... FOR UPDATE`. Единого канонического порядка product IDs нет, поэтому встречные пересортицы A→B и B→A могут вызвать deadlock; PostgreSQL откатит одну транзакцию.
7. Достаточность проверяется по `physical_quantity`, а не `available_quantity`; резервы не уменьшают разрешённое к пересортице количество.
8. При недостатке существующего физического остатка status становится `failed`, движения не создаются. При успехе status становится `completed`.
9. Есть дефект фактической проверки: если source balance row отсутствует, `SELECT ... INTO` не присваивает `0`; `from_balance` остаётся `NULL`, условие недостатка даёт `NULL`, и функция может создать отрицательный исходный баланс.
10. Ни Pydantic, ни table DDL не требуют `quantity > 0`. Ноль создаёт два нулевых движения; отрицательное Q меняет направления знаков и фактически выполняет обратное изменение.
11. FK подтверждают существование from/to product и warehouse для ненулевых значений. Проверок активности товара, account/поставщика, партии, контейнера, location или уникальной единицы нет.
12. В production обнаружено 663 operation rows; единственное фактическое значение status — `completed`. Для каждой из 663 операций есть ровно два движения, их net quantity равен нулю.
13. Polling Python repository при текущем enabled trigger избыточен: к моменту возврата INSERT trigger уже выставил `completed`/`failed`. `processing` не виден другим транзакциям до commit.
14. Внешнего Celery/cron/systemd/RabbitMQ/SQL polling worker для смены status в доступных deployment/repositories не найдено.

## 2. DDL таблицы

Источник: `pg_dump --schema-only --table=public.re_sorting_operations`, подтверждённый `pg_class`, `pg_attribute`, `pg_attrdef`, `pg_constraint`, `pg_indexes`.

```sql
CREATE TABLE public.re_sorting_operations (
    id integer NOT NULL,
    from_product_id character varying(50),
    to_product_id character varying(50),
    warehouse_id integer,
    quantity numeric(15,3),
    reason text,
    created_at timestamp without time zone DEFAULT now(),
    author character varying(150),
    operation_status character varying(20) DEFAULT 'pending'::character varying,
    error_message text,
    CONSTRAINT re_sorting_operations_operation_status_check CHECK (
        operation_status::text = ANY (
            ARRAY['pending', 'processing', 'completed', 'failed']::text[]
        )
    )
);

ALTER TABLE public.re_sorting_operations OWNER TO vector_admin;

CREATE SEQUENCE public.re_sorting_operations_id_seq
    AS integer START WITH 1 INCREMENT BY 1 NO MINVALUE NO MAXVALUE CACHE 1;

ALTER SEQUENCE public.re_sorting_operations_id_seq
    OWNED BY public.re_sorting_operations.id;

ALTER TABLE ONLY public.re_sorting_operations
    ALTER COLUMN id SET DEFAULT
    nextval('public.re_sorting_operations_id_seq'::regclass);

ALTER TABLE ONLY public.re_sorting_operations
    ADD CONSTRAINT re_sorting_operations_pkey PRIMARY KEY (id);

ALTER TABLE ONLY public.re_sorting_operations
    ADD CONSTRAINT re_sorting_operations_from_product_id_fkey
    FOREIGN KEY (from_product_id) REFERENCES public.products(id);

ALTER TABLE ONLY public.re_sorting_operations
    ADD CONSTRAINT re_sorting_operations_to_product_id_fkey
    FOREIGN KEY (to_product_id) REFERENCES public.products(id);

ALTER TABLE ONLY public.re_sorting_operations
    ADD CONSTRAINT re_sorting_operations_warehouse_id_fkey
    FOREIGN KEY (warehouse_id) REFERENCES public.warehouses(id);

ALTER TABLE ONLY public.re_sorting_operations
    ADD CONSTRAINT fk_re_sorting_operations_warehouse
    FOREIGN KEY (warehouse_id) REFERENCES public.warehouses(id) ON DELETE CASCADE;
```

### Свойства DDL

| Свойство | Факт |
|---|---|
| Schema | `public` |
| Owner | `vector_admin` |
| Primary key | `id` |
| Unique constraints | Только PK; business/idempotency unique key отсутствует |
| Status default | `pending` |
| Status CHECK | Только `pending`, `processing`, `completed`, `failed`; колонка nullable |
| Created default | `now()`; колонка nullable |
| Product FK | Оба IDs ссылаются на `products(id)`, без `ON DELETE CASCADE` |
| Warehouse FK | Два дублирующих FK: обычный и `ON DELETE CASCADE` |
| Quantity CHECK | Отсутствует |
| GUID/idempotency | Колонок нет |
| Additional indexes | Нет; только unique btree PK index по `id` |
| Table/column comments | Все `NULL` |

Все business columns nullable на уровне БД, хотя API schema требует шесть входных полей. Дублирующие warehouse FK — фактическое состояние production DDL.

### Privileges

- Owner `vector_admin` имеет все table privileges с grant option.
- `readonly_user` имеет `SELECT`.
- Шесть именованных пользовательских ролей имеют `SELECT, INSERT, UPDATE, DELETE` без grant option; имена скрыты как потенциальные персональные данные.
- Одна из этих ролей имеет `SELECT, USAGE` на sequence; имя скрыто.
- Явных `TRUNCATE`, `REFERENCES`, `TRIGGER` grants не-owner ролям в dump нет.

## 3. Triggers и functions

### Trigger команды пересортицы

```sql
CREATE TRIGGER tr_re_sorting_operation_processing
AFTER INSERT ON public.re_sorting_operations
FOR EACH ROW
EXECUTE FUNCTION public.process_re_sorting_operation();
```

| Атрибут | Значение |
|---|---|
| Timing | `AFTER` |
| Event | `INSERT` |
| Level | `ROW` |
| WHEN condition | Нет |
| Enabled | `O` — enabled for origin/local sessions, обычный enabled status |
| Function | `public.process_re_sorting_operation()` |
| Language | PL/pgSQL |
| Security definer | Нет (`SECURITY INVOKER`) |
| Volatility/parallel | `VOLATILE`, `PARALLEL UNSAFE` |
| Owner | `vector_admin` |

### Смысл `public.process_re_sorting_operation()`

Полное определение получено через `pg_get_functiondef`. Фактический алгоритм:

```text
IF NEW.operation_status = 'pending':
    UPDATE operation SET status='processing'

    SELECT source physical_quantity
      FROM current_balances
      WHERE product_id=from AND warehouse_id=warehouse
      FOR UPDATE

    если to_product_id не NULL:
        SELECT target physical_quantity ... FOR UPDATE

    IF from_balance - quantity < 0:
        UPDATE operation
          SET status='failed', error_message='Недостаточно товара ...', created_at=NOW()
        RETURN

    INSERT inventory_transactions(
        from product, warehouse, status_id=1,
        quantity=-Q, type='re_sorting_outgoing', operation_id, NOW(), author)

    если to_product_id не NULL:
        INSERT inventory_transactions(
            to product, warehouse, status_id=1,
            quantity=+Q, type='re_sorting_incoming', operation_id, NOW(), author)

    UPDATE operation SET status='completed', created_at=NOW()
```

Локальные переменные `new_from_balance` и `new_to_balance` рассчитываются, но далее не используются. Прямого `UPDATE current_balances` эта функция не делает.

### Trigger журнала движений

```sql
CREATE TRIGGER tr_transactions_balance
AFTER INSERT OR DELETE OR UPDATE ON public.inventory_transactions
FOR EACH ROW
EXECUTE FUNCTION public.update_physical_balances();
```

Trigger enabled (`tgenabled='O'`). `update_physical_balances()` для NEW либо OLD ключа `(product_id, warehouse_id)`:

1. Суммирует все подходящие `inventory_transactions`.
2. Для `re_sorting_incoming` и `re_sorting_outgoing` использует уже заданный знак `quantity` без инверсии.
3. Выполняет `INSERT INTO current_balances (...) ... ON CONFLICT (product_id, warehouse_id) DO UPDATE SET physical_quantity=EXCLUDED.physical_quantity`.
4. Отдельно пересчитывает `reserved_quantity` как сумму незавершённых `reservation` transactions.

`current_balances` — обычная таблица, не view/materialized view. PK: `(product_id, warehouse_id)`. `physical_quantity numeric(10,3) NOT NULL DEFAULT 0`, `reserved_quantity numeric(10,3) NOT NULL DEFAULT 0`, а `available_quantity numeric(10,3) GENERATED ALWAYS AS (physical_quantity-reserved_quantity) STORED`.

### Другие зависимости

- `public.get_daily_balances_paginated(...)` считает исторический balance из `inventory_transactions`; оба типа пересортицы суммируются с сохранённым знаком.
- Views и materialized views, чьи definitions содержат `re_sorting_operations`, `from_product_id`, `to_product_id` или `operation_status`, не найдены.
- Catalog dependency на operation table подтверждает trigger, constraints, defaults, sequence и row type.
- `inventory_transactions.re_sorting_operations_id` имеет FK на operation row с `ON DELETE CASCADE`.
- CHECK `inventory_transactions_transaction_type_check` явно разрешает `re_sorting_incoming` и `re_sorting_outgoing`.

## 4. Внешний worker

Внешнего обработчика нет: смену `pending → processing → completed/failed` выполняет PostgreSQL trigger function синхронно.

Повторный поиск выполнен по `/home/skurbick/PROJECTS`, Docker Compose, Dockerfile, Celery, cron/systemd-like filenames, RabbitMQ consumers и SQL worker terms. Имена `process_re_sorting_operation`, `tr_re_sorting_operation_processing`, `update_physical_balances`, `tr_transactions_balance` вне DB catalog не найдены. Основной compose поднимает только `1c_routing_api` и RabbitMQ; отдельного resorting worker нет (`docker-compose.yaml`). Deployment compose в `окружение/1CRoutingAPI` содержит только API service. Соседний `WarehouseOperationsOrchestrator` реализует kit orchestration и не ссылается на пересортицу.

## 5. Фактическая формула и таблицы

Для `Q = re_sorting_operations.quantity`, исходного `F`, итогового `T`, склада `W`:

```text
inventory_transactions(F,W): append quantity = -Q, type = re_sorting_outgoing
inventory_transactions(T,W): append quantity = +Q, type = re_sorting_incoming

current_balances(F,W).physical_quantity = SUM(всех учитываемых движений F,W)
current_balances(T,W).physical_quantity = SUM(всех учитываемых движений T,W)

при Q > 0:
    source delta = -Q
    target delta = +Q
    aggregate net delta = 0
```

| Таблица | Действие | Поля/ключ | Назначение |
|---|---|---|---|
| `re_sorting_operations` | INSERT + UPDATE | PK `id`; status/error/created_at | Command header и бизнес-status |
| `current_balances` | SELECT FOR UPDATE | `(product_id, warehouse_id)` | Проверка source physical stock и блокировка source/target |
| `inventory_transactions` | Два INSERT при успехе | product, warehouse, status=1, signed quantity, type, operation FK, author/time | Неизменяемая в рамках операции пара движений |
| `current_balances` | UPSERT после каждого movement | PK `(product_id, warehouse_id)` | Полный пересчёт physical balance из журнала |
| `current_balances` | UPDATE | тот же PK | Пересчёт reserved quantity |
| `products` | FK read/check | `id` | Существование ненулевых from/to IDs |
| `warehouses` | FK read/check | `id` | Существование ненулевого warehouse ID |

Нулевые balance rows не удаляются. Если итоговой balance row нет, `update_physical_balances` создаёт её через UPSERT. Партии, account, supplier, container, location и unique-unit идентификаторы не используются. Поля `account`, `supply_id` и другие nullable columns `inventory_transactions` функцией не заполняются.

## 6. Проверки и edge cases

### Подтверждённые проверки

- Trigger обрабатывает только NEW row со status `pending`.
- FK проверяют ненулевые product/warehouse IDs.
- Source balance проверяется по `physical_quantity - Q < 0`.
- Status CHECK ограничивает четыре значения.
- `inventory_transactions` FK проверяют product, warehouse, status ID и operation ID.

### Отсутствующие проверки

- Нет `quantity > 0`.
- Нет `from_product_id <> to_product_id`.
- Нет проверки product active flag.
- Нет проверки `available_quantity`; резервы игнорируются при достаточности.
- Нет account/owner/supplier consistency.
- Нет партий, locations, containers, КИЗ/СЗ/SRID.
- Нет idempotency key/unique business constraint.

### Фактические пограничные случаи

1. **Source balance row отсутствует.** `SELECT COALESCE(physical_quantity,0) INTO from_balance ...` не возвращает строку; `COALESCE` не выполняется, переменная остаётся NULL. `NULL - Q < 0` не является TRUE, поэтому функция продолжает и может создать negative source balance через outgoing movement.
2. **Target balance row отсутствует.** `to_balance` также остаётся NULL, но рассчитанный `new_to_balance` не используется. Incoming movement корректно создаёт target balance через UPSERT.
3. **Q = 0.** Проверка проходит, создаются две нулевые transactions и status `completed`.
4. **Q < 0.** Outgoing получает положительное quantity, incoming — отрицательное; операция обращает ожидаемое направление. DDL это разрешает.
5. **From = to.** Обе transactions относятся к одному ключу и в сумме дают ноль; запрета нет. Второй `SELECT FOR UPDATE` повторно запрашивает уже удерживаемую строку.
6. **FK/trigger exception.** В функции нет `EXCEPTION` block. Ошибка откатывает весь outer INSERT; operation row со status `failed` не сохраняется, Python получает PostgreSQL error.
7. **Недостаток существующего остатка.** Function сохраняет operation row как `failed`, записывает подробный error_message и не создаёт movements.

## 7. Транзакционная граница и конкурентность

`AFTER INSERT` row trigger выполняется внутри той же transaction/statement, что и исходный insert. Вызванные им movement INSERTs запускают вложенные balance triggers также внутри этой транзакции. Поэтому атомарная граница включает:

```text
operation INSERT
→ status processing
→ source/target row locks
→ outgoing movement + source balance recalculation
→ incoming movement + target balance recalculation
→ status completed
→ commit исходного statement/transaction
```

При недостатке вместо movement branch сохраняется `failed`. При необработанном exception всё откатывается, включая operation row и `processing` update.

### Locks и параллельность

- `SELECT FOR UPDATE` блокирует существующий source row, затем существующий target row.
- Advisory locks отсутствуют.
- Отсутствующую source/target row этот SELECT не блокирует; последующие UPSERT/FK/unique mechanics обеспечивают только обычные PostgreSQL locks.
- Нет канонического порядка блокировки по product ID. Параллельные A→B и B→A могут взять противоположные первые locks и deadlock. PostgreSQL deadlock detector отменит одну transaction; API получит PostgresError 422, operation row отменённой transaction не сохранится.
- Две операции одного source сериализуются на source balance row. После ожидания вторая SELECT видит committed physical quantity первой и повторно проверяет достаточность.
- Сохранение только одной стороны при обычной SQL error исключается транзакцией trigger chain. Неизвестные внешние effects отсутствуют до последующего вызова 1С.
- `processing` — промежуточное uncommitted значение внутри trigger transaction; обычный внешний observer его не увидит. Финальный status устанавливается перед возвратом outer INSERT.

## 8. Статусы и реальные примеры

### Допустимые и фактические статусы

| Status | Кодовое значение | Значение по функции | Фактический count |
|---|---|---|---:|
| `pending` | Table default; условие запуска trigger | До начала обработки | 0 |
| `processing` | Первый UPDATE trigger | Внутритранзакционный промежуточный status | 0 |
| `completed` | Финальный UPDATE success branch | **Бизнес-успех** | 663 |
| `failed` | Недостаточно source physical quantity | Бизнес-ошибка без movements | 0 |

Других статусов CHECK не допускает. `successful` отсутствует. Бизнес-успех однозначно `completed`, поскольку только этот status устанавливается после обоих movement INSERTs.

### Последние обезличенные операции

| ID | From hash | To hash | Quantity | Warehouse | Status | Error | Created at |
|---:|---|---|---:|---:|---|---|---|
| 663 | `6084aa5c` | `b5018778` | 1.000 | 2 | completed | NULL | 2026-07-14 07:04:16.490467 |
| 662 | `0eb08b8c` | `6779d86a` | 2000.000 | 1 | completed | NULL | 2026-07-09 08:23:27.750257 |
| 661 | `c4b64a0f` | `14b555f1` | 2000.000 | 1 | completed | NULL | 2026-07-09 08:22:41.396307 |
| 660 | `e5e10491` | `1b558c1c` | 4896.000 | 1 | completed | NULL | 2026-07-09 07:25:05.601377 |
| 659 | `eac68468` | `de4f6879` | 1.000 | 2 | completed | NULL | 2026-07-01 06:03:19.768842 |

Для каждой из пяти строк найдены ровно две transactions: outgoing и incoming, одинаковое timestamp, net quantity `0.000`. Агрегат по всем 663 операциям: `not_two_transactions=0`, `nonzero_net=0`; всего 663 outgoing и 663 incoming movements.

`created_at` operation row перезаписывается `NOW()` при `completed` и `failed`, поэтому это фактически время финализации trigger, а не гарантированно исходное время подачи команды.

## 9. Противоречия с предыдущим анализом

Предыдущий отчёт `docs/context/re_sorting_operation_analysis.md` корректно отделял неизвестный DB-side processor, поскольку DDL отсутствует в Git. Read-only production catalog устранил следующие неизвестности:

| Предыдущий вывод/неизвестность | Теперь установленный факт |
|---|---|
| Processor может быть trigger или external worker | Это enabled PostgreSQL AFTER INSERT trigger |
| Формула остатков не подтверждена | Подтверждена пара `-Q/+Q` через `inventory_transactions` |
| Atomicity двух сторон неизвестна | Обе стороны и balance recalculations в outer INSERT transaction |
| Достаточность/резервы неизвестны | Проверяется physical only; reserves игнорируются |
| Отрицательный остаток нельзя подтвердить | При существующей source row предотвращается; при отсутствующей row возможен из-за NULL bug; отрицательный Q также не запрещён |
| Polling может ждать processor | При enabled synchronous trigger INSERT возвращается уже с final status; polling обычно один SELECT |
| Таблицы движений неизвестны | `inventory_transactions` и `current_balances` подтверждены |
| Final business status неизвестен | `completed` — success, `failed` — insufficient stock |

Предыдущие выводы об отсутствии API idempotency, вызове 1С после local DB completion и игнорировании HTTP error status 1С остаются в силе.

## 10. Оставшиеся вопросы владельцу процесса

1. Допустимо ли пересортировать зарезервированный товар, если physical достаточно, а available недостаточно?
2. Должно ли отсутствие source row считаться нулевым остатком и завершаться `failed`?
3. Нужно ли бизнесово запретить `quantity <= 0` и одинаковые from/to products?
4. Почему operation status/created_at перезаписывает исходное время создания; требуется ли отдельный `completed_at`?
5. Нужен ли persisted failed operation для любых SQL/FK/deadlock errors, а не только insufficient stock?
6. Как должен API реагировать на `failed`: не вызывать 1С и вернуть business error либо сохранить HTTP 201?
7. Требуется ли canonical lock ordering или иной policy для встречных A→B/B→A операций?
8. Должны ли account, owner/supplier, партии, контейнеры, locations или маркированные единицы участвовать в пересортице будущего WMS?
9. Почему в production существуют два warehouse FK, один из которых `ON DELETE CASCADE`?
10. Нужна ли idempotency/correlation key, учитывая отсутствие business unique constraint?

## 11. Выполненные read-only SQL-запросы

Каждая группа выполнялась после `BEGIN READ ONLY`; проверено `SHOW transaction_read_only = on`; завершение — `ROLLBACK`.

1. Поиск таблицы/owner/comments в `pg_class` + `pg_namespace`.
2. Колонки/types/nullability/defaults/comments из `pg_attribute`, `pg_attrdef`, `format_type`, `col_description`.
3. PK/FK/UNIQUE/CHECK через `pg_constraint` + `pg_get_constraintdef`.
4. Indexes через `pg_indexes`.
5. Grants через `information_schema.role_table_grants`.
6. Triggers через `pg_trigger`, `pg_proc`, `pg_namespace`, `pg_get_triggerdef`.
7. Trigger functions через `pg_get_functiondef` и properties из `pg_proc`.
8. Direct dependencies через `pg_depend`.
9. Functions/procedures search по `pg_proc`/`pg_get_functiondef` для `re_sorting_operations`, `re_sorting_`, `from_product_id`, `to_product_id`, `operation_status`.
10. Views/materialized views search по `pg_views` и `pg_matviews`.
11. Status aggregate:

```sql
SELECT operation_status, COUNT(*)
FROM public.re_sorting_operations
GROUP BY operation_status
ORDER BY operation_status;
```

12. Последние пять rows с `left(md5(product_id),8)`, без author.
13. DDL/constraints/indexes/triggers `inventory_transactions` и `current_balances` через те же catalogs.
14. Проверка generated/identity properties через `pg_attribute.attgenerated/attidentity`.
15. Correlation operation→movements через LEFT JOIN по `inventory_transactions.re_sorting_operations_id`; только counts/types/signed sum/timestamps.
16. Aggregate всех operations: число rows не с двумя movements и число ненулевых net sums.
17. Counts transaction types только для non-null `re_sorting_operations_id`.
18. `pg_dump --schema-only --table=public.re_sorting_operations` для точного table/sequence/ACL DDL. `pg_dump` выполняет только catalog reads.

Ни один `INSERT`, `UPDATE`, `DELETE`, `CALL`, `REFRESH`, DDL или application endpoint не выполнялся.

## 12. Изученные источники

- Production PostgreSQL catalogs: `pg_class`, `pg_namespace`, `pg_attribute`, `pg_attrdef`, `pg_constraint`, `pg_indexes`, `pg_trigger`, `pg_proc`, `pg_depend`, `pg_views`, `pg_matviews`, `information_schema.role_table_grants`.
- `app/database/repositories/warehouse_and_balances.py`
- `app/service/warehouse_and_balances.py`
- `app/infrastructure/ONE_C/routing.py`
- `app/database/repositories/inventory_transactions.py`
- `app/models/warehouse_and_balances.py`
- `docker-compose.yaml`
- `Dockerfile`
- `/home/skurbick/PROJECTS/окружение/1CRoutingAPI/docker-compose.yaml`
- Доступные compose/deployment/worker-файлы под `/home/skurbick/PROJECTS`.
- `docs/context/re_sorting_operation_analysis.md`

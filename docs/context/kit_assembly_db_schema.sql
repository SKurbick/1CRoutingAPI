/*
Заметки по DB-схеме операции комплектации/разукомплектации.

Важно:
- Production DDL для этих таблиц/views/triggers/functions отсутствует в репозитории.
- docs/context/database_schema.sql явно говорит, что в репозитории есть только неполный DDL.
- SQL ниже НЕ является исполняемым production DDL.
- Он документирует контракт колонок, выведенный из SQL-использования в коде приложения.
*/

/* ============================================================================
   public.kit_operations
   ============================================================================

Выведено из:
- app/database/repositories/warehouse_and_balances.py
- app/database/repositories/inventory_transactions.py

Запись:
  INSERT INTO kit_operations
      (warehouse_id, kit_product_id, operation_type, quantity, author)
      VALUES ($1, $2, $3, $4, $5)
      RETURNING id;

Чтение:
  SELECT kit_product_id AS product_id, status AS operation_status, error_message
  FROM kit_operations
  WHERE id = $1;

Чтение истории:
  SELECT id, kit_product_id, warehouse_id, operation_type, quantity, status,
         author, created_at, DATE(created_at) AS "date"
  FROM kit_operations
  WHERE created_at BETWEEN $1 AND $2
  ORDER BY DATE(created_at), kit_product_id;

Наблюдаемые статусы ожидания:
  pending, processing

Финальные статусы:
  не подтверждено кодом repository.

DDL: не подтверждено:

CREATE TABLE public.kit_operations (
    id             integer/bigint PRIMARY KEY,
    warehouse_id   integer NOT NULL,
    kit_product_id text/varchar NOT NULL,
    operation_type text/varchar NOT NULL, -- ожидается API: assembly|disassembly
    quantity       integer/numeric NOT NULL,
    author         text/varchar NOT NULL,
    status         text/varchar NOT NULL DEFAULT 'pending',
    error_message  text NULL,
    created_at     timestamp/timestamptz NOT NULL DEFAULT now()
);

Возможные constraints/indexes/triggers:
  не подтверждено. Нужен production catalog.
*/

/* ============================================================================
   public.products
   ============================================================================

Выведено из:
- app/database/repositories/warehouse_and_balances.py
- app/database/repositories/goods_information.py
- migrations/return_to_supplier.sql содержит FK на public.products(id), но DDL products отсутствует.

Чтение:
  SELECT kit_components FROM products WHERE id = $1;
  SELECT * FROM products WHERE is_kit = TRUE and is_active = TRUE;
  SELECT * FROM products WHERE is_active = TRUE;
  SELECT * FROM products WHERE id = $1 AND is_active = TRUE;

Запись:
  INSERT INTO products (id, name, is_kit, share_of_kit, kit_components, photo_link)
  VALUES ($1, $2, $3, $4, $5::jsonb, $6);

DDL: не подтверждено:

CREATE TABLE public.products (
    id             text/varchar PRIMARY KEY,
    name           text/varchar NOT NULL,
    is_kit         boolean NOT NULL,
    share_of_kit   boolean NOT NULL,
    kit_components jsonb NULL,
    photo_link     text/varchar NULL,
    is_active      boolean NOT NULL DEFAULT true
);

Возможные constraints/indexes/triggers:
  не подтверждено. Нужен production catalog.
*/

/* ============================================================================
   public.inventory_transactions
   ============================================================================

Код операции комплектации не пишет в эту таблицу напрямую.

Связанный отчёт читает:
  app/database/repositories/inventory_transactions.py агрегирует участие в комплектации:
    transaction_type IN ('kit_disassembly', 'kit_assembly', 'kit_result')

Другой код подтверждает общие колонки:
  product_id, quantity, warehouse_id, author, correction_comment,
  transaction_type, status_id, created_at, delivery_type, document_guid

DDL: не подтверждено:

CREATE TABLE public.inventory_transactions (
    id                  integer/bigint PRIMARY KEY,
    product_id          text/varchar NOT NULL,
    warehouse_id        integer NOT NULL,
    quantity            integer/numeric NOT NULL,
    transaction_type    text/varchar NOT NULL,
    status_id           integer NULL,
    author              text/varchar NULL,
    correction_comment  text NULL,
    delivery_type       text/varchar NULL,
    document_guid       text/varchar NULL,
    created_at          timestamp/timestamptz NOT NULL DEFAULT now()
);

Связанные с комплектами значения `transaction_type`, наблюдаемые в отчётах:
  kit_disassembly
  kit_assembly
  kit_result

Возможные constraints/indexes/triggers:
  не подтверждено. Нужен production catalog.
*/

/* ============================================================================
   public.current_balances
   ============================================================================

Читается `WarehouseAndBalancesRepository.get_all_product_current_balances`.
Может быть table, view или materialized view; не подтверждено.

Наблюдаемые колонки:
  product_id
  warehouse_id
  physical_quantity
  reserved_quantity
  available_quantity

DDL: не подтверждено:

CREATE VIEW public.current_balances AS ...

или

CREATE TABLE public.current_balances (
    product_id          text/varchar NOT NULL,
    warehouse_id        integer NOT NULL,
    physical_quantity   integer/numeric NOT NULL,
    reserved_quantity   integer/numeric NOT NULL,
    available_quantity  integer/numeric NOT NULL
);

Возможные constraints/indexes/triggers:
  не подтверждено. Нужен production catalog.
*/

/* ============================================================================
   public.product_availability
   ============================================================================

Читается `WarehouseAndBalancesRepository.get_valid_stock_data`.
Endpoint операции комплектации её не вызывает, но таблица/view связана с доступностью комплектов.
Может быть table, view или materialized view; не подтверждено.

Наблюдаемые колонки:
  product_id
  name
  is_kit
  available_stock
  components_info -- JSON string/list с component_id, required, available

DDL: не подтверждено:

CREATE VIEW public.product_availability AS ...
*/

/* ============================================================================
   public.warehouses
   ============================================================================

`warehouse_id` хранится в `kit_operations`.
`WarehouseAndBalancesRepository.get_warehouses` читает:
  SELECT * FROM warehouses;

Наблюдаемые поля ответа:
  id
  name
  address

DDL: не подтверждено:

CREATE TABLE public.warehouses (
    id      integer PRIMARY KEY,
    name    text/varchar NOT NULL,
    address text/varchar NULL
);
*/

/* ============================================================================
   Triggers / functions / indexes / constraints
   ============================================================================

DDL trigger/function для `kit_operations` или мутации остатков в репозитории отсутствует.

Косвенно требуемое поведение:
- После INSERT в `kit_operations` что-то меняет статус с pending или
  processing.
- Этот же или связанный DB-side процесс может писать `inventory_transactions` и/или
  обновлять/refresh balances, но точный SQL не подтверждено.

Известная документация репозитория:
- docs/context/database_triggers.md говорит, что DDL триггеров отсутствует, а точный механизм
  может быть trigger, external DB worker или другой процесс.
- docs/context/database_functions.md документирует только get_daily_balances_paginated
  и говорит, что другие trigger functions отсутствуют.

Audit query для запуска на production DB находится в:
- docs/context/sql_audit_queries.sql
*/

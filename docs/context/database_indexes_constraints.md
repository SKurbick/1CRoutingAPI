# Индексы и ограничения

Подтверждено `migrations/return_to_supplier.sql`:

- `return_to_supplier.id SERIAL PRIMARY KEY`;
- indexes: `guid`, `is_valid`, `local_vendor_code`;
- `return_to_supplier_items.id SERIAL PRIMARY KEY`;
- FK `product_id -> public.products(id) ON DELETE CASCADE`;
- indexes: `guid`, `product_id`, `is_valid`;
- required: item `guid/product_id/quantity/is_valid/created_at`.

Из SQL-кода предполагается unique constraint `sticker_generation_task_users(task_id,user_id)` (иначе `ON CONFLICT` без target failure semantics отличается), а также conflict targets for localisation/importers/manufacturers/user-data. Их DDL не представлен.

Проверка identity fields:

| Поле | Встречается | Unique подтверждён |
|---|---|---|
| `operation_id` | report models/DB ids | нет |
| `order_id` | returns/reserves/orders | нет |
| `external_id` | не найден | n/a |
| `document_id` | не найден как общий identity | n/a |
| `supply_id` | shipment/FBO | нет |
| `request_id` | не найден | n/a |
| `idempotency_key` | не найден | n/a |
| `guid` | integration documents | indexes есть лишь для return-to-supplier, unique нет |
| `srid` | returns | unique не подтверждён |

Потенциально нужны после data audit: partial unique active document keys; unique `wms.receipt_items(guid,product_id)`; indexes on status/created_at for polling/tasks; `srid`; reserve order/supply. Добавлять без production schema/query plans нельзя.

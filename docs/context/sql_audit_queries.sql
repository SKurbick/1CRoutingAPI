-- Только read-only audit. Рекомендуется выполнять в read-only transaction:
-- BEGIN TRANSACTION READ ONLY; ... ROLLBACK;

-- 1. Полный список пользовательских triggers и функций, которых нет в репозитории.
SELECT n.nspname AS schema_name, c.relname AS table_name, t.tgname,
       pg_get_triggerdef(t.oid) AS definition
FROM pg_trigger t
JOIN pg_class c ON c.oid = t.tgrelid
JOIN pg_namespace n ON n.oid = c.relnamespace
WHERE NOT t.tgisinternal
ORDER BY 1, 2, 3;

-- 2. Constraints/indexes ключевых таблиц.
SELECT schemaname, tablename, indexname, indexdef
FROM pg_indexes
WHERE tablename IN (
  'return_to_supplier','return_to_supplier_items','goods_returns_dev',
  'incoming_returns','product_reserves','fbs_reserves','fbo_reserves',
  'sticker_generation_tasks','sticker_generation_task_users','receipt_items'
)
ORDER BY tablename, indexname;

-- 3. Дубли активных строк входящих документов по guid.
SELECT guid, count(*) AS active_rows
FROM return_to_supplier
WHERE is_valid IS TRUE
GROUP BY guid, local_vendor_code
HAVING count(*) > 1;

-- 4. Дубли активных financial строк (строки платежа могут быть легитимно множественными;
-- сравнивается полный бизнес-ключ строки).
SELECT guid, payment_object, amount, count(*)
FROM cash_disbursement_order
WHERE is_valid IS TRUE
GROUP BY guid, payment_object, amount
HAVING count(*) > 1;

-- 5. Return-to-supplier items без product.
SELECT rtsi.id, rtsi.guid, rtsi.product_id
FROM return_to_supplier_items rtsi
LEFT JOIN products p ON p.id = rtsi.product_id
WHERE p.id IS NULL;

-- 6. Goods returns со ссылкой на отсутствующий incoming return.
SELECT grd.srid, grd.incoming_return_id
FROM goods_returns_dev grd
LEFT JOIN incoming_returns ir ON ir.id = grd.incoming_return_id
WHERE grd.incoming_return_id IS NOT NULL AND ir.id IS NULL;

-- 7. Один srid встречается более одного раза.
SELECT srid, count(*)
FROM goods_returns_dev
GROUP BY srid
HAVING count(*) > 1;

-- 8. Полученные returns без incoming_return_id.
SELECT srid, created_at
FROM goods_returns_dev
WHERE is_received IS TRUE AND incoming_return_id IS NULL;

-- 9. Незавершённая пересортица старше часа.
SELECT id, operation_status, created_at
FROM re_sorting_operations
WHERE operation_status IN ('pending','processing')
  AND created_at < now() - interval '1 hour'
ORDER BY created_at;

-- 10. Незавершённая комплектация старше часа.
SELECT id, status, created_at
FROM kit_operations
WHERE status IN ('pending','processing')
  AND created_at < now() - interval '1 hour'
ORDER BY created_at;

-- 11. Дубли receipt markers WMS: повторный movement возможен.
SELECT guid, product_id, count(*), sum(quantity) AS quantity
FROM wms.receipt_items
GROUP BY guid, product_id
HAVING count(*) > 1;

-- 12. WMS receipt marker без product.
SELECT ri.*
FROM wms.receipt_items ri
LEFT JOIN products p ON p.id = ri.product_id
WHERE p.id IS NULL;

-- 13. Отрицательные inventory movements.
SELECT id, product_id, warehouse_id, quantity, transaction_type, created_at
FROM inventory_transactions
WHERE quantity < 0;

-- 14. Подозрительные current balances.
SELECT *
FROM current_balances
WHERE physical_quantity < 0 OR reserved_quantity < 0 OR available_quantity < 0
   OR available_quantity > physical_quantity;

-- 15. Orphan task-user links.
SELECT stu.*
FROM sticker_generation_task_users stu
LEFT JOIN sticker_generation_tasks st ON st.id = stu.task_id
WHERE st.id IS NULL;

-- 16. Старые активные sticker tasks (названия статусов сверить с production).
SELECT id, uuid, status, created_at
FROM sticker_generation_tasks
WHERE status IN ('pending','processing')
  AND created_at < now() - interval '1 hour';

-- 17. Active financial document rows, для которых одновременно есть несколько версий
-- с различным document_number. Требует ручной интерпретации.
SELECT guid, count(DISTINCT document_number_1c) AS document_numbers
FROM income_on_bank_account
WHERE is_valid IS TRUE
GROUP BY guid
HAVING count(DISTINCT document_number_1c) > 1;

-- 18. В репозитории нет integration log/outbox table. Найти возможные таблицы,
-- созданные вне migrations.
SELECT table_schema, table_name
FROM information_schema.tables
WHERE table_name ILIKE ANY (ARRAY['%outbox%','%integration%log%','%request%log%','%operation%log%'])
ORDER BY 1,2;

-- 19. FK без supporting index (кандидаты; результат требует анализа).
SELECT conrelid::regclass AS table_name, conname,
       pg_get_constraintdef(oid) AS constraint_definition
FROM pg_constraint
WHERE contype = 'f'
ORDER BY 1,2;

-- 20. Статусы в операционных таблицах для сверки допустимых значений.
SELECT 're_sorting_operations' AS source, operation_status AS status, count(*)
FROM re_sorting_operations GROUP BY operation_status
UNION ALL
SELECT 'kit_operations', status, count(*) FROM kit_operations GROUP BY status
ORDER BY 1,2;

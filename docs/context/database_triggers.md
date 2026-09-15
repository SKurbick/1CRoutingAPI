# Триггеры

DDL triggers в репозитории отсутствует.

Косвенно подтверждена DB-side обработка:

- insert `re_sorting_operations` -> код ожидает, что `operation_status` уйдёт из `pending/processing`;
- insert `kit_operations` -> аналогично ожидаются `status/error_message`;
- inventory/reserve tables формируют derived balances.

Это может быть trigger, external DB worker или иной процесс; точный механизм неизвестен.

`LocalBarcodeGenerationRepository.add_barcode_data` выполняет `ALTER TABLE temp_barcode_data DISABLE TRIGGER ALL`; включение и область блокировки должны быть проверены в полном методе и рабочей БД. Риск: отключение constraints/side effects для параллельных sessions или отсутствие re-enable после exception.

Для audit нужен read-only запрос к `pg_trigger`/functions на рабочей БД; он приведён в `sql_audit_queries.sql`.

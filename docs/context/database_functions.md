# Функции PostgreSQL

## `get_daily_balances_paginated`

- Вызов: `WarehouseAndBalancesRepository.get_historical_stocks`.
- Параметры по вызову: `page_size, page_num, date_from, date_to, product_id, warehouse_id`.
- Ожидаемые поля результата: `transaction_date`, `end_of_day_balance`, `product_id`.
- Смысл: дневная история остатков с пагинацией.
- DDL, schema, исключения и изменяемые объекты отсутствуют. По использованию функция считается read-only, но это не доказано определением.

Других явных вызовов PostgreSQL functions/procedures в repository не найдено. Trigger functions существуют фактически либо вне репозитория: операции ждут изменения statuses, но их имена/DDL неизвестны.

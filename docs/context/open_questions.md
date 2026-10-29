# Открытые вопросы

1. Кто владеет каждой `public.*` и `wms.*` таблицей? Нужно для service boundaries и декомиссии.
2. Каков полный production DDL, triggers/functions и search_path? Без него нельзя доказать constraints/status transitions.
3. Что обрабатывает `kit_operations` и `re_sorting_operations`: trigger или worker? Важно для timeout/retry/ownership.
4. Какие active endpoints реально вызывает 1С, frontend и другие services? Нужно для safe removal.
5. Есть ли у 1С идемпотентность по guid/supply и API проверки состояния/отмены? Определяет recovery strategy.
6. Какие WMS operations являются idempotent и существует ли compensation/reversal? Важно для receipt partial failure.
7. Гарантированы ли uniqueness `guid`, `srid`, order/supply IDs и WMS receipt pair? Код этого не доказывает.
8. Какие statuses финальные для kit/resorting/orders/returns и допустим ли rollback?
9. Как повторяются зависшие sticker/1С/WMS operations; настроены ли broker DLQ/TTL/retry вне кода?
10. Где аналоги reserves, returns, kit, resorting, КИЗ, СЗ и shipment sticker в WMS?
11. Что именно команда называет «СЗ» и «уникальной единицей товара» в данном домене?
12. Какие процессы frontend выполняет несколькими calls в 1CRoutingAPI и WMS?
13. Почему API auth dependency отключена и какая защита есть на gateway/network?
14. Содержит ли production schema integration/outbox logs, отсутствующие в repository?
15. Какой утверждённый порядок вывода 1CRoutingAPI и кто owner миграции контрактов 1С/frontend?

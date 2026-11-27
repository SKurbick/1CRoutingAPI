# Карта БД

Полный catalog/DDL отсутствует. Ниже — таблицы и views/functions, реально упомянутые SQL. Schema без prefix трактуется как `search_path` (вероятно public), но это требует подтверждения.

| Группа | Объекты | Кто читает/пишет |
|---|---|---|
| Catalog | `products`, `products_data`, `article`, `warehouses`, `seller_account` | goods, dimensions, orders, docs, returns |
| Stock | `inventory_transactions`, `current_balances`, `product_availability` | warehouse, shipment, WMS checks |
| Orders/receipt | `ordered_goods_from_buyers`, `goods_acceptance_certificate`, `nested_box`, `local_barcode_data`, `supply_to_sellers_warehouse` | order/receipt/barcode repositories |
| Shipment/reserve | `shipment_of_goods`, `fbs_reserves`, `fbo_reserves`, `product_reserves` | shipment repository |
| Returns | `goods_returns_dev`, `goods_returns_status_history`, `incoming_returns`, `goods_returns_mark_list`, `kiz_returns_outbox`, `return_to_supplier`, `return_to_supplier_items` | return repositories; KIZ outbox worker |
| Operations | `kit_operations`, `re_sorting_operations`, `inventory_checks` | warehouse/inventory reports; DB processor |
| Finance | `income_on_bank_account`, `write_off_of_non_cash_funds`, `cash_disbursement_order`, `cash_flow_writeoffs` | financial input routes |
| Sticker | `stickers_storage`, `localisation`, `sticker_user_data`, `sticker_user_data_individual`, `manufacturers`, `importers`, `sticker_generation_tasks`, `sticker_generation_task_users` | sticker API/consumer |
| Packaging | `containers` | containers/dimensions |
| Shared order state | `assembly_task`, `order_status_log`, `historical_statuses_of_assembly_tasks` | reserve-status endpoint |
| WMS-owned/shared | `wms.inventory`, `wms.locations`, `wms.receipt_items` | WMSIntegrationService/repository |
| Security | `vector_services_api_keys` | unused auth dependency |

DDL для `return_to_supplier` и `return_to_supplier_items` находится в соответствующей миграции; также есть миграции `manual_sticker_returns.sql` и `kiz_returns_outbox.sql`. Последняя создаёт JSONB payload, время отправки, attempts/next_attempt_at/last_error и частичный индекс неотправленных заданий. `current_balances` и `product_availability` могут быть view/materialized view/table — код не позволяет определить.

Владение большинством объектов не задано. `wms.*` явно относится к WMS namespace, но 1CRoutingAPI пишет `wms.receipt_items`, нарушая чистую service boundary.

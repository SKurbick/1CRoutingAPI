# Доменная модель

ORM нет; модель восстановлена по Pydantic и SQL.

| Сущность | Поля/статусы | Хранение и lifecycle |
|---|---|---|
| Товар | `id`, name, `is_kit`, components, active | `products`; создаётся/read, удаления нет |
| Остаток | product, warehouse, physical/reserved/available | `inventory_transactions`, derived `current_balances` |
| Резерв/отгрузка | order/supply, delivery type, quantity, fulfilled | `fbs_reserves`, `fbo_reserves`, `product_reserves`, `shipment_of_goods` |
| Поступление 1С | guid, document metadata, items, `is_valid` | receipt repository; затем WMS |
| Приёмка | order/product, boxes, barcode, author | `goods_acceptance_certificate`, `nested_box`, barcode tables |
| Заказ поставщику | guid, items, acceptance/print flags | `ordered_goods_from_buyers` |
| Возврат покупателя | `srid`, latest status, `is_received`, marks | `goods_returns_dev`, history, `incoming_returns`, mark list |
| Возврат поставщику | guid, supplier, item, quantity, `is_valid` | `return_to_supplier(_items)` |
| Комплектация | kit, assembly/disassembly, quantity, status | `kit_operations`; status меняет DB-side logic |
| Пересортица | from/to product, quantity, pending/processing/final | `re_sorting_operations` |
| Инвентаризация | warehouse/product/quantity | `inventory_checks` append |
| Финансовый документ | guid, document/status, payment rows, valid | financial tables, versioning |
| Sticker task | type, hash/UUID, status, result, users | RabbitMQ + task tables + S3/Redis |
| Контейнер | dimensions, volume, pallet count, active | CRUD `containers` |

Удаление реализовано только для containers. Для документов используется `is_valid`. Полный перечень допустимых статусов в репозитории не определён.

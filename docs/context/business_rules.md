# Бизнес-правила

1. Повторная выгрузка документа инвалидирует строки того же `guid`, затем вставляет новую версию (`ReceiptOfGoodsRepository`, financial repositories, return-to-supplier).
2. Return-to-supplier balance items создаются только для существующих `products.id`; supplier `9714053621` исключён.
3. Receipt сначала сохраняется в основной БД, затем синхронизирует WMS. WMS error не отменяет успех и попадает в `details`.
4. WMS receipt пропускает неизвестные products; фильтр по event status отключён. Новая позиция создаёт bulk `receive`, correction — отдельное movement с проверкой остатка.
5. Incoming receipt сначала пишет БД, затем отправляет `inc_invoice/` в 1С.
6. Incoming return одной транзакцией создаёт `incoming_returns`, связывает все `srid`, пишет mark list; после commit вызывает `goods_return/`.
7. Комплектация/пересортица вставляет command и busy-wait читает статус DB-side processor; после успеха уведомляет 1С.
8. Брак создаёт парные outgoing/incoming в одной транзакции.
9. FBO shipment после DB success группируется по account+supply и отправляется в `commission_sales_fbo/`; ошибка только печатается.
10. FBS/FBO reserve/write-off изменяют reserve/shipment tables; idempotency key отсутствует.
11. Sticker generation переиспользует task по unique key, публикует RabbitMQ, consumer завершает task; task-user insert использует `ON CONFLICT DO NOTHING`.
12. Container dimensions положительны по Pydantic; product dimensions используются для packaging calculation.
13. WB docs endpoint читает tokens из `seller_account`, скачивает ZIP/PDF и парсит документы.

Retry и компенсации не реализованы. HTTP response status 1С не переводится в доменный результат.

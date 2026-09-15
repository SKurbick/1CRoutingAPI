# Инварианты

| Инвариант | Обеспечение | Последствие |
|---|---|---|
| Product для return-to-supplier item существует | FK миграции | insert rejected |
| Активна одна версия guid | update-before-insert, только код | две active версии при race/failure |
| Брак имеет две стороны | code + transaction | расхождение складов |
| `srid` связан с одним incoming return | transaction, uniqueness не подтверждена | двойная приёмка |
| Task-user не дублируется | `ON CONFLICT`, constraint предполагается | дубли notices |
| Container dimensions > 0 | Pydantic | неверный расчёт |
| WMS receipt не повторяется | lookup guid+product; unique не подтверждён | двойной receive |
| External request only once | нигде | двойное списание/документ |
| DB согласована с 1С/WMS | нигде | расхождение систем |
| Quantity положительно | не для всех моделей/DB | отрицательный остаток |
| Status не откатывается | DDL/triggers отсутствуют | неверный lifecycle |

Общего межсервисного `operation_id` нет. `idempotency_key` и `request_id` не найдены.

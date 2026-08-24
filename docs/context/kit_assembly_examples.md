# Примеры комплектации / разукомплектации

Эти примеры составлены по application-схемам и SQL-использованию. Это не production payloads, снятые из логов. Любое поведение, которое не подтверждено кодом напрямую, помечено как не подтверждено.

## Запрос на комплектацию

Endpoint:

```http
POST /api/warehouse_and_balances/assembly_or_disassembly_metawild
Content-Type: application/json
```

Тело запроса:

```json
{
  "metawild": "metawild_test",
  "count": 3,
  "author": "Ваня который соска",
  "warehouse_id": 1,
  "operation_type": "assembly"
}
```

Источник: `example_assembly_metawild_data` в `app/models/warehouse_and_balances.py`.

## Запрос на разукомплектацию

```json
{
  "metawild": "metawild_test",
  "count": 3,
  "author": "Ваня который соска",
  "warehouse_id": 1,
  "operation_type": "disassembly"
}
```

Значения `operation_type` ограничены Pydantic: только `assembly` или `disassembly`.

## Ожидаемый INSERT в `kit_operations`

SQL, который выполняет repository:

```sql
INSERT INTO kit_operations
(warehouse_id, kit_product_id, operation_type, quantity, author)
VALUES
($1, $2, $3, $4, $5)
RETURNING id;
```

Для запроса на комплектацию параметры будут такими:

```text
$1 = 1
$2 = 'metawild_test'
$3 = 'assembly'
$4 = 3
$5 = 'Ваня который соска'
```

Ожидаемая форма строки после insert, по полям, которые затем читаются:

```text
id              = сгенерировано БД
warehouse_id    = 1
kit_product_id  = 'metawild_test'
operation_type  = 'assembly'
quantity        = 3
author          = 'Ваня который соска'
status          = pending/processing изначально, точный default не подтверждено
error_message   = null изначально, не подтверждено
created_at      = сгенерировано БД, не подтверждено
```

Значения по умолчанию и constraints не подтверждено, потому что production DDL отсутствует.

## Ответ polling статуса из БД

Repository выполняет polling:

```sql
SELECT kit_product_id AS product_id, status AS operation_status, error_message
FROM kit_operations
WHERE id = $1;
```

Пример формы успешного DB-ответа:

```json
{
  "product_id": "metawild_test",
  "operation_status": "completed",
  "code_status": 201,
  "error_message": null
}
```

`completed` приведён только как иллюстративный финальный статус; реальные финальные статусы не подтверждено кодом. Подтверждённые статусы ожидания: `pending` и `processing`.

Пример формы DB-ошибки от repository:

```json
{
  "product_id": "metawild_test",
  "operation_status": "PostgresError",
  "code_status": 422,
  "error_message": "..."
}
```

Endpoint преобразует это в HTTP error, потому что `code_status >= 400`.

## Чтение состава комплекта

SQL:

```sql
SELECT kit_components FROM products WHERE id = $1;
```

Пример данных `products`, которые нужны коду:

```text
id              = 'metawild_test'
name            = 'Губо-закаточная машинка'
is_kit          = true
is_active       = true
kit_components  = {"testwild": 2, "testwild2": 1}
```

Это соответствует примерам в `app/models/goods_information.py`.

## Payload, уходящий в 1С

Service исключает `warehouse_id` и преобразует `kit_komponents` из dict в list.

Комплектация:

```json
{
  "author": "Ваня который соска",
  "metawild": "metawild_test",
  "count": 3,
  "operation_type": "assembly",
  "kit_komponents": [
    {
      "product_id": "testwild",
      "quantity": 2
    },
    {
      "product_id": "testwild2",
      "quantity": 1
    }
  ]
}
```

Разукомплектация:

```json
{
  "author": "Ваня который соска",
  "metawild": "metawild_test",
  "count": 3,
  "operation_type": "disassembly",
  "kit_komponents": [
    {
      "product_id": "testwild",
      "quantity": 2
    },
    {
      "product_id": "testwild2",
      "quantity": 1
    }
  ]
}
```

Важные подтверждённые детали:

- `warehouse_id` не отправляется в 1С.
- Написание `kit_komponents` взято из service code.
- Количества компонентов не умножаются на `count` перед отправкой.
- `kit_operations.id` не отправляется в 1С.

## Запрос в 1С

```http
POST {ONE_C_BASE_URL}ass_disass/
Authorization: Basic <ONE_C_LOGIN:ONE_C_PASSWORD>
Content-Type: application/json
```

Timeout: для этого метода не задан.

Retry: не реализован.

## Обработка ответа 1С

Клиент читает текст ответа:

```python
json_response = await response.text()
return json_response
```

Service игнорирует возвращённый текст. Ни одна строка `kit_operations` не обновляется по ответу 1С.

Пример успешного ответа 1С:

```text
не подтверждено
```

Пример ответа 1С с ошибкой:

```text
не подтверждено
```

HTTP 4xx/5xx от 1С не обрабатывается текущим client code как application error, если только сам `aiohttp` не выбросит exception.

## Ожидаемые изменения остатков

Подтверждено только на уровне отчёта:

```sql
SUM(CASE
    WHEN it.transaction_type in ('kit_disassembly', 'kit_assembly', 'kit_result')
    AND it.warehouse_id = 1 THEN it.quantity
    ELSE 0
END)::INTEGER AS "Участие в сборке/разборе"
```

Ожидаемая бизнес-интерпретация, не подтверждено SQL/DDL:

- Комплектация должна уменьшать компоненты и увеличивать товар-комплект.
- Разукомплектация должна уменьшать товар-комплект и увеличивать компоненты.

Точные строки не подтверждено. Возможный набор строк для комплектации может использовать transaction types `kit_assembly` и/или `kit_result`, но код не показывает DB-side SQL, который создаёт эти строки.

Не использовать следующее как подтверждённое production-поведение:

```text
комплектация, count=3, components {"testwild": 2, "testwild2": 1}

Возможно, но не подтверждено:
- testwild уменьшается на 6
- testwild2 уменьшается на 3
- metawild_test увеличивается на 3
```

```text
разукомплектация, count=3, components {"testwild": 2, "testwild2": 1}

Возможно, но не подтверждено:
- metawild_test уменьшается на 3
- testwild увеличивается на 6
- testwild2 увеличивается на 3
```

Чтобы подтвердить знаки, transaction types, validation и обновление остатков, нужен production SQL триггера/function/worker.

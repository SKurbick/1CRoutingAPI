# Кандидаты на Orchestrated Saga

## Receipt DB + WMS

Инициатор: 1С через receipt update. Шаги: A — local receipt version; B — WMS bulk movements; C — marker rows. Failure B/C оставляет partial state. Компенсация WMS API не найдена. Нужны `operation_id`, idempotent bulk movement, status endpoint, outbox и states `RECEIVED/DB_SAVED/WMS_PENDING/WMS_DONE/PARTIAL/FAILED`.

## Incoming return DB + 1С

Инициатор предположительно frontend. A — local return/marks/`srid`; B — 1С `goods_return/`. A атомарен, B нет. Нужны request key, durable dispatch, query/reconcile endpoint; возможность отмены A/1С неизвестна.

## Incoming receipt DB + 1С

A — local incoming receipt; B — `inc_invoice/`. Аналогичные требования: operation record, idempotent 1С contract, retry with backoff, state query.

## Kit/resorting DB processor + 1С

A — insert command; B — DB-side balance processor; C — 1С. Текущий owner фактически размыт между API и DB trigger. Нужны bounded wait, durable status, idempotent command and 1С dispatch. Отдельный orchestrator оправдан только если DB processor/WMS станут отдельными services.

## FBO shipment + 1С

A — reserve/shipment DB; B — grouped commission sale in 1С. B exception swallowed. Нужны stable operation per account+supply, external document identity, reconciliation and states `LOCAL_DONE/ONE_C_PENDING/ONE_C_DONE/UNKNOWN/FAILED`.

Saga не объявляется обязательной: transactional outbox + idempotent consumers может быть проще для двухшаговых flows.

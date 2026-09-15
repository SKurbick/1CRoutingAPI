# Известные проблемы

| Проблема | Код/сценарий | Последствие | Критичность/обход/направление |
|---|---|---|---|
| API без effective auth | routers; вызвать write endpoint без token | несанкционированная запись | critical; network ACL; подключить dependency |
| DB commit перед 1С/WMS | receipt/return/shipment/warehouse services | partial success | critical; ручная сверка; outbox/idempotency |
| FBO 1С error swallowed | `ShipmentOfGoodsService` | ложный success | high; logs; durable operation state |
| Busy loop без sleep/timeout | resorting repository (и сходный kit flow) | CPU/DB load, hanging request | high; restart; bounded async polling/job |
| 1С timeout отсутствует у 4/5 calls | `ONE_C/routing.py` | hanging resources/unknown result | high; proxy timeout; explicit timeout+reconcile |
| Financial invalidation/insert неатомарны | financial/cash repositories | no active version/data loss | high; replay; one transaction |
| Return-to-supplier two transactions | repository | headers/items mismatch | high; replay guid; one transaction |
| WMS movement before marker | WMS service | marker failure -> duplicate movement on repeat | critical; WMS query/manual audit; idempotency key |
| No correlation/operation ID | all flows | incident reconciliation difficult | high; logs search; propagate ID |
| Status in body differs HTTP | endpoint/repository responses | caller may treat failure as success | medium-high; inspect body; raise HTTPException |
| Trigger/schema missing | repository vs migrations | unsafe changes/deploy mismatch | high; DB introspection; version full migrations |
| Trigger disable in barcode path | local barcode repository | hidden global side effects | high; maintenance isolation; avoid DISABLE ALL |
| Logs/print may include payload | services/ONE_C | personal/business data exposure | medium-high; restrict logs; structured redaction |
| No broker DLQ/retry policy in code | topology | lost/stuck sticker tasks | high; task reconciliation; configure DLQ |
| Permissive CORS | `main.py` | broad browser origin access | medium; gateway controls; allowlist |
| Background pool task unmanaged | `init_db` create_task | shutdown leak/noisy DB load | medium; lifecycle task handle/cancel |

Полные reproduction tests отсутствуют; сценарий каждой проблемы следует непосредственно из порядка statements/calls.

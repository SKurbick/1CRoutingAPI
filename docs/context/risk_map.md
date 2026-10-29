# Карта рисков

| Риск | Компонент | Вероятность | Последствия | Критичность | Защита сейчас | Рекомендация |
|---|---|---:|---|---|---|---|
| Двойное movement/списание | WMS/FBS | высокая | неверный остаток | critical | weak lookup | idempotency key + unique |
| Двойной документ 1С | outbound HTTP | средняя | финансовое/складское расхождение | critical | неизвестно у 1С | stable external ID |
| DB/1С расходятся | all outbound | высокая | manual reconciliation | critical | logs only | outbox + reconcile |
| DB/WMS расходятся | receipt | высокая | stock mismatch | critical | details/log | durable saga/status |
| Timeout с unknown result | 1С/WMS | высокая | unsafe retry | high | partial timeouts | query by operation ID |
| Потеря Rabbit message | sticker | средняя | stuck task | high | durable queues/tasks | confirms, DLQ, sweeper |
| Partial financial version | finance repos | средняя | missing active doc | high | none | transaction + partial unique |
| Direct shared table change | public/wms | высокая | cross-service breakage | high | none | ownership/API boundary |
| Unauthorized mutation | API | высокая if exposed | arbitrary stock/finance update | critical | perimeter unknown | auth + scopes |
| No audit/correlation | all | высокая | slow incident response | high | author/prints | structured audit IDs |
| Status history incomplete | operations | средняя | cannot prove lifecycle | high | some history tables | append-only state history |
| Negative/invalid quantity | models/DB | средняя | balance corruption | high | inconsistent validation | API+DB CHECK |

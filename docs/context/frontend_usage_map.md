# Использование frontend

Frontend-репозитория, route names/screens и telemetry нет. Ниже — только вероятные операторские сценарии по API semantics.

| Сценарий | Endpoint sequence | Частичный успех |
|---|---|---|
| Отгрузка | get params/reserved -> create reserve -> add shipped; либо compound shipment endpoint | отдельные calls могут оставить reserve без shipment |
| Приёмка закупки | get buyer orders -> local barcode update -> acceptance status | падение status update оставит созданную приёмку |
| Возврат | get return goods -> incoming returns | DB может быть успешна при failure 1С |
| Комплектация | get balances -> assembly/disassembly -> history | DB operation может завершиться, 1С — нет |
| Пересортица | quantity check -> re_sorting -> history | аналогично |
| Стикер | get template -> generate -> SSE/tasks -> download | publish/consumer/S3 могут завершиться частично |
| Упаковка | containers CRUD -> product dimensions update | две независимые сущности |

Compound shipment endpoint уже сокращают число frontend calls. Для остальных объединение через orchestrator имеет смысл только после подтверждения реальных frontend sequences.

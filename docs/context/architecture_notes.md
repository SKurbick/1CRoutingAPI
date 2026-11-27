# Архитектура

`main.py` создаёт `FastAPI(lifespan=...)`, регистрирует доменные router и monitoring. Lifespan создаёт pool `asyncpg`, Redis (или disabled client), S3 client и Rabbit broker; при `CONSUMERS_START=true` запускает FastStream consumers. Объекты находятся в `app.state`; `app/dependencies/` собирает repository/service.

```text
HTTP: Endpoint -> Depends(service) -> service -> repository/raw SQL -> PostgreSQL
Consumer: Rabbit DOCGEN_EVENT -> handle_responses_* -> StickerGenerationService
         -> sticker_generation_tasks -> Redis notification
Background: init_db -> asyncio.create_task(monitor_pool) -> pg_stat_activity / 30 sec
KIZ: receipt DB transaction -> kiz_returns_outbox -> lifespan worker
     -> separate RabbitMQ (RABBITMQ_URL) -> wms.events / wms.kiz_returns
1С: DB operation/commit -> ONECRouting/aiohttp BasicAuth -> 1С
WMS: receipt DB commit -> WMS HTTP movement -> wms.receipt_items marker
```

Транзакции локальны repository. Bulk writes часто используют `conn.transaction()`, но финансовые invalidation+insert и две части return-to-supplier не образуют общей транзакции. Для КИЗов реализован transactional outbox с `FOR UPDATE SKIP LOCKED`, publisher confirms и повторными попытками; distributed transaction нет. Обработчик запускается без подключения к брокеру, отменяется до закрытия DB pool. Подробнее: `kiz_returns_outbox.md`.

Клиент 1С создаёт новую `ClientSession` на вызов; timeout задан только FBO (60 s). WMS использует `httpx` timeout 30 s. Retry нет. Ответы 1С обычно читаются как text без проверки business success.

Middleware: metrics, SlowAPI, permissive CORS. `AuthService`/`verify_service_token` существуют, но не подключены к активным router. Логи смешивают `print`, logger и rotating `wms_integration.log`; correlation ID нет.

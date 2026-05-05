from contextlib import asynccontextmanager, AsyncExitStack
from concurrent.futures import ProcessPoolExecutor

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from faststream import FastStream
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware
import uvicorn

from app.api.v1.endpoints import (receipt_of_goods_router, income_on_bank_account_router, shipment_of_goods_router,
                                  ordered_goods_from_buyers_router, local_barcode_generation_router, warehouse_and_balances_router,
                                  goods_information_router, inventory_check_router, inventory_transactions_router, return_of_goods_router, docs_router,
                                  containers_router, products_dimensions_router, box_stickers_router, cash_flow_writeoff_router,
                                  return_to_supplier_router)
from app.broker.broker import broker_manager
import app.broker.subscriber  # noqa: F401
from app.database.db_connect import init_db, close_db
from app.dependencies.config import settings
from app.monitoring import MetricsMiddleware, monitoring_router
from app.limiter import limiter
from app.file_storage import S3StorageManager


@asynccontextmanager
async def lifespan(app: FastAPI):
    process_pool = ProcessPoolExecutor(max_workers=4)
    async with AsyncExitStack() as stack:    
        # db
        pool = await init_db()
        stack.push_async_callback(close_db, pool)

        # s3
        storage_manager = await stack.enter_async_context(
            S3StorageManager(
                region_name=settings.AWS_REGION_NAME,
                bucket_name=settings.DOCGEN_BUCKET_NAME,
                aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
                aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY.get_secret_value(),
                endpoint_url=settings.FILE_STORAGE_HOST,
                dns_subdomain=settings.FILE_STORAGE_DNS_SUBDOMAIN,
            )
        )

        file_storage = storage_manager.storage

        # rabbitmq
        broker = broker_manager.broker

        # faststream
        if settings.CONSUMERS_START:
            broker_app = FastStream(broker)
            broker_app.context.set_global("pool", pool)
            broker_app.context.set_global("file_storage", file_storage)
            await broker_app.start()
            stack.push_async_callback(broker_app.stop)
        else:
            await broker_manager.connect()
            stack.push_async_callback(broker_manager.close)

        app.state.broker = broker
        app.state.process_pool = process_pool
        app.state.pool = pool
        app.state.file_storage = file_storage
        yield

    if process_pool:
        process_pool.shutdown(wait=True)


app = FastAPI(lifespan=lifespan, title="1CRoutingAPI")


# 🔄 ПОРЯДОК MIDDLEWARE ВАЖЕН!
# Мониторинг (первым - измеряет всё)
app.add_middleware(MetricsMiddleware)

app.add_middleware(SlowAPIMiddleware)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Настраиваем лимитер
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# Подключаем роутеры
app.include_router(monitoring_router, prefix="/api")  # 🆕 Мониторинг
app.include_router(receipt_of_goods_router, prefix="/api")
app.include_router(income_on_bank_account_router, prefix="/api")
app.include_router(shipment_of_goods_router, prefix="/api")
app.include_router(ordered_goods_from_buyers_router, prefix="/api")
app.include_router(local_barcode_generation_router, prefix="/api")
app.include_router(warehouse_and_balances_router, prefix="/api")
app.include_router(goods_information_router, prefix="/api")
app.include_router(inventory_check_router, prefix="/api")
app.include_router(inventory_transactions_router, prefix="/api")
app.include_router(return_of_goods_router, prefix="/api")
app.include_router(docs_router, prefix="/api")
app.include_router(containers_router, prefix="/api")
app.include_router(products_dimensions_router, prefix="/api")
app.include_router(box_stickers_router, prefix="/api")
app.include_router(cash_flow_writeoff_router, prefix="/api")
app.include_router(return_to_supplier_router, prefix="/api")


if __name__ == "__main__":
    uvicorn.run("main:app", host=settings.APP_IP_ADDRESS, port=settings.APP_PORT, reload=True)

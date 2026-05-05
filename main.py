from concurrent.futures import ProcessPoolExecutor

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from faststream import FastStream
from faststream.asgi import AsgiFastStream

from app.database.db_connect import init_db, close_db
from app.api.v1.endpoints import (receipt_of_goods_router, income_on_bank_account_router, shipment_of_goods_router,
                                  ordered_goods_from_buyers_router, local_barcode_generation_router, warehouse_and_balances_router,
                                  goods_information_router, inventory_check_router, inventory_transactions_router, return_of_goods_router, docs_router,
                                  containers_router, products_dimensions_router, box_stickers_router, cash_flow_writeoff_router,
                                  return_to_supplier_router)
from app.monitoring import MetricsMiddleware, monitoring_router
from contextlib import asynccontextmanager
import uvicorn
from app.dependencies.config import settings
from app.broker.broker import broker_manager

from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware
from app.limiter import limiter
import app.broker.subscriber


@asynccontextmanager
async def lifespan(app: FastAPI):
    pool = await init_db()
    await broker_manager.connect()
    process_pool = ProcessPoolExecutor(max_workers=4)
    app.state.pool = pool
    app.state.process_pool = process_pool
    yield
    await close_db(pool)
    # await broker_manager.close()
    if process_pool:
        process_pool.shutdown(wait=True)

# stream_app = FastStream(broker_manager.broker, lifespan=lifespan)

app = FastAPI(lifespan=lifespan, title="1CRoutingAPI")

# app.mount("/ws", AsgiFastStream(broker_manager.broker))



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
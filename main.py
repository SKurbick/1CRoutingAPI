from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.database.db_connect import init_db, close_db
from app.api.v1.endpoints import (receipt_of_goods_router, income_on_bank_account_router, shipment_of_goods_router,
                                  ordered_goods_from_buyers_router, local_barcode_generation_router, warehouse_and_balances_router,
                                  goods_information_router, inventory_check_router, inventory_transactions_router, return_of_goods_router, docs_router)
from app.monitoring import MetricsMiddleware, monitoring_router
from contextlib import asynccontextmanager
import uvicorn
from app.dependencies.config import settings

from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware
from app.limiter import limiter


@asynccontextmanager
async def lifespan(app: FastAPI):
    pool = await init_db()
    app.state.pool = pool
    yield
    await close_db(pool)


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

if __name__ == "__main__":
    uvicorn.run("main:app", host=settings.APP_IP_ADDRESS, port=settings.APP_PORT, reload=True)
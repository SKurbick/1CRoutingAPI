# todo подключение пользователя
# todo метод отправки данных

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.database.db_connect import init_db, close_db
from app.api.v1.endpoints import (receipt_of_goods_router, income_on_bank_account_router, shipment_of_goods_router,
                                  ordered_goods_from_buyers_router,local_barcode_generation_router, warehouse_and_balances_router)
from contextlib import asynccontextmanager
import uvicorn
from app.dependencies.config import settings


# Контекстный менеджер для управления жизненным циклом приложения
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Инициализация пула соединений при старте приложения
    pool = await init_db()
    app.state.pool = pool
    yield
    # Закрытие пула соединений при завершении работы приложения
    await close_db(pool)


# Создаем экземпляр FastAPI с использованием lifespan
app = FastAPI(lifespan=lifespan, title="1CRoutingAPI")
app.include_router(receipt_of_goods_router, prefix="/api")
app.include_router(income_on_bank_account_router, prefix="/api")
app.include_router(shipment_of_goods_router, prefix="/api")
app.include_router(ordered_goods_from_buyers_router, prefix="/api")
app.include_router(local_barcode_generation_router, prefix="/api")
app.include_router(warehouse_and_balances_router, prefix="/api")
origins = [
    "*",  # временное решение
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,  # Список разрешённых origin
    allow_credentials=True,  # Разрешить передачу cookies и авторизационных данных
    allow_methods=["*"],  # Разрешить все HTTP методы (GET, POST, PUT, DELETE и т.д.)
    allow_headers=["*"],  # Разрешить все заголовки
)

if __name__ == "__main__":
    uvicorn.run("main:app", host=settings.APP_IP_ADDRESS, port=settings.APP_PORT, reload=True)

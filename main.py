from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.database.db_connect import init_db, close_db
from app.api.v1 import router as router_v1
from app.api.v2 import router as router_v2

from contextlib import asynccontextmanager
import uvicorn
from app.dependencies.config import settings


from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware
from app.limiter import limiter  # Импортируем наш лимитер



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



# Настраиваем лимитер
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)


app.include_router(router_v1, prefix="/api/v1")
app.include_router(router_v2, prefix="/api/v2")


origins = [
    "*",  # временное решение
]

app.add_middleware(SlowAPIMiddleware)
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,  # Список разрешённых origin
    allow_credentials=True,  # Разрешить передачу cookies и авторизационных данных
    allow_methods=["*"],  # Разрешить все HTTP методы (GET, POST, PUT, DELETE и т.д.)
    allow_headers=["*"],  # Разрешить все заголовки
)

if __name__ == "__main__":
    uvicorn.run("main:app", host=settings.APP_IP_ADDRESS, port=settings.APP_PORT, reload=True)

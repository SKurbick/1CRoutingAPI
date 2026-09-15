import asyncio

from asyncpg import create_pool, Pool
from app.dependencies.config import settings


async def init_db() -> Pool:
    """Инициализация пула соединений с базой данных."""
    pool = await create_pool(
        user=settings.POSTGRES_USER,
        password=settings.POSTGRES_PASSWORD,
        database=settings.POSTGRES_DB,
        host=settings.POSTGRES_HOST,
        port=settings.POSTGRES_PORT,
        min_size=settings.POSTGRES_MIN_CONN_COUNT,
        max_size=settings.POSTGRES_MAX_CONN_COUNT,
        max_inactive_connection_lifetime=settings.POSTGRES_MAX_CONN_INACTIVE_LIFETIME,
        server_settings={
            "application_name": settings.APP_NAME
        }
    )
    # Проверим какие параметры установились по умолчанию
    print("📊 ДЕФОЛТНЫЕ параметры asyncpg:")
    print(f"   min_size: {pool._minsize}")
    print(f"   max_size: {pool._maxsize}")
    print(f"   max_queries: {pool._max_queries}")
    print(f"   max_inactive_connection_lifetime: {pool._max_inactive_connection_lifetime}")
    print(f"   setup: {pool._setup}")
    print(f"   init: {pool._init}")

    async def monitor_pool():
        while True:
            # Текущее количество подключений в пуле
            current_size = len(pool._holders) if hasattr(pool, '_holders') else 'unknown'
            print(f"📊 Пул подключений: {current_size}/10")

            # Проверим активные подключения в БД
            async with pool.acquire() as conn:
                active_connections = await conn.fetchval("""
                    SELECT count(*) FROM pg_stat_activity 
                    WHERE datname = current_database() 
                    AND state = 'active'
                """)
                print(f"📈 Активные подключения в БД: {active_connections}")

            await asyncio.sleep(30)  # Каждые 5 секунд

    # Запускаем мониторинг в фоне
    asyncio.create_task(monitor_pool())
    # Проверим реальное подключение
    # async with pool.acquire() as conn:
    #     # Параметры сервера
    #     db_info = await conn.fetchrow("""
    #         SELECT
    #             current_setting('max_connections') as max_connections,
    #             current_setting('timeout') as timeout,
    #             current_setting('tcp_keepalives_idle') as keepalive_idle
    #     """)
    #
    #     print("🗄️ Параметры PostgreSQL сервера:")
    #     print(f"   max_connections: {db_info['max_connections']}")
    #     print(f"   timeout: {db_info['timeout']}")
    #     print(f"   tcp_keepalives_idle: {db_info['keepalive_idle']}")

    print("Создан пул подключений к Базе Данных.")
    return pool


async def close_db(pool: Pool) -> None:
    """Закрытие пула соединений."""
    await pool.close()
    print("Пул соединений к базе данных закрыт.")

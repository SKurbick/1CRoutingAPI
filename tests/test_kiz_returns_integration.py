"""Opt-in checks against disposable services, never the application .env targets."""
import asyncio
import json
import os
from pathlib import Path
from unittest.mock import AsyncMock
from uuid import uuid4

import aio_pika
import asyncpg
import pytest

from app.broker.kiz_returns import KizReturnsPublisher
from app.database.repositories.kiz_returns_outbox import enqueue_kiz_returns
from app.database.repositories.return_of_goods import ReturnOfGoodsRepository
from app.models.return_of_goods import (
    IncomingReturns, ManualUnidentifiedReturn, MarkCode, MissingStickerReturn,
)
from app.service.kiz_returns_outbox import KizReturnsOutboxWorker

ROOT = Path(__file__).resolve().parents[1]


@pytest.mark.skipif(not os.getenv("TEST_KIZ_POSTGRES_URL"), reason="Disposable PostgreSQL URL required")
def test_postgres_atomicity_retry_restart_concurrency_and_cancellation():
    async def run():
        # Create a private database: the URL's original database is untouched.
        admin = await asyncpg.connect(os.environ["TEST_KIZ_POSTGRES_URL"])
        database = "kiz_test_" + uuid4().hex
        pool = None
        try:
            await admin.execute(f'CREATE DATABASE "{database}"')
            pool = await asyncpg.create_pool(
                os.environ["TEST_KIZ_POSTGRES_URL"], database=database,
                min_size=1, max_size=4,
            )
            async with pool.acquire() as conn:
                migration = (ROOT / "migrations/kiz_returns_outbox.sql").read_text()
                await conn.execute(migration)
                await conn.execute(migration)  # Reapplying the migration is safe.
                await conn.execute("""
                    CREATE TABLE products (id VARCHAR(50) PRIMARY KEY);
                    CREATE TABLE warehouses (id INT PRIMARY KEY);
                    CREATE TABLE incoming_returns (
                        id BIGSERIAL PRIMARY KEY, author TEXT, product_id TEXT,
                        warehouse_id INT, quantity INT, return_date DATE,
                        share_of_kit BOOL, metawild TEXT
                    );
                    CREATE TABLE goods_returns_dev (
                        srid TEXT PRIMARY KEY, nm_id INT, account TEXT,
                        is_received BOOL, incoming_return_id BIGINT, sticker_id TEXT
                    );
                    CREATE TABLE article (nm_id INT, local_vendor_code TEXT);
                    CREATE TABLE seller_account (account_name TEXT);
                    CREATE TABLE goods_returns_mark_list (
                        mark_code TEXT, author TEXT, product_id TEXT
                    );
                    CREATE TABLE goods_return_manual_identifications (
                        srid TEXT, product_id TEXT, original_nm_id INT,
                        resolved_by TEXT, comment TEXT, incoming_return_id BIGINT
                    );
                    INSERT INTO products VALUES ('SKU');
                    INSERT INTO warehouses VALUES (1);
                    INSERT INTO seller_account VALUES ('seller');
                    INSERT INTO goods_returns_dev (srid, account, is_received)
                    VALUES ('standard', 'seller', FALSE),
                           ('manual', 'seller', FALSE), ('rollback', 'seller', FALSE);
                """)
                await conn.execute((ROOT / "migrations/manual_sticker_returns.sql").read_text())

            repo = ReturnOfGoodsRepository(pool)
            common = dict(product_id="SKU", author="Operator", warehouse_id=1, return_date="2026-11-27")
            standard = IncomingReturns(
                **common, sum_quantity=1,
                is_received_data=[{"srid": "standard", "is_received": True}],
                mark_list=[{"mark_code": "first"}, {"mark_code": None}],
            )
            assert (await repo.incoming_returns([standard])).status == 201
            assert (await repo.receive_unidentified(ManualUnidentifiedReturn(
                **common, srids=["manual"], mark_list=[{"mark_code": "second"}],
            ))).status == 201
            assert (await repo.receive_missing_sticker(MissingStickerReturn(
                **common, sticker_id="missing", mark_list=[{"mark_code": "third"}],
            ))).status == 201
            async with pool.acquire() as conn:
                assert await conn.fetchval("SELECT count(*) FROM kiz_returns_outbox") == 3
                await conn.execute("ALTER TABLE kiz_returns_outbox ADD CONSTRAINT fail_insert CHECK (FALSE) NOT VALID")
                standard.is_received_data[0].srid = "rollback"
                assert (await repo.incoming_returns([standard])).status == 422
                assert await conn.fetchval("SELECT count(*) FROM incoming_returns") == 3
                assert await conn.fetchval("SELECT count(*) FROM goods_returns_mark_list") == 4
                assert await conn.fetchval("SELECT is_received FROM goods_returns_dev WHERE srid='rollback'") is False
                await conn.execute("ALTER TABLE kiz_returns_outbox DROP CONSTRAINT fail_insert")

            publisher = AsyncMock()
            publisher.publish.side_effect = [ConnectionError(), None, None]
            worker = KizReturnsOutboxWorker(pool, publisher, 1)
            assert await worker.process_one()  # Connection failure.
            assert await worker.process_one()  # Other events are not blocked.
            assert await worker.process_one()
            assert not await worker.process_one()  # Failed event is delayed.
            first_call = publisher.publish.call_args_list[0]
            async with pool.acquire() as conn:
                row = await conn.fetchrow("SELECT * FROM kiz_returns_outbox WHERE sent_at IS NULL")
                assert row["attempts"] == 1 and row["last_error"] == "ConnectionError"
                await conn.execute("UPDATE kiz_returns_outbox SET next_attempt_at=NOW() WHERE sent_at IS NULL")
            # A fresh worker resumes the persisted event.
            publisher.publish.side_effect = None
            assert await KizReturnsOutboxWorker(pool, publisher, 1).process_one()
            assert publisher.publish.call_args == first_call

            async with pool.acquire() as conn:
                await enqueue_kiz_returns(conn, [MarkCode(mark_code="parallel-1")])
                await enqueue_kiz_returns(conn, [MarkCode(mark_code="parallel-2")])
            entered, release = asyncio.Event(), asyncio.Event()

            async def blocking_publish(*args):
                entered.set()
                await release.wait()

            slow = AsyncMock()
            slow.publish.side_effect = blocking_publish
            task = asyncio.create_task(KizReturnsOutboxWorker(pool, slow, 1).process_one())
            await asyncio.wait_for(entered.wait(), 2)
            try:
                assert await asyncio.wait_for(worker.process_one(), 2)
                assert slow.publish.call_args.args[0] != publisher.publish.call_args.args[0]
            finally:
                release.set()
                await task

            async with pool.acquire() as conn:
                await enqueue_kiz_returns(conn, [MarkCode(mark_code="cancelled")])
            entered.clear()
            release.clear()
            task = asyncio.create_task(KizReturnsOutboxWorker(pool, slow, 1).process_one())
            await asyncio.wait_for(entered.wait(), 2)
            task.cancel()
            with pytest.raises(asyncio.CancelledError):
                await task
            assert await worker.process_one()  # Cancellation released the row lock.
            async with pool.acquire() as conn:
                assert await conn.fetchval("SELECT count(*) FROM kiz_returns_outbox WHERE sent_at IS NULL") == 0
        finally:
            if pool is not None:
                await pool.close()
            await admin.execute(f'DROP DATABASE IF EXISTS "{database}"')
            await admin.close()

    asyncio.run(run())


@pytest.mark.skipif(not os.getenv("TEST_KIZ_RABBITMQ_URL"), reason="Disposable RabbitMQ URL required")
def test_rabbit_confirms_unroutable_error_and_reconnection():
    async def run():
        url = os.environ["TEST_KIZ_RABBITMQ_URL"]
        connection = await aio_pika.connect(url)
        publisher = KizReturnsPublisher(url, "kiz-test-" + uuid4().hex, "wms.kiz_returns", 3)
        try:
            channel = await connection.channel()
            exchange = await channel.declare_exchange(publisher.exchange_name, type="topic", auto_delete=True)
            queue = await channel.declare_queue(exclusive=True)
            with pytest.raises(aio_pika.exceptions.DeliveryError):
                await publisher.publish(42, {"mark_codes": ["mark-1"]})
            await queue.bind(exchange, routing_key="wms.kiz_returns")
            for _ in range(2):
                await publisher.publish(42, {"mark_codes": ["mark-1"]})
                message = await queue.get(timeout=2)
                assert json.loads(message.body) == {"mark_codes": ["mark-1"]}
                assert message.message_id == "kiz-returns-42"
                assert message.delivery_mode == aio_pika.DeliveryMode.PERSISTENT
                await message.ack()
                await publisher.connection.close()  # Next call must reconnect.
        finally:
            await publisher.close()
            await connection.close()

    asyncio.run(run())

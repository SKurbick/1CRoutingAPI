import asyncio
import json
from datetime import date
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock, patch

import asyncpg
import pytest
from pamqp.commands import Basic

from app.broker.kiz_returns import KizReturnsPublisher
from app.database.repositories.kiz_returns_outbox import enqueue_kiz_returns
from app.database.repositories.return_of_goods import ReturnOfGoodsRepository
from app.models.return_of_goods import IncomingReturns, ManualUnidentifiedReturn, MarkCode
from app.service.kiz_returns_outbox import KizReturnsOutboxWorker


class Context:
    def __init__(self, value):
        self.value = value

    async def __aenter__(self):
        return self.value

    async def __aexit__(self, *args):
        return False


def make_connection():
    conn = AsyncMock()
    conn.transaction = MagicMock(return_value=Context(conn))
    pool = SimpleNamespace(acquire=lambda: Context(conn))
    return conn, pool


def test_filters_placeholder_and_blanks_deduplicates_and_preserves_code():
    conn = AsyncMock()
    code = " 010ABC\x1d21serial "
    marks = [MarkCode(mark_code=v) for v in [None, "broken", " BROKEN ", "", "  ", code, code, "second"]]

    asyncio.run(enqueue_kiz_returns(conn, marks))

    assert conn.execute.await_count == 1
    assert json.loads(conn.execute.call_args.args[1]) == {"mark_codes": [code, "second"]}


@pytest.mark.parametrize("marks", [[], [MarkCode()], [MarkCode(mark_code=" ")]])
def test_empty_payload_does_not_create_event(marks):
    conn = AsyncMock()
    asyncio.run(enqueue_kiz_returns(conn, marks))
    conn.execute.assert_not_awaited()


def incoming_request(code="mark-1"):
    return IncomingReturns(
        product_id="SKU", sum_quantity=1, author="Operator", warehouse_id=1,
        return_date=date(2026, 11, 27),
        is_received_data=[{"srid": "srid-1", "is_received": True}],
        mark_list=[{"mark_code": code}],
    )


def test_standard_receipt_enqueues_one_event_for_whole_request():
    conn, pool = make_connection()
    conn.fetchrow.return_value = {"id": 42}
    result = asyncio.run(ReturnOfGoodsRepository(pool).incoming_returns([
        incoming_request(), incoming_request(), incoming_request("mark-2"),
    ]))

    assert result.status == 201
    assert conn.execute.await_count == 1
    assert json.loads(conn.execute.call_args.args[1]) == {"mark_codes": ["mark-1", "mark-2"]}


def test_manual_identification_enqueues_marks():
    conn, pool = make_connection()
    conn.fetchval.side_effect = [True, True, True, 42]
    conn.fetch.return_value = [{
        "srid": "srid-1", "is_received": False, "incoming_return_id": None,
        "local_vendor_code": None, "account": "seller", "nm_id": 123,
    }]
    request = ManualUnidentifiedReturn(
        product_id="SKU", author="Operator", warehouse_id=1,
        return_date=date(2026, 11, 27), srids=["srid-1"],
        mark_list=[{"mark_code": "mark-1"}],
    )
    result = asyncio.run(ReturnOfGoodsRepository(pool).receive_unidentified(request))

    assert result.status == 201
    assert json.loads(conn.execute.call_args.args[1]) == {"mark_codes": ["mark-1"]}


def test_outbox_failure_propagates_out_of_receipt_transaction():
    conn, pool = make_connection()
    conn.fetchrow.return_value = {"id": 42}
    conn.execute.side_effect = asyncpg.PostgresError("outbox write failed")
    transaction = MagicMock()
    transaction.__aenter__ = AsyncMock(return_value=conn)
    transaction.__aexit__ = AsyncMock(return_value=False)
    conn.transaction.return_value = transaction

    result = asyncio.run(ReturnOfGoodsRepository(pool).incoming_returns([incoming_request()]))

    assert result.status == 422
    assert transaction.__aexit__.call_args.args[0] is asyncpg.PostgresError


def test_worker_retries_then_marks_sent_with_same_payload_and_id():
    conn, pool = make_connection()
    conn.fetchrow.side_effect = [
        {"id": 42, "payload": '{"mark_codes":["mark-1"]}', "attempts": 0},
        {"id": 42, "payload": '{"mark_codes":["mark-1"]}', "attempts": 1},
        None,
    ]
    publisher = AsyncMock()
    publisher.publish.side_effect = [ConnectionError("secret URL must not be logged"), None]
    worker = KizReturnsOutboxWorker(pool, publisher, 1)

    async def run():
        assert await worker.process_one()
        assert await worker.process_one()
        assert not await worker.process_one()

    asyncio.run(run())

    failure, success = conn.execute.call_args_list
    assert "next_attempt_at" in failure.args[0]
    assert failure.args[1:] == (42, "ConnectionError", 2)
    assert "sent_at = clock_timestamp()" in success.args[0]
    assert publisher.publish.call_args_list[0] == publisher.publish.call_args_list[1]


def test_worker_cancellation_does_not_mark_event_sent_or_failed():
    conn, pool = make_connection()
    conn.fetchrow.return_value = {"id": 42, "payload": {"mark_codes": ["mark"]}, "attempts": 0}
    publisher = AsyncMock()
    publisher.publish.side_effect = asyncio.CancelledError

    with pytest.raises(asyncio.CancelledError):
        asyncio.run(KizReturnsOutboxWorker(pool, publisher, 1).process_one())

    conn.execute.assert_not_awaited()


def test_backoff_is_capped():
    conn, pool = make_connection()
    conn.fetchrow.return_value = {"id": 42, "payload": {"mark_codes": ["mark"]}, "attempts": 10000}
    publisher = AsyncMock()
    publisher.publish.side_effect = ConnectionError
    asyncio.run(KizReturnsOutboxWorker(pool, publisher, 1).process_one())
    assert conn.execute.call_args.args[3] == 300


def test_worker_closes_publisher_and_stops_task():
    _, pool = make_connection()
    publisher = AsyncMock()
    worker = KizReturnsOutboxWorker(pool, publisher, 1)
    worker.process_one = AsyncMock(return_value=False)

    async def run():
        worker.start()
        await asyncio.sleep(0)
        await worker.close()
        assert worker.task.done()

    asyncio.run(run())
    publisher.close.assert_awaited_once()


@pytest.mark.parametrize("confirmation", [Basic.Ack(), Basic.Nack(), None])
def test_publisher_requires_confirmation_and_mandatory_routing(confirmation):
    exchange = AsyncMock()
    exchange.publish.return_value = confirmation
    channel = AsyncMock(is_closed=False)
    channel.get_exchange.return_value = exchange
    connection = AsyncMock(is_closed=False)
    connection.channel.return_value = channel
    publisher = KizReturnsPublisher("amqp://unused", "wms.events", "wms.kiz_returns", 1)

    with patch("app.broker.kiz_returns.aio_pika.connect", AsyncMock(return_value=connection)):
        if isinstance(confirmation, Basic.Ack):
            asyncio.run(publisher.publish(42, {"mark_codes": ["mark-1"]}))
        else:
            with pytest.raises(RuntimeError):
                asyncio.run(publisher.publish(42, {"mark_codes": ["mark-1"]}))

    connection.channel.assert_awaited_once_with(publisher_confirms=True, on_return_raises=True)
    channel.get_exchange.assert_awaited_once_with("wms.events", ensure=True)
    message = exchange.publish.call_args.args[0]
    assert json.loads(message.body) == {"mark_codes": ["mark-1"]}
    assert message.message_id == "kiz-returns-42"
    assert message.delivery_mode == 2
    assert exchange.publish.call_args.kwargs["mandatory"] is True
    assert exchange.publish.call_args.kwargs["routing_key"] == "wms.kiz_returns"

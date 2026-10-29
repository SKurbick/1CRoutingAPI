import asyncio
from datetime import date

from app.database.repositories.return_of_goods import ReturnOfGoodsRepository
from app.models.return_of_goods import MissingStickerReturn


class AsyncContext:
    def __init__(self, value):
        self.value = value

    async def __aenter__(self):
        return self.value

    async def __aexit__(self, exc_type, exc, traceback):
        return False


class FakeConnection:
    def __init__(
            self,
            *,
            source_returns=None,
            manual_exists=False,
            product_exists=True,
            warehouse_exists=True,
    ):
        self.source_returns = source_returns or []
        self.manual_exists = manual_exists
        self.product_exists = product_exists
        self.warehouse_exists = warehouse_exists
        self.executed = []
        self.executed_many = []

    def transaction(self):
        return AsyncContext(self)

    async def fetch(self, query, *args):
        assert "FROM public.goods_returns_dev" in query
        return self.source_returns

    async def fetchval(self, query, *args):
        if "FROM public.manual_sticker_returns" in query:
            return self.manual_exists
        if "FROM public.products" in query:
            return self.product_exists
        if "FROM public.warehouses" in query:
            return self.warehouse_exists
        if "INSERT INTO public.incoming_returns" in query:
            self.executed.append((query, args))
            return 42
        raise AssertionError(f"Unexpected query: {query}")

    async def execute(self, query, *args):
        self.executed.append((query, args))

    async def executemany(self, query, args):
        self.executed_many.append((query, args))


class FakePool:
    def __init__(self, connection):
        self.connection = connection

    def acquire(self):
        return AsyncContext(self.connection)


def make_request(**overrides):
    values = {
        "sticker_id": " sticker-1 ",
        "product_id": " SKU-1 ",
        "warehouse_id": 1,
        "return_date": date(2026, 9, 27),
        "author": " Operator ",
        "mark_list": [{"mark_code": "mark-1"}, {"mark_code": None}],
    }
    values.update(overrides)
    return MissingStickerReturn(**values)


def test_missing_sticker_request_normalizes_required_strings_and_marks():
    request = make_request()

    assert request.sticker_id == "sticker-1"
    assert request.product_id == "SKU-1"
    assert request.author == "Operator"
    assert [mark.mark_code for mark in request.mark_list] == ["mark-1", "broken"]


def test_received_source_sticker_is_rejected():
    connection = FakeConnection(source_returns=[{"is_received": True}])
    repository = ReturnOfGoodsRepository(FakePool(connection))

    result = asyncio.run(repository.receive_missing_sticker(make_request()))

    assert result.status == 409
    assert result.message == "Товар уже оприходован"
    assert connection.executed == []


def test_unreceived_source_sticker_must_use_standard_receipt():
    connection = FakeConnection(source_returns=[{"is_received": False}])
    repository = ReturnOfGoodsRepository(FakePool(connection))

    result = asyncio.run(repository.receive_missing_sticker(make_request()))

    assert result.status == 409
    assert "стандартным способом" in result.message
    assert connection.executed == []


def test_previously_received_missing_sticker_is_rejected():
    connection = FakeConnection(manual_exists=True)
    repository = ReturnOfGoodsRepository(FakePool(connection))

    result = asyncio.run(repository.receive_missing_sticker(make_request()))

    assert result.status == 409
    assert result.message == "Товар уже оприходован"
    assert connection.executed == []


def test_missing_sticker_creates_receipt_link_and_marks():
    connection = FakeConnection()
    repository = ReturnOfGoodsRepository(FakePool(connection))

    result = asyncio.run(repository.receive_missing_sticker(make_request()))

    assert result.status == 201
    assert len(connection.executed) == 2

    incoming_query, incoming_args = connection.executed[0]
    assert "INSERT INTO public.incoming_returns" in incoming_query
    assert incoming_args[:3] == ("Operator", "SKU-1", 1)

    link_query, link_args = connection.executed[1]
    assert "INSERT INTO public.manual_sticker_returns" in link_query
    assert link_args == (42, "sticker-1", "SKU-1")

    marks_query, marks = connection.executed_many[0]
    assert "INSERT INTO public.goods_returns_mark_list" in marks_query
    assert marks == [
        ("mark-1", "Operator", "SKU-1"),
        ("broken", "Operator", "SKU-1"),
    ]

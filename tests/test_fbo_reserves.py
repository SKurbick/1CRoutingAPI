"""DB checks are opt-in; all writes use testwild and are rolled back."""
import asyncio
import os
from contextlib import asynccontextmanager
from decimal import Decimal
from unittest.mock import AsyncMock

import asyncpg
import pytest
from dotenv import dotenv_values
from fastapi import FastAPI, HTTPException
from fastapi.testclient import TestClient
from pydantic import ValidationError

from app.database.repositories.shipment_of_goods import ShipmentOfGoodsRepository
from app.models.shipment_of_goods import FBOReservePatch
from app.api.v1.endpoints.shipment_of_goods import router
from app.dependencies import get_shipment_of_goods_service


@pytest.mark.parametrize("field", [
    "shipped", "delivery_type", "is_hanging", "is_fulfilled",
    "id", "source_reserve_id", "created_at", "unknown",
])
def test_system_fields_are_rejected(field):
    with pytest.raises(ValidationError):
        FBOReservePatch.model_validate({field: 0})


@pytest.mark.parametrize("payload", [
    {}, {"product_id": None}, {"warehouse_id": None}, {"ordered": None},
    {"ordered": -1}, {"ordered": "NaN"}, {"product_id": ""},
    {"expires_at": "2026-10-26T12:00:00"},
])
def test_invalid_patch_is_rejected(payload):
    with pytest.raises(ValidationError):
        FBOReservePatch.model_validate(payload)


def test_patch_preserves_omitted_fields_and_explicit_null():
    assert FBOReservePatch(account=None).model_dump(exclude_unset=True) == {"account": None}
    assert FBOReservePatch(ordered="1.5").ordered == Decimal("1.5")


def test_http_contract_and_validation():
    service = AsyncMock()
    service.patch_fbo_reserve.return_value = {
        "status": 200, "message": "updated",
        "data": [{"id": 1, "ordered": Decimal("5"), "shipped": Decimal("0")}],
    }
    app = FastAPI()
    app.include_router(router, prefix="/api")
    app.dependency_overrides[get_shipment_of_goods_service] = lambda: service
    with TestClient(app) as client:
        url = "/api/shipment_of_goods/fbo_reserves/1"
        response = client.patch(url, json={"ordered": 5})
        assert response.status_code == 200
        assert response.json()["data"] == [{"id": 1, "ordered": "5", "shipped": "0"}]
        response = client.patch(url, json={"delivery_type": "ФБС"})
        assert response.status_code == 422
        assert service.patch_fbo_reserve.await_count == 1
        response = client.delete(url)
        assert response.status_code == 204
        assert response.content == b""
        service.delete_fbo_reserve.side_effect = HTTPException(409, "conflict")
        assert client.delete(url).status_code == 409
        service.patch_fbo_reserve.side_effect = HTTPException(404, "missing")
        assert client.patch(url, json={"ordered": 5}).status_code == 404


def test_generated_openapi_documents_fbo_reserve_operations():
    app = FastAPI()
    app.include_router(router, prefix="/api")
    schema = app.openapi()
    operations = schema["paths"]["/api/shipment_of_goods/fbo_reserves/{reserve_id}"]
    patch = operations["patch"]
    examples = patch["requestBody"]["content"]["application/json"]["examples"]
    for example in examples.values():
        FBOReservePatch.model_validate(example["value"])
    properties = schema["components"]["schemas"]["FBOReservePatch"]["properties"]
    assert all(field.get("description") for field in properties.values())
    assert schema["components"]["schemas"]["FBOReservePatch"]["additionalProperties"] is False
    for operation in operations.values():
        assert "ФБО" in operation["summary"]
        assert "shipped = 0" in operation["description"]
        assert "reserve_id из GET" in operation["parameters"][0]["description"]
        for status in ("404", "409", "422"):
            assert operation["responses"][status]["content"]["application/json"]
    assert "content" not in operations["delete"]["responses"]["204"]


@pytest.mark.skipif(os.getenv("RUN_FBO_DB_TESTS") != "1", reason="Explicit DB opt-in required")
def test_fbo_reserve_database_lifecycle():
    asyncio.run(_database_lifecycle())


async def _database_lifecycle():
    env = dotenv_values(".env")
    conn = await asyncpg.connect(
        user=env["POSTGRES_USER"], password=env["POSTGRES_PASSWORD"],
        database=env["POSTGRES_DB"], host=env["POSTGRES_HOST"],
        port=int(env["POSTGRES_PORT"]), timeout=12,
        server_settings={"application_name": "testwild_fbo_rollback_test",
                         "statement_timeout": "15000", "lock_timeout": "3000"},
    )

    class Pool:
        @asynccontextmanager
        async def acquire(self):
            yield conn

    repo = ShipmentOfGoodsRepository(Pool())
    transaction = conn.transaction()
    await transaction.start()
    try:
        assert await conn.fetchval("SELECT EXISTS(SELECT 1 FROM products WHERE id='testwild')")
        warehouses = await conn.fetch("SELECT id FROM warehouses ORDER BY id LIMIT 2")
        assert len(warehouses) == 2, "Two existing warehouses are needed"
        first, second = (row["id"] for row in warehouses)

        async def create(ordered=7, delivery_type="ФБО", source=None):
            return await conn.fetchval(
                """INSERT INTO product_reserves
                   (product_id,warehouse_id,ordered,delivery_type,supply_id,source_reserve_id)
                   VALUES ('testwild',$1,$2,$3,'testwild-fbo-rollback-audit',$4) RETURNING id""",
                first, ordered, delivery_type, source,
            )

        async def balance(warehouse):
            return await conn.fetchval(
                "SELECT reserved_quantity FROM current_balances WHERE product_id='testwild' AND warehouse_id=$1",
                warehouse,
            ) or Decimal(0)

        async def expect_conflict(call):
            with pytest.raises(HTTPException) as error:
                await call
            assert error.value.status_code == 409

        before = await balance(first)
        reserve_id = await create()
        assert await balance(first) == before + 7
        result = await repo.patch_fbo_reserve(reserve_id, FBOReservePatch(ordered="3.5", account="testwild"))
        assert result.data[0]["ordered"] == Decimal("3.5")
        assert await balance(first) == before + Decimal("3.5")
        movement = await conn.fetchrow(
            "SELECT account,quantity FROM inventory_transactions WHERE product_reserves_id=$1", reserve_id
        )
        assert movement["account"] == "testwild"
        assert movement["quantity"] == Decimal("3.5")

        second_before = await balance(second)
        await repo.patch_fbo_reserve(reserve_id, FBOReservePatch(warehouse_id=second))
        assert await balance(first) == before
        assert await balance(second) == second_before + Decimal("3.5")
        await repo.delete_fbo_reserve(reserve_id)
        assert await balance(second) == second_before
        assert not await conn.fetchval("SELECT EXISTS(SELECT 1 FROM inventory_transactions WHERE product_reserves_id=$1)", reserve_id)

        fbs_id = await create(delivery_type="ФБС")
        await expect_conflict(repo.patch_fbo_reserve(fbs_id, FBOReservePatch(ordered=2)))
        await expect_conflict(repo.delete_fbo_reserve(fbs_id))
        shipped_id = await create()
        await conn.execute("UPDATE product_reserves SET shipped=1 WHERE id=$1", shipped_id)
        await expect_conflict(repo.patch_fbo_reserve(shipped_id, FBOReservePatch(ordered=2)))
        await expect_conflict(repo.delete_fbo_reserve(shipped_id))

        parent = await create(ordered=6)
        child = await create(ordered=4, source=parent)
        await expect_conflict(repo.delete_fbo_reserve(parent))
        await expect_conflict(repo.patch_fbo_reserve(child, FBOReservePatch(warehouse_id=second)))
        await repo.delete_fbo_reserve(child)
        assert await conn.fetchval("SELECT ordered FROM product_reserves WHERE id=$1", parent) == 6

        linked = await create()
        shipment = await conn.fetchval(
            """INSERT INTO shipment_of_goods(product_id,warehouse_id,quantity,delivery_type,product_reserves_id)
               VALUES ('testwild',$1,1,'ФБО',$2) RETURNING id""", first, linked
        )
        await expect_conflict(repo.delete_fbo_reserve(linked))
        await expect_conflict(repo.patch_fbo_reserve(linked, FBOReservePatch(ordered=2)))
        assert await conn.fetchval("SELECT EXISTS(SELECT 1 FROM shipment_of_goods WHERE id=$1)", shipment)

        # Ошибка FK откатывает PATCH целиком, в том числе сработавшие триггеры.
        invalid_warehouse = await conn.fetchval("SELECT max(id)+1 FROM warehouses")
        untouched = await create()
        balance_before_error = await balance(first)
        with pytest.raises(HTTPException) as error:
            await repo.patch_fbo_reserve(untouched, FBOReservePatch(warehouse_id=invalid_warehouse, ordered=2))
        assert error.value.status_code == 422
        assert await conn.fetchval("SELECT ordered FROM product_reserves WHERE id=$1", untouched) == 7
        assert await balance(first) == balance_before_error

        # Не допускаем каскадного удаления постороннего движения.
        await conn.execute(
            """INSERT INTO inventory_transactions
               (product_id,warehouse_id,quantity,transaction_type,product_reserves_id,status_id)
               VALUES ('testwild',$1,1,'outgoing',$2,1)""", first, untouched
        )
        await expect_conflict(repo.delete_fbo_reserve(untouched))

        missing_movement = await create()
        await conn.execute("DELETE FROM inventory_transactions WHERE product_reserves_id=$1", missing_movement)
        await expect_conflict(repo.delete_fbo_reserve(missing_movement))

        with pytest.raises(HTTPException) as error:
            await repo.delete_fbo_reserve(reserve_id)
        assert error.value.status_code == 404
    finally:
        await transaction.rollback()
        await conn.close()

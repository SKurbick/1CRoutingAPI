import asyncio
from types import SimpleNamespace
from unittest.mock import AsyncMock

from fastapi import BackgroundTasks

from app.models.shipment_of_goods import DeliveryType
from app.service.receipt_of_goods import ReceiptOfGoodsService
from app.service.return_of_goods import ReturnOfGoodsService
from app.service.shipment_of_goods import ShipmentOfGoodsService


def test_returns_register_background_notification():
    repository = AsyncMock()
    repository.incoming_returns.return_value = SimpleNamespace(status=201)
    service = ReturnOfGoodsService(repository)
    tasks = BackgroundTasks()
    data = [SimpleNamespace(product_id="sku", warehouse_id=1)]

    result = asyncio.run(service.incoming_returns(data, tasks))

    assert result.status == 201
    assert len(tasks.tasks) == 1
    assert tasks.tasks[0].func == service.notify_one_c_about_returns


def test_failed_returns_do_not_register_notification():
    repository = AsyncMock()
    repository.incoming_returns.return_value = SimpleNamespace(status=422)
    service = ReturnOfGoodsService(repository)
    tasks = BackgroundTasks()

    asyncio.run(service.incoming_returns([], tasks))

    assert tasks.tasks == []


def test_fbo_shipment_registers_background_notification():
    repository = AsyncMock()
    repository.shipment_with_reserve_updating.return_value = SimpleNamespace(
        status=201
    )
    service = ShipmentOfGoodsService(repository)
    tasks = BackgroundTasks()
    data = [
        SimpleNamespace(
            supply_id="supply",
            account="account",
            product_id="sku",
            quantity=1,
        )
    ]

    asyncio.run(
        service.shipment_with_reserve_updating(
            data, DeliveryType.FBO, tasks
        )
    )

    assert len(tasks.tasks) == 1
    assert tasks.tasks[0].func == service.notify_one_c_about_fbo_shipment


def test_fbs_shipment_does_not_register_notification():
    repository = AsyncMock()
    repository.shipment_with_reserve_updating.return_value = SimpleNamespace(
        status=201
    )
    service = ShipmentOfGoodsService(repository)
    tasks = BackgroundTasks()

    asyncio.run(
        service.shipment_with_reserve_updating(
            [], DeliveryType.FBS, tasks
        )
    )

    assert tasks.tasks == []


def test_deprecated_fbo_update_registers_background_notification():
    repository = AsyncMock()
    repository.update_data.return_value = SimpleNamespace(status=201)
    service = ShipmentOfGoodsService(repository)
    tasks = BackgroundTasks()

    asyncio.run(service.create_data([], DeliveryType.FBO, tasks))

    assert len(tasks.tasks) == 1
    assert tasks.tasks[0].func == service.notify_one_c_about_fbo_shipment


def test_incoming_receipt_service_registers_background_notification():
    repository = AsyncMock()
    repository.add_incoming_receipt.return_value = SimpleNamespace(status=201)
    service = ReceiptOfGoodsService(repository)
    tasks = BackgroundTasks()

    asyncio.run(service.add_incoming_receipt([], tasks))

    assert len(tasks.tasks) == 1
    assert tasks.tasks[0].func == service.notify_one_c_about_incoming_receipt

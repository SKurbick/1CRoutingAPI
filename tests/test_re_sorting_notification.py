import asyncio
import logging
from unittest.mock import AsyncMock

import aiohttp
import pytest
from fastapi import BackgroundTasks

from app.infrastructure.ONE_C.routing import ONECRouting, OneCResponse
from app.models.warehouse_and_balances import ReSortingOperation, ReSortingOperationResponse
from app.service import warehouse_and_balances as service_module
from app.service.warehouse_and_balances import WarehouseAndBalancesService


@pytest.fixture
def operation():
    return ReSortingOperation(
        from_product_id="from-sku",
        to_product_id="to-sku",
        warehouse_id=1,
        quantity=2,
        reason="test",
        author="tester",
    )


def make_service(response):
    repository = AsyncMock()
    repository.re_sorting_operations.return_value = response
    return WarehouseAndBalancesService(repository)


def test_completed_registers_background_notification(operation):
    response = ReSortingOperationResponse(
        operation_status="completed", code_status=201
    )
    service = make_service(response)
    tasks = BackgroundTasks()

    result = asyncio.run(service.re_sorting_operations(operation, tasks))

    assert result == response
    assert len(tasks.tasks) == 1
    assert tasks.tasks[0].func == service.notify_one_c_about_re_sorting
    assert tasks.tasks[0].args == (operation,)


@pytest.mark.parametrize(
    ("operation_status", "code_status"),
    [("failed", 201), ("pending", 201), ("processing", 201), ("PostgresError", 422)],
)
def test_non_completed_does_not_register_notification(
    operation, operation_status, code_status
):
    response = ReSortingOperationResponse(
        operation_status=operation_status,
        code_status=code_status,
        error_message="error",
    )
    service = make_service(response)
    tasks = BackgroundTasks()

    result = asyncio.run(service.re_sorting_operations(operation, tasks))

    assert result == response
    assert tasks.tasks == []


@pytest.mark.parametrize(
    ("status", "event"),
    [
        (200, "one_c_re_sorting_notification_succeeded"),
        (400, "one_c_re_sorting_notification_http_error"),
        (500, "one_c_re_sorting_notification_http_error"),
    ],
)
def test_notification_logs_http_result(
    monkeypatch, caplog, operation, status, event
):
    client = AsyncMock()
    client.re_sorting_operations.return_value = OneCResponse(
        status=status, body="response"
    )
    monkeypatch.setattr(service_module, "ONECRouting", lambda **kwargs: client)
    service = make_service(None)

    with caplog.at_level(logging.INFO):
        asyncio.run(service.notify_one_c_about_re_sorting(operation))

    assert event in caplog.text
    assert f"http_status={status}" in caplog.text


@pytest.mark.parametrize(
    "error",
    [asyncio.TimeoutError(), aiohttp.ClientConnectionError("connection failed")],
)
def test_transport_error_is_caught_and_logged(
    monkeypatch, caplog, operation, error
):
    client = AsyncMock()
    client.re_sorting_operations.side_effect = error
    monkeypatch.setattr(service_module, "ONECRouting", lambda **kwargs: client)
    service = make_service(None)

    with caplog.at_level(logging.ERROR):
        asyncio.run(service.notify_one_c_about_re_sorting(operation))

    assert "one_c_re_sorting_notification_transport_error" in caplog.text


def test_http_error_body_is_truncated(monkeypatch, caplog, operation):
    client = AsyncMock()
    client.re_sorting_operations.return_value = OneCResponse(
        status=500, body="x" * 5000 + "must-not-be-logged"
    )
    monkeypatch.setattr(service_module, "ONECRouting", lambda **kwargs: client)
    service = make_service(None)

    with caplog.at_level(logging.ERROR):
        asyncio.run(service.notify_one_c_about_re_sorting(operation))

    assert "must-not-be-logged" not in caplog.text


def test_one_c_payload_excludes_warehouse_id(monkeypatch, operation):
    captured = {}

    class ResponseContext:
        status = 200

        async def __aenter__(self):
            return self

        async def __aexit__(self, exc_type, exc, traceback):
            return False

        async def text(self):
            return "ok"

    class Session:
        def __init__(self, *, timeout):
            captured["timeout"] = timeout

        async def __aenter__(self):
            return self

        async def __aexit__(self, exc_type, exc, traceback):
            return False

        def post(self, url, *, json, auth):
            captured.update(url=url, payload=json, auth=auth)
            return ResponseContext()

    monkeypatch.setattr(aiohttp, "ClientSession", Session)
    client = ONECRouting(login="login", password="password", base_url="http://1c/")

    response = asyncio.run(client.re_sorting_operations(operation))

    assert response == OneCResponse(status=200, body="ok")
    assert captured["url"] == "http://1c/goods_resorting/"
    assert captured["payload"] == operation.model_dump(exclude={"warehouse_id"})
    assert "warehouse_id" not in captured["payload"]
    assert captured["timeout"].total == 30

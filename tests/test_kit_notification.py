import asyncio
import logging
from unittest.mock import AsyncMock

import aiohttp
import pytest
from fastapi import BackgroundTasks

from app.infrastructure.ONE_C.routing import ONECRouting, OneCResponse
from app.models.warehouse_and_balances import (
    AssemblyMetawildResponse,
    AssemblyOrDisassemblyMetawildData,
)
from app.service import warehouse_and_balances as service_module
from app.service.warehouse_and_balances import WarehouseAndBalancesService


@pytest.fixture
def kit_operation():
    return AssemblyOrDisassemblyMetawildData(
        metawild="kit-sku",
        warehouse_id=1,
        count=2,
        author="tester",
        operation_type="assembly",
    )


def make_service(response):
    repository = AsyncMock()
    repository.assembly_or_disassembly_metawild.return_value = response
    return WarehouseAndBalancesService(repository), repository


def test_completed_kit_operation_registers_background_notification(kit_operation):
    response = AssemblyMetawildResponse(
        product_id="kit-sku", operation_status="completed", code_status=201
    )
    service, repository = make_service(response)
    repository.kit_components_by_product_id.return_value = {"component-sku": 4}
    tasks = BackgroundTasks()

    result = asyncio.run(
        service.assembly_or_disassembly_metawild(kit_operation, tasks)
    )

    assert result == response
    assert len(tasks.tasks) == 1
    assert tasks.tasks[0].func == service.notify_one_c_about_assembly_or_disassembly
    payload, log_context = tasks.tasks[0].args
    assert "warehouse_id" not in payload
    assert payload["kit_komponents"] == [
        {"product_id": "component-sku", "quantity": 4}
    ]


@pytest.mark.parametrize(
    ("operation_status", "code_status"),
    [("failed", 201), ("pending", 201), ("processing", 201), ("PostgresError", 422)],
)
def test_non_completed_kit_operation_does_not_register_notification(
    kit_operation, operation_status, code_status
):
    response = AssemblyMetawildResponse(
        product_id="kit-sku",
        operation_status=operation_status,
        code_status=code_status,
        error_message="error",
    )
    service, _ = make_service(response)
    tasks = BackgroundTasks()

    asyncio.run(service.assembly_or_disassembly_metawild(kit_operation, tasks))

    assert tasks.tasks == []


@pytest.mark.parametrize(
    ("status", "event"),
    [
        (200, "one_c_kit_notification_succeeded"),
        (400, "one_c_kit_notification_http_error"),
        (500, "one_c_kit_notification_http_error"),
    ],
)
def test_kit_notification_logs_http_result(
    monkeypatch, caplog, kit_operation, status, event
):
    client = AsyncMock()
    client.assembly_or_disassembly_metawild.return_value = OneCResponse(
        status=status, body="response"
    )
    monkeypatch.setattr(service_module, "ONECRouting", lambda **kwargs: client)
    service, _ = make_service(None)
    payload = kit_operation.model_dump(exclude={"warehouse_id"})
    payload["kit_komponents"] = [
        {"product_id": "component-sku", "quantity": 4}
    ]
    log_context = {"product_id": kit_operation.metawild}

    with caplog.at_level(logging.INFO):
        asyncio.run(
            service.notify_one_c_about_assembly_or_disassembly(payload, log_context)
        )

    assert event in caplog.text
    sent_payload = client.assembly_or_disassembly_metawild.await_args.kwargs["data"]
    assert "warehouse_id" not in sent_payload
    assert sent_payload["kit_komponents"] == [
        {"product_id": "component-sku", "quantity": 4}
    ]


@pytest.mark.parametrize(
    "error",
    [asyncio.TimeoutError(), aiohttp.ClientConnectionError("connection failed")],
)
def test_kit_transport_error_is_caught(
    monkeypatch, caplog, kit_operation, error
):
    client = AsyncMock()
    client.assembly_or_disassembly_metawild.side_effect = error
    monkeypatch.setattr(service_module, "ONECRouting", lambda **kwargs: client)
    service, _ = make_service(None)
    payload = kit_operation.model_dump(exclude={"warehouse_id"})
    log_context = {"product_id": kit_operation.metawild}

    with caplog.at_level(logging.ERROR):
        asyncio.run(
            service.notify_one_c_about_assembly_or_disassembly(payload, log_context)
        )

    assert "one_c_kit_notification_transport_error" in caplog.text


def test_component_lookup_error_stays_in_request_flow(kit_operation):
    response = AssemblyMetawildResponse(
        product_id="kit-sku", operation_status="completed", code_status=201
    )
    service, repository = make_service(response)
    repository.kit_components_by_product_id.side_effect = RuntimeError("db failed")
    tasks = BackgroundTasks()

    with pytest.raises(RuntimeError, match="db failed"):
        asyncio.run(
            service.assembly_or_disassembly_metawild(kit_operation, tasks)
        )



def test_ass_disass_client_returns_status_and_body(monkeypatch):
    captured = {}

    class ResponseContext:
        status = 500

        async def __aenter__(self):
            return self

        async def __aexit__(self, exc_type, exc, traceback):
            return False

        async def text(self):
            return "1c error"

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
    payload = {"metawild": "kit-sku", "kit_komponents": []}

    response = asyncio.run(client.assembly_or_disassembly_metawild(payload))

    assert response == OneCResponse(status=500, body="1c error")
    assert captured["url"] == "http://1c/ass_disass/"
    assert captured["payload"] == payload
    assert captured["timeout"].total == 30

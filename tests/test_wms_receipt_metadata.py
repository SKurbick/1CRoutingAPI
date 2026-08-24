from datetime import datetime, timezone
from types import ModuleType, SimpleNamespace
import sys
from unittest import IsolatedAsyncioTestCase
from unittest.mock import AsyncMock

from app.database.repositories.wms_receipt_repository import WMSReceiptRepository

# Import the service in isolation from the dependency package's endpoint wiring,
# which otherwise introduces an unrelated circular import during unit discovery.
config_module = ModuleType("app.dependencies.config")
config_module.settings = SimpleNamespace(WMS_API_URL_MOVEMENTS="http://wms/api/movements")
sys.modules["app.dependencies.config"] = config_module

from app.service.wms_integration_service import WMSIntegrationService
from app.service.receipt_of_goods import ReceiptOfGoodsService
from app.models.receipt_of_goods import ReceiptOfGoodsUpdate


NOW = datetime(2026, 7, 22, 10, 30, tzinfo=timezone.utc)
LATER = datetime(2026, 7, 22, 11, 45, tzinfo=timezone.utc)


def make_receipt(quantity=5, **overrides):
    values = {
        "guid": "receipt-guid",
        "document_number": "RCPT-42",
        "supplier_name": "Supplier",
        "supplier_code": "7701234567",
        "document_created_at": NOW,
        "supply_date": NOW,
        "update_document_datetime": LATER,
        "event_status": "Проведен",
        "author_of_the_change": "Иванов",
        "our_organizations_name": "ООО Наша организация",
        "order_guid": "order-guid",
        "currency": "RUB",
        "supply_data": [SimpleNamespace(local_vendor_code="SKU-1", quantity=quantity)],
    }
    values.update(overrides)
    receipt = SimpleNamespace(**values)
    receipt.model_dump = lambda: values
    return receipt


def make_service(existing=None):
    repo = SimpleNamespace(
        get_receipt_item=AsyncMock(return_value=existing),
        create_receipt_item=AsyncMock(return_value=1),
        update_receipt_item_quantity=AsyncMock(),
        get_available_quantity_in_location=AsyncMock(return_value=100),
    )
    service = WMSIntegrationService(repo, pool=None)
    service._get_valid_products = AsyncMock(return_value={"SKU-1"})
    service._create_wms_movements_bulk = AsyncMock(return_value={"total": 1})
    service._create_wms_movement = AsyncMock()
    return service, repo


class WMSReceiptMetadataTests(IsolatedAsyncioTestCase):
    async def test_new_receipt_creates_snapshot_with_document_metadata(self):
        service, repo = make_service()
        receipt = make_receipt()
    
        stats = await service.process_receipts([receipt])
    
        service._create_wms_movements_bulk.assert_awaited_once()
        repo.create_receipt_item.assert_awaited_once_with(
            guid="receipt-guid",
            product_id="SKU-1",
            quantity=5.0,
            document_number="RCPT-42",
            supplier_name="Supplier",
            supplier_code="7701234567",
            document_created_at=NOW,
            supply_date=NOW,
            update_document_datetime=LATER,
            event_status="Проведен",
            author_of_the_change="Иванов",
            our_organizations_name="ООО Наша организация",
            order_guid="order-guid",
            currency="RUB",
        )
        assert stats["created_movements"] == 1
    
    
    async def test_changed_quantity_keeps_movement_flow_and_updates_all_metadata(self):
        service, repo = make_service(existing={"quantity": 3})
        receipt = make_receipt(quantity=5, event_status="Изменен", author_of_the_change="Петров")
    
        await service.process_receipts([receipt])
    
        service._create_wms_movement.assert_awaited_once()
        movement = service._create_wms_movement.await_args.kwargs
        assert movement["movement_type"] == "adjust"
        assert movement["quantity"] == 2.0
        snapshot = repo.update_receipt_item_quantity.await_args.kwargs
        assert snapshot["new_quantity"] == 5.0
        assert snapshot["event_status"] == "Изменен"
        assert snapshot["author_of_the_change"] == "Петров"
        assert snapshot["document_number"] == "RCPT-42"
        assert snapshot["currency"] == "RUB"
    
    
    async def test_unchanged_quantity_updates_metadata_without_movement(self):
        service, repo = make_service(existing={"quantity": 5})
        receipt = make_receipt(
            quantity=5,
            event_status="Отменен",
            update_document_datetime=LATER,
            author_of_the_change="Сидоров",
            supplier_code=None,
            order_guid=None,
            currency=None,
        )
    
        await service.process_receipts([receipt])
    
        service._create_wms_movement.assert_not_awaited()
        repo.get_available_quantity_in_location.assert_not_awaited()
        snapshot = repo.update_receipt_item_quantity.await_args.kwargs
        assert snapshot["new_quantity"] == 5.0
        assert snapshot["event_status"] == "Отменен"
        assert snapshot["update_document_datetime"] == LATER
        assert snapshot["author_of_the_change"] == "Сидоров"
        assert snapshot["supplier_code"] is None
        assert snapshot["order_guid"] is None
        assert snapshot["currency"] is None

    async def test_movement_failure_does_not_update_snapshot(self):
        service, repo = make_service(existing={"quantity": 3})
        service._create_wms_movement.side_effect = RuntimeError("movement failed")

        stats = await service.process_receipts([make_receipt(quantity=5)])

        repo.update_receipt_item_quantity.assert_not_awaited()
        assert stats["errors"][0]["error"] == "movement failed"

    async def test_naive_document_dates_are_assigned_moscow_timezone(self):
        naive = datetime(2026, 7, 22, 12, 30)
        parsed = ReceiptOfGoodsUpdate.model_validate({
            "supply_date": "2026-07-22T12:30:00",
            "supplier_name": "Supplier",
            "guid": "receipt-guid",
            "document_number": "RCPT-42",
            "document_created_at": "2026-07-22T10:00:00",
            "event_status": "Проведен",
            "update_document_datetime": "2026-07-22T13:00:00",
            "author_of_the_change": "Иванов",
            "our_organizations_name": "ООО Наша организация",
            "supply_data": [{
                "local_vendor_code": "SKU-1",
                "product_name": "Product",
                "quantity": 1,
                "amount_with_vat": 1,
            }],
        })

        assert parsed.supply_date.tzinfo is None
        normalized = WMSIntegrationService._normalize_document_datetime(naive)
        assert normalized.utcoffset().total_seconds() == 3 * 60 * 60
        assert normalized.replace(tzinfo=None) == naive

    async def test_aware_document_date_preserves_its_instant(self):
        aware = datetime.fromisoformat("2026-07-22T12:30:00+05:00")
        normalized = WMSIntegrationService._normalize_document_datetime(aware)
        assert normalized is aware
        assert normalized.utcoffset().total_seconds() == 5 * 60 * 60

    async def test_supplier_code_is_none_only_for_absent_or_null_input(self):
        base = {
            "supply_date": "2026-07-22T12:30:00+03:00",
            "supplier_name": "Supplier",
            "guid": "receipt-guid",
            "document_number": "RCPT-42",
            "document_created_at": "2026-07-22T10:00:00+03:00",
            "event_status": "Проведен",
            "update_document_datetime": "2026-07-22T13:00:00+03:00",
            "author_of_the_change": "Иванов",
            "our_organizations_name": "ООО Наша организация",
            "supply_data": [{
                "local_vendor_code": "SKU-1",
                "product_name": "Product",
                "quantity": 1,
                "amount_with_vat": 1,
            }],
        }

        assert ReceiptOfGoodsUpdate.model_validate(base).supplier_code is None
        assert ReceiptOfGoodsUpdate.model_validate({**base, "supplier_code": None}).supplier_code is None
        assert ReceiptOfGoodsUpdate.model_validate({**base, "supplier_code": ""}).supplier_code == ""
        assert ReceiptOfGoodsUpdate.model_validate({**base, "supplier_code": "7701"}).supplier_code == "7701"

    async def test_database_sized_strings_are_not_truncated_by_service(self):
        service, repo = make_service()
        receipt = make_receipt(
            event_status="E" * 100,
            author_of_the_change="A" * 255,
            our_organizations_name="O" * 500,
            order_guid="G" * 255,
            currency="C" * 50,
        )

        await service.process_receipts([receipt])

        snapshot = repo.create_receipt_item.await_args.kwargs
        assert len(snapshot["event_status"]) == 100
        assert len(snapshot["author_of_the_change"]) == 255
        assert len(snapshot["our_organizations_name"]) == 500
        assert len(snapshot["order_guid"]) == 255
        assert len(snapshot["currency"]) == 50

    async def test_nullable_metadata_is_forwarded_to_snapshot_insert(self):
        service, repo = make_service()
        receipt = make_receipt(supplier_code=None, order_guid=None, currency=None)
    
        await service.process_receipts([receipt])
    
        snapshot = repo.create_receipt_item.await_args.kwargs
        assert snapshot["supplier_code"] is None
        assert snapshot["order_guid"] is None
        assert snapshot["currency"] is None
    
    
class FakeConnection:
    def __init__(self):
        self.fetchrow = AsyncMock(return_value={"receipt_item_id": 9})
        self.execute = AsyncMock()


class AcquireContext:
    def __init__(self, connection):
        self.connection = connection

    async def __aenter__(self):
        return self.connection

    async def __aexit__(self, exc_type, exc, tb):
        return False


class FakePool:
    def __init__(self, connection):
        self.connection = connection

    def acquire(self):
        return AcquireContext(self.connection)


class WMSReceiptRepositoryTests(IsolatedAsyncioTestCase):
    async def test_repository_insert_is_parameterized_and_preserves_nulls(self):
        connection = FakeConnection()
        repository = WMSReceiptRepository(FakePool(connection))

        created = datetime(2026, 7, 20, 8, 1, tzinfo=timezone.utc)
        supplied = datetime(2026, 7, 21, 9, 2, tzinfo=timezone.utc)
        updated = datetime(2026, 7, 22, 10, 3, tzinfo=timezone.utc)
        expected = [
            "receipt-guid", "SKU-1", 5, "RCPT-42", "Supplier", "supplier-code",
            created, supplied, updated, "Проведен", "Иванов",
            "ООО Наша организация", "order-guid", "RUB",
        ]
        item_id = await repository.create_receipt_item(*expected)

        sql, *params = connection.fetchrow.await_args.args
        assert item_id == 9
        assert "VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13, $14)" in sql
        assert params == expected
        assert "updated_at" not in sql


class WMSReceiptUpdateRepositoryTests(IsolatedAsyncioTestCase):
    async def test_repository_update_is_parameterized_and_uses_db_trigger_for_updated_at(self):
        connection = FakeConnection()
        repository = WMSReceiptRepository(FakePool(connection))

        created = datetime(2026, 7, 20, 8, 1, tzinfo=timezone.utc)
        supplied = datetime(2026, 7, 21, 9, 2, tzinfo=timezone.utc)
        updated = datetime(2026, 7, 22, 10, 3, tzinfo=timezone.utc)
        expected = [
            "receipt-guid", "SKU-1", 7, "RCPT-43", "New Supplier", "new-code",
            created, supplied, updated, "Изменен", "Петров",
            "ООО Новая организация", "new-order-guid", "USD",
        ]
        await repository.update_receipt_item_quantity(*expected)

        sql, *params = connection.execute.await_args.args
        assert "quantity = $3" in sql
        assert "currency = $14" in sql
        assert "updated_at" not in sql
        assert params == expected


class ReceiptResponseCompatibilityTests(IsolatedAsyncioTestCase):
    async def test_receipt_service_keeps_existing_response_object(self):
        response = SimpleNamespace(status=201, message="created", details=None)
        receipt_repository = SimpleNamespace(update_data=AsyncMock(return_value=response))
        wms_service = SimpleNamespace(process_receipts=AsyncMock(return_value={
            "created_movements": 0,
            "adjusted_movements": 0,
            "skipped_products": [],
            "adjustment_warnings": [],
        }))
        service = ReceiptOfGoodsService(receipt_repository, wms_service)

        result = await service.create_data([make_receipt()])

        assert result is response
        assert result.status == 201
        assert result.message == "created"
        assert result.details is None

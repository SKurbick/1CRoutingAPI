from .receipt_of_goods import router as receipt_of_goods_router
from .financial_transactions import router as income_on_bank_account_router
from .shipment_of_goods import router as shipment_of_goods_router
from .ordered_goods_from_buyers import router as ordered_goods_from_buyers_router
from .local_barcode_generation import router as local_barcode_generation_router
from .warehouse_and_balances import router as warehouse_and_balances_router
from .goods_information import router as goods_information_router
from .inventory_check import router as inventory_check_router
from .inventory_transactions import router as inventory_transactions_router
from .return_of_goods import router as return_of_goods_router
from .docs import router as docs_router
__all__ = [
    'receipt_of_goods_router',
    'income_on_bank_account_router',
    'shipment_of_goods_router',
    'ordered_goods_from_buyers_router',
    'local_barcode_generation_router',
    'warehouse_and_balances_router',
    'goods_information_router',
    'inventory_check_router',
    'inventory_transactions_router',
    'return_of_goods_router',
    'docs_router'
]

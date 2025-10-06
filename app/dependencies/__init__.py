from .receipt_of_goods import get_receipt_of_goods_service
from .income_on_bank_account import get_income_on_bank_account_service
from .shipment_of_goods import get_shipment_of_goods_service
from .ordered_goods_from_buyers import get_ordered_goods_from_buyers_service
from .local_barcode_generation import local_barcode_generation_service
from .warehouse_and_balances import get_warehouse_and_balances_service
from .goods_information import get_goods_information_service
from .inventory_check import get_inventory_check_service
from .inventory_transactions import get_inventory_transactions_service
from .return_of_goods import get_return_of_goods_service
from .goods_managers import get_goods_managers_service

__all__ = [
    'get_income_on_bank_account_service',
    'get_receipt_of_goods_service',
    'get_shipment_of_goods_service',
    'get_ordered_goods_from_buyers_service',
    'local_barcode_generation_service',
    'get_warehouse_and_balances_service',
    'get_goods_information_service',
    'get_inventory_check_service',
    'get_inventory_transactions_service',
<<<<<<< HEAD
    'get_return_of_goods_service'
=======
    'get_return_of_goods_service',
    'get_docs_service',
    'get_goods_managers_service',
>>>>>>> a8f6d06 ([+] Добавил получение списка менеджеров товаров.)
]

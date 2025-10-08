from fastapi import APIRouter

from .endpoints import (receipt_of_goods_router, income_on_bank_account_router, shipment_of_goods_router,
                        ordered_goods_from_buyers_router, local_barcode_generation_router, warehouse_and_balances_router,
                        goods_information_router, inventory_check_router, inventory_transactions_router, 
                        return_of_goods_router, docs_router, goods_managers_router)


router = APIRouter()

router.include_router(receipt_of_goods_router)
router.include_router(income_on_bank_account_router)
router.include_router(shipment_of_goods_router)
router.include_router(ordered_goods_from_buyers_router)
router.include_router(local_barcode_generation_router)
router.include_router(warehouse_and_balances_router)
router.include_router(goods_information_router)
router.include_router(inventory_check_router)
router.include_router(inventory_transactions_router)
router.include_router(return_of_goods_router)
router.include_router(docs_router)
router.include_router(goods_managers_router)

__all__ = [
    "router",
]

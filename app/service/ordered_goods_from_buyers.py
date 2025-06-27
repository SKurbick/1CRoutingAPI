import datetime
from pprint import pprint
from typing import List

from app.models import OrderedGoodsFromBuyersUpdate
from app.database.repositories import OrderedGoodsFromBuyersRepository
from app.models.ordered_goods_from_buyers import OrderedGoodsFromBuyersResponse, IsAcceptanceStatus, OrderedGoodsAndPrintedBarcodeData


class OrderedGoodsFromBuyersService:
    def __init__(
            self,
            ordered_goods_from_buyers_repository: OrderedGoodsFromBuyersRepository,
    ):
        self.ordered_goods_from_buyers_repository = ordered_goods_from_buyers_repository

    async def create_data(self, data: List[OrderedGoodsFromBuyersUpdate]) -> OrderedGoodsFromBuyersResponse:
        result = await self.ordered_goods_from_buyers_repository.update_data(data)
        return result

    async def get_buyer_orders(self, date_from: datetime.date, date_to: datetime.date, in_acceptance: bool) -> OrderedGoodsAndPrintedBarcodeData:
        printed_barcode_data = []

        ogb_data = await self.ordered_goods_from_buyers_repository.get_buyer_orders(date_from=date_from, date_to=date_to, in_acceptance=in_acceptance)
        vendor_codes = []
        for res in ogb_data:
            lvc = res.local_vendor_code
            if lvc.startswith("wild"):
                vendor_codes.append(lvc)

        if in_acceptance:
            printed_barcode_data = await self.ordered_goods_from_buyers_repository.get_printed_barcodes()
            for res in printed_barcode_data:
                lvc = res.product
                if lvc.startswith("wild"):
                    vendor_codes.append(lvc)

        photo_link_by_lvc_data = await self.ordered_goods_from_buyers_repository.get_photo_link_by_wilds(vendor_codes=vendor_codes)

        if in_acceptance:
            for item in printed_barcode_data:
                lvc = item.product
                if lvc in photo_link_by_lvc_data:
                    item.photo_link = photo_link_by_lvc_data[lvc]

        for item in ogb_data:
            lvc = item.local_vendor_code
            if lvc in photo_link_by_lvc_data:
                item.photo_link = photo_link_by_lvc_data[lvc]

        pprint(printed_barcode_data)

        return OrderedGoodsAndPrintedBarcodeData(ordered_of_goods_data=ogb_data, printed_barcode_data=printed_barcode_data)

    async def update_acceptance_status(self, data: List[IsAcceptanceStatus]):
        result = await self.ordered_goods_from_buyers_repository.update_acceptance_status(data=data)
        return result

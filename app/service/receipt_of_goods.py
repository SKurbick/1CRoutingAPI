from pprint import pprint
from typing import List

from app.dependencies.config import settings
from app.infrastructure.ONE_C import ONECRouting
from app.models import ReceiptOfGoodsUpdate, AddIncomingReceiptUpdate
from app.database.repositories import ReceiptOfGoodsRepository
from app.models.receipt_of_goods import ReceiptOfGoodsResponse


class ReceiptOfGoodsService:
    def __init__(
            self,
            receipt_of_goods_repository: ReceiptOfGoodsRepository,
    ):
        self.receipt_of_goods_repository = receipt_of_goods_repository

    async def create_data(self, data: List[ReceiptOfGoodsUpdate]) -> ReceiptOfGoodsResponse:
        result = await self.receipt_of_goods_repository.update_data(data)
        return result

    async def add_incoming_receipt(self, data: List[AddIncomingReceiptUpdate]) -> ReceiptOfGoodsResponse:
        result = await self.receipt_of_goods_repository.add_incoming_receipt(data)
        #  при успешном выполнении вставки отправлять запрос в 1с
        if result.status == 201:
            guid_data = []
            for values in data:
                guid_data.append(values.guid)

            one_c_model_data = await self.receipt_of_goods_repository.get_one_c_model_data(guid_data= guid_data)
            pprint(one_c_model_data)
            pprint(guid_data)

            one_c_connect = ONECRouting(base_url=settings.ONE_C_BASE_URL, password=settings.ONE_C_PASSWORD, login=settings.ONE_C_LOGIN)
            await one_c_connect.receipt_of_goods_update(data= one_c_model_data)
        return result

    async def add_or_update_one_c_document(self,  data: List[AddIncomingReceiptUpdate]):
        """
        40fc6fcd-5af8-11f0-84f2-50ebf6b2ce7d
        2b58cb62-50d2-11f0-84f2-50ebf6b2ce7d
        """
        # собираем все guid из data
        # получаем данные по совпадению guid  из таблицы goods_acceptance_certificate и ordered_goods_from_buyers с условием is_printed
        # поля: guid
            # local_vendor_code
            # product_name
            # quantity
            # amount_with_vat
            # amount_without_vat
        # на основании этих данных собираем модель для отправки в 1С
        pass

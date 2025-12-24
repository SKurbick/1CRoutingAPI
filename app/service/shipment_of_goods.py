import datetime
from pprint import pprint
from typing import List

from app.dependencies.config import settings, account_inn_map
from app.infrastructure.ONE_C import ONECRouting
from app.models import ShipmentOfGoodsUpdate, ShippedGoodsByID, WriteOffAccordingToFBS
from app.database.repositories import ShipmentOfGoodsRepository
from app.models.shipment_of_goods import ShipmentOfGoodsResponse, ShipmentParamsData, ReserveOfGoodsResponse, ReserveOfGoodsCreate, ShippedGoods, DeliveryType, \
    ReservedData, CreationWithMovement, ShipmentWithReserveUpdating


class ShipmentOfGoodsService:
    def __init__(
            self,
            shipment_of_goods_repository: ShipmentOfGoodsRepository,
    ):
        self.shipment_of_goods_repository = shipment_of_goods_repository




    async def write_off_according_to_fbs(self, data: List[WriteOffAccordingToFBS])-> ShipmentOfGoodsResponse:
        result = await self.shipment_of_goods_repository.write_off_according_to_fbs(data)

        return result

    async def shipment_with_reserve_updating(self, data: List[ShipmentWithReserveUpdating], delivery_type: DeliveryType) -> ShipmentOfGoodsResponse:
        #todo предпроверка на метод отгрузки. Если ФБО - запрос в 1с
        result = await self.shipment_of_goods_repository.shipment_with_reserve_updating(data)
        if result.status == 201:
            match delivery_type:  # запрос для 1С
                case DeliveryType.FBO:
                    try:
                        one_c_connect = ONECRouting(base_url=settings.ONE_C_BASE_URL, password=settings.ONE_C_PASSWORD, login=settings.ONE_C_LOGIN)
                        refactoring_data = one_c_connect.refactoring_to_account_data(shipments=data, account_to_inn=account_inn_map)
                        pprint(refactoring_data)
                        one_c_result = await one_c_connect.commission_sales_fbo_add(data=refactoring_data)
                        print(one_c_result)
                    except Exception as e:
                        print(e)
        return result


    async def creation_reserve_with_movement(self, data: List[CreationWithMovement], delivery_type) -> ShipmentOfGoodsResponse:
        result = await self.shipment_of_goods_repository.creation_reserve_with_movement(data)
        return result

    async def get_summ_reserve_data(self):

        result = await self.shipment_of_goods_repository.get_summ_reserve_data()
        return result

    async def add_shipped_goods_by_id(self, data: List[ShippedGoodsByID]) -> ShipmentOfGoodsResponse:
        result = await self.shipment_of_goods_repository.add_shipped_goods_by_id(data)
        return result

    async def get_reserved_data(self, is_fulfilled: bool | None, begin_date: datetime.date | None, delivery_type: DeliveryType | None) -> List[ReservedData]:
        result = await self.shipment_of_goods_repository.get_reserved_data(is_fulfilled=is_fulfilled, begin_date=begin_date, delivery_type=delivery_type)
        return result

    async def create_data(self, data: List[ShipmentOfGoodsUpdate], delivery_type: DeliveryType) -> ShipmentOfGoodsResponse:
        result = await self.shipment_of_goods_repository.update_data(data)
        if result.status == 201:
            match delivery_type:  # запрос для 1С
                case DeliveryType.FBO:
                    try:
                        one_c_connect = ONECRouting(base_url=settings.ONE_C_BASE_URL, password=settings.ONE_C_PASSWORD, login=settings.ONE_C_LOGIN)
                        refactoring_data = one_c_connect.refactoring_to_account_data(shipments=data, account_to_inn=account_inn_map)
                        one_c_result = await one_c_connect.commission_sales_fbo_add(data=refactoring_data)
                        print(one_c_result)
                    except Exception as e:
                        print(e)
        return result

    async def get_shipment_params(self) -> ShipmentParamsData:
        result = await self.shipment_of_goods_repository.get_shipment_params()
        return result

    async def create_reserve(self, data: List[ReserveOfGoodsCreate]) -> List[ReserveOfGoodsResponse]| ShipmentOfGoodsResponse:
        result = await self.shipment_of_goods_repository.create_reserve(data)
        return result

    async def add_shipped_goods(self, data: List[ShippedGoods]) -> List[ReserveOfGoodsResponse]| ShipmentOfGoodsResponse:
        result = await self.shipment_of_goods_repository.add_shipped_goods(data)
        return result

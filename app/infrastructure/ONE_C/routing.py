from dataclasses import dataclass

import aiohttp
from aiohttp import BasicAuth

from typing import List, Dict
from collections import defaultdict

from app.models import ShipmentOfGoodsUpdate, OneCModelUpdate, ReturnsOneCModelAdd, ReSortingOperation
from app.models.one_c import AccountData, Wild, Order, SupplyData

@dataclass(frozen=True)
class OneCResponse:
    status: int
    body: str



class ONECRouting:
    def __init__(self, login, password, base_url):
        self.base_url = base_url
        self.login = login
        self.password = password

    async def assembly_or_disassembly_metawild(self, data) -> OneCResponse:
        url = self.base_url + "ass_disass/"

        timeout = aiohttp.ClientTimeout(total=30)
        async with aiohttp.ClientSession(timeout=timeout) as session:
            async with session.post(
                    url, json=data, auth=BasicAuth(self.login, self.password)
            ) as response:
                body = await response.text()
                return OneCResponse(status=response.status, body=body)

    async def re_sorting_operations(self, data: ReSortingOperation) -> OneCResponse:
        url = self.base_url + "goods_resorting/"
        model_dump_json_data = data.model_dump(exclude={"warehouse_id"})

        timeout = aiohttp.ClientTimeout(total=30)
        async with aiohttp.ClientSession(timeout=timeout) as session:
            async with session.post(
                    url, json=model_dump_json_data, auth=BasicAuth(self.login, self.password)
            ) as response:
                body = await response.text()
                return OneCResponse(status=response.status, body=body)

    async def goods_returns(
            self, data: List[ReturnsOneCModelAdd]
    ) -> OneCResponse:
        url = self.base_url + "goods_return/"
        payload = [value.model_dump(exclude_none=True) for value in data]
        return await self._post(url, payload, timeout_seconds=300)

    async def receipt_of_goods_update(
            self, data: List[OneCModelUpdate]
    ) -> OneCResponse:
        url = self.base_url + "inc_invoice/"
        payload = [value.model_dump() for value in data]
        return await self._post(url, payload, timeout_seconds=300)

    async def commission_sales_fbo_add(self, data) -> OneCResponse:
        url = self.base_url + "commission_sales_fbo/"
        return await self._post(url, data, timeout_seconds=60)

    async def product_writeoff(self, data) -> OneCResponse:
        url = self.base_url + "spisanie/"
        payload = [item.model_dump() for item in data]
        return await self._post(url, payload, timeout_seconds=60)

    async def _post(
            self, url: str, payload, timeout_seconds: int
    ) -> OneCResponse:
        timeout = aiohttp.ClientTimeout(total=timeout_seconds)
        async with aiohttp.ClientSession(timeout=timeout) as session:
            async with session.post(
                    url, json=payload, auth=BasicAuth(self.login, self.password)
            ) as response:
                body = await response.text()
                return OneCResponse(status=response.status, body=body)

    @staticmethod
    def refactoring_to_account_data(
            shipments: List[ShipmentOfGoodsUpdate],
            account_to_inn: Dict[str, str]  # {"account": "inn"}
    ) -> List[AccountData]:
        # 1. Группируем поставки по аккаунту и supply_id
        account_supplies_map: Dict[str, Dict[str, List[ShipmentOfGoodsUpdate]]] = defaultdict(lambda: defaultdict(list))

        for shipment in shipments:
            account_supplies_map[shipment.account][shipment.supply_id].append(shipment)

        # 2. Собираем результат
        result = []

        for account, supplies in account_supplies_map.items():
            inn = account_to_inn.get(account, "000000000000")
            supply_data_list = []

            for supply_id, shipments_in_supply in supplies.items():
                # Группируем товары по product_id и суммируем quantity
                product_quantities: Dict[str, int] = defaultdict(int)
                for shipment in shipments_in_supply:
                    product_quantities[shipment.product_id] += shipment.quantity

                # Формируем wilds для поставки
                wilds = [
                    Wild(wild_code=pid, orders=[Order(sum=0, count=qty)])
                    for pid, qty in product_quantities.items()
                ]

                supply_data_list.append(SupplyData(
                    supply_id=supply_id,
                    wilds=wilds
                ))

            result.append(AccountData(
                account=account,
                inn=inn,
                data=supply_data_list
            ).model_dump())

        return result

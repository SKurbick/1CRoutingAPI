from pprint import pprint

import aiohttp
import asyncio
from aiohttp import BasicAuth

from typing import List, Dict
from collections import defaultdict

from app.models import ShipmentOfGoodsUpdate, OneCModelUpdate, ReturnsOneCModelAdd
from app.models.one_c import AccountData, Wild, Order, SupplyData


class ONECRouting:
    def __init__(self, login, password, base_url):
        self.base_url = base_url
        self.login = login
        self.password = password

    async def goods_returns(self, data: List[ReturnsOneCModelAdd]):
        url = self.base_url + "goods_return/"
        model_dump_json_data = [value.model_dump() for value in data]

        print(model_dump_json_data)
        async with aiohttp.ClientSession() as session:
            async with session.request(method="POST", url=url, json=model_dump_json_data, auth=BasicAuth(self.login, self.password)) as response:
                print(response.status)
                json_response = await response.text()
                print(json_response)
                return json_response

    async def receipt_of_goods_update(self, data: List[OneCModelUpdate]):
        url = self.base_url + "inc_invoice/"
        model_dump_json_data = [value.model_dump() for value in data]
        print(model_dump_json_data)
        async with aiohttp.ClientSession() as session:
            async with session.request(method="POST", url=url, json=model_dump_json_data, auth=BasicAuth(self.login, self.password)) as response:
                print(response.status)
                json_response = await response.text()
                return json_response

    async def commission_sales_fbo_add(self, data):
        url = self.base_url + "commission_sales_fbo/"
        async with aiohttp.ClientSession() as session:
            async with session.request(method="POST", url=url, json=data, auth=BasicAuth(self.login, self.password)) as response:
                print(response.status)
                json_response = await response.text()
                return json_response

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
            ).model_dump_json())

        return result

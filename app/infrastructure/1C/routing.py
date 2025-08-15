from pprint import pprint

import aiohttp
import asyncio
from aiohttp import BasicAuth

from typing import List, Dict
from collections import defaultdict

from app.models import ShipmentOfGoodsUpdate
from app.models.one_c import AccountData, Wild, Order, SupplyData


class ONECRouting:
    def __init__(self):
        self.base_url = "http://194.156.125.15:45123/ut_new_test/hs/docs/"
        self.login = 'user3458'
        self.password = '53Bigipa'

    async def commission_sales_fbo_add(self, data):
        url = self.base_url + "commission_sales_fbo/"
        async with aiohttp.ClientSession() as session:
            async with session.request(method="POST", url=url, json=data, auth=BasicAuth(self.login, self.password)) as response:
                print(response.status)
                json_response = await response.text()
                print(json_response)

    def shipments_to_account_data(self,
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
            ))

        return result


data = [
    {
        "account": "Хачатрян",
        "inn": "771675966776",
        "data": [
            {
                "supply_id": "170261889",
                "wilds": [
                    {
                        "wild_code": "wild128",
                        "orders": [
                            {
                                "sum": 0,
                                "count": 1
                            }
                        ]
                    }
                ]
            }
        ]
    }
]
# Тестовые данные
# shipments = [
#     ShipmentOfGoodsUpdate(account="A", supply_id="S1", product_id="P1", quantity=1, author="", shipment_date=None, product_reserves_id=None, warehouse_id=1,
#                           delivery_type="ФБО"),
#     ShipmentOfGoodsUpdate(account="A", supply_id="S1", product_id="P1", quantity=2, author="", shipment_date=None, product_reserves_id=None, warehouse_id=1,
#                           delivery_type="ФБО"),
#     ShipmentOfGoodsUpdate(account="A", supply_id="S1", product_id="P2", quantity=5, author="", shipment_date=None, product_reserves_id=None, warehouse_id=1,
#                           delivery_type="ФБО"),
#     ShipmentOfGoodsUpdate(account="A", supply_id="S2", product_id="P3", quantity=4, author="", shipment_date=None, product_reserves_id=None, warehouse_id=1,
#                           delivery_type="ФБО"),
#     ShipmentOfGoodsUpdate(account="B", supply_id="S3", product_id="P1", quantity=10, author="", shipment_date=None, product_reserves_id=None, warehouse_id=1,
#                           delivery_type="ФБО"),
# ]
#
# account_to_inn = {"A": "1234567890", "B": "9876543210"}


# pprint(shipments)
# async def test():
#     test = ONECRouting()
#     await test.commission_sales_fbo_add(data)
#     # res = test.shipments_to_account_data(account_to_inn=account_to_inn, shipments=shipments)
#     # data = [account_data.model_dump() for account_data in res]
#     # pprint(data)
#
#
# asyncio.run(test())

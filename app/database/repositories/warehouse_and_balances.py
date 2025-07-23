import json
from pprint import pprint
from typing import List, Tuple

import asyncpg
from asyncpg import Pool, UniqueViolationError
from app.models import DefectiveGoodsUpdate
from app.models.warehouse_and_balances import DefectiveGoodsResponse, Warehouse, CurrentBalances, ValidStockData, ComponentsInfo, \
    AssemblyOrDisassemblyMetawildData, \
    AssemblyMetawildResponse, WarehouseAndBalanceResponse


class WarehouseAndBalancesRepository:
    def __init__(self, pool: Pool):
        self.pool = pool

    async def add_defective_goods(self, data: List[DefectiveGoodsUpdate]) -> DefectiveGoodsResponse:
        data_to_update: List[Tuple] = []
        insert_query = """
        INSERT INTO inventory_transactions (transaction_type, author, product_id, warehouse_id, quantity, correction_comment, status_id )
        VALUES ($1, $2, $3, $4, $5, $6, $7) ;
        """

        for defective_goods in data:
            data_to_update.extend(
                [
                    ("outgoing", defective_goods.author, defective_goods.product_id, defective_goods.from_warehouse, defective_goods.quantity,
                     defective_goods.correction_comment, defective_goods.status_id),
                    ("incoming", defective_goods.author, defective_goods.product_id, defective_goods.to_warehouse, defective_goods.quantity,
                     defective_goods.correction_comment, defective_goods.status_id)
                ]
            )
        pprint(data_to_update)
        async with self.pool.acquire() as conn:
            async with conn.transaction():
                await conn.executemany(insert_query, data_to_update)

        result = DefectiveGoodsResponse(
            status=201,
            message="Данные успешно обновлены"
        )
        return result

    async def get_warehouses(self) -> List[Warehouse]:
        select_query = """
        SELECT * FROM warehouses;
        """
        async with self.pool.acquire() as conn:
            result = await conn.fetch(select_query)

        return [Warehouse(**res) for res in result]

    async def get_all_product_current_balances(self) -> List[CurrentBalances]:
        select_query = """
        SELECT * FROM current_balances;
        """
        async with self.pool.acquire() as conn:
            result = await conn.fetch(select_query)
        pprint(result)
        return [CurrentBalances(**res) for res in result]

    async def get_valid_stock_data(self) -> List[ValidStockData]:
        select_query = """
        SELECT * FROM product_availability;
        """
        async with self.pool.acquire() as conn:
            result = await conn.fetch(select_query)

        stock_data = []
        for row in result:
            components_info = None
            if row['is_kit'] and row['components_info']:
                # Парсим JSON строку в список словарей
                components_list = json.loads(row['components_info'])
                components_info = [
                    ComponentsInfo(
                        component_id=str(comp['component_id']),
                        required=int(comp['required']),
                        available=int(comp['available'])
                    )
                    for comp in components_list
                ]

            stock_data.append(
                ValidStockData(
                    product_id=str(row['product_id']),
                    name=str(row['name']),
                    is_kit=bool(row['is_kit']),
                    warehouse_id=1,
                    available_stock=int(row['available_stock']),
                    components_info=components_info
                )
            )

        return stock_data

    async def assembly_or_disassembly_metawild(self, data: AssemblyOrDisassemblyMetawildData) -> AssemblyMetawildResponse:
        data_to_insert = (data.warehouse_id, data.metawild, data.operation_type, data.count, data.author)
        try:
            insert_query = """
            INSERT INTO kit_operations 
            (warehouse_id, kit_product_id, operation_type, quantity, author)
            VALUES 
            ($1, $2, $3, $4, $5)
            RETURNING id;
            """
            select_query = """
            SELECT kit_product_id AS product_id,  status AS operation_status,  error_message FROM kit_operations
                   WHERE id = $1;
            """
            async with self.pool.acquire() as conn:
                result_id = await conn.fetchrow(insert_query, *data_to_insert)
                while True:
                    check_status = await conn.fetchrow(select_query, result_id['id'])
                    pprint(check_status)
                    if check_status['operation_status'] != 'pending':
                        break
                return AssemblyMetawildResponse(**check_status,code_status=201)
        except asyncpg.PostgresError as e:
            return AssemblyMetawildResponse(
                product_id=data.metawild,
                code_status=422,
                operation_status="PostgresError",
                error_message=str(e)
            )

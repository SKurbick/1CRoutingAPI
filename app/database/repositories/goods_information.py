import datetime
import json
from typing import List, Tuple

import asyncpg
from asyncpg import Pool
from app.models import OrderedGoodsFromBuyersUpdate, OrderedGoodsFromBuyersResponse, OrderedGoodsFromBuyersData, PrintedBarcodeData, \
    GoodsAcceptanceCertificateCreate, MetawildsData
from app.models.ordered_goods_from_buyers import IsAcceptanceStatus


class GoodsInformationRepository:
    def __init__(self, pool: Pool):
        self.pool = pool

    async def get_metawilds_data(self) -> List[MetawildsData]:
        query = """
            SELECT * FROM products WHERE is_kit = TRUE;
        """
        async with self.pool.acquire() as conn:
            result = await conn.fetch(query)

        metawilds_data = []
        for res in result:
            # Преобразуем строку kit_components в словарь
            try:
                kit_components = json.loads(res['kit_components'])
            except (json.JSONDecodeError, TypeError):
                kit_components = {}

            metawilds_data.append(
                MetawildsData(
                    id=res['id'],
                    name=res['name'],
                    kit_components=kit_components
                )
            )

        return metawilds_data

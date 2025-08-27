from typing import Dict

from asyncpg import Pool


class DocsRepository:
    def __init__(self, pool: Pool):
        self.pool = pool

    async def get_tokens(self) -> Dict:
        query = """
        SELECT account_name, token FROM seller_account;
        """
        async with self.pool.acquire() as conn:
            select_result = await conn.fetch(query)
        result = {account_name: token for account_name, token in select_result}

        return result

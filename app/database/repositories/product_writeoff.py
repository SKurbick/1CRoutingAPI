from typing import List
from uuid import UUID

from asyncpg import Pool

from app.models.product_writeoff import (
    ProductWriteoffItem,
    ProductWriteoffOperation,
)


class ProductWriteoffRepository:
    def __init__(self, pool: Pool):
        self.pool = pool

    async def create_pending(
        self,
        request_id: UUID,
        items: List[ProductWriteoffItem],
    ) -> None:
        query = """
        INSERT INTO product_writeoffs
            (request_id, product_id, quantity, comment, delivery_status)
        VALUES ($1, $2, $3, $4, 'pending')
        """
        records = [
            (request_id, item.product_id, item.quantity, item.comment)
            for item in items
        ]
        async with self.pool.acquire() as conn:
            async with conn.transaction():
                await conn.executemany(query, records)

    async def mark_delivery_result(
        self,
        request_id: UUID,
        delivery_status: str,
        one_c_http_status: int | None,
        one_c_response: str | None,
        error_message: str | None,
    ) -> None:
        query = """
        UPDATE product_writeoffs
        SET delivery_status = $2::varchar,
            one_c_http_status = $3,
            one_c_response = $4,
            error_message = $5,
            attempt_count = attempt_count + 1,
            last_attempt_at = NOW(),
            sent_at = CASE WHEN $2::varchar = 'sent' THEN NOW() ELSE sent_at END,
            updated_at = NOW()
        WHERE request_id = $1
        """
        async with self.pool.acquire() as conn:
            await conn.execute(
                query,
                request_id,
                delivery_status,
                one_c_http_status,
                one_c_response,
                error_message,
            )

    async def claim_failed_for_retry(
        self,
        request_id: UUID,
    ) -> tuple[str, List[ProductWriteoffItem]]:
        select_query = """
        SELECT product_id, quantity, comment, delivery_status
        FROM product_writeoffs
        WHERE request_id = $1
        ORDER BY id
        FOR UPDATE
        """
        update_query = """
        UPDATE product_writeoffs
        SET delivery_status = 'pending',
            one_c_http_status = NULL,
            one_c_response = NULL,
            error_message = NULL,
            updated_at = NOW()
        WHERE request_id = $1
        """
        async with self.pool.acquire() as conn:
            async with conn.transaction():
                rows = await conn.fetch(select_query, request_id)
                if not rows:
                    return "not_found", []
                if any(row["delivery_status"] != "failed" for row in rows):
                    return "not_retryable", []
                await conn.execute(update_query, request_id)
                return "claimed", [
                    ProductWriteoffItem(
                        product_id=row["product_id"],
                        quantity=row["quantity"],
                        comment=row["comment"],
                    )
                    for row in rows
                ]

    async def get_operations(
        self,
        product_id: str | None,
        statuses: List[str] | None,
        limit: int,
        offset: int,
    ) -> tuple[List[ProductWriteoffOperation], int]:
        conditions = []
        params = []
        if product_id is not None:
            params.append(product_id)
            conditions.append(f"product_id = ${len(params)}")
        if statuses:
            params.append(statuses)
            conditions.append(f"delivery_status = ANY(${len(params)}::varchar[])")

        where_clause = f"WHERE {' AND '.join(conditions)}" if conditions else ""
        count_query = f"SELECT COUNT(*) FROM product_writeoffs {where_clause}"
        total = await self._fetch_count(count_query, params)

        params.extend([limit, offset])
        select_query = f"""
        SELECT id, request_id, product_id, quantity, comment, delivery_status,
               one_c_http_status, one_c_response, error_message,
               attempt_count, last_attempt_at, created_at, updated_at, sent_at
        FROM product_writeoffs
        {where_clause}
        ORDER BY created_at DESC, id DESC
        LIMIT ${len(params) - 1} OFFSET ${len(params)}
        """
        async with self.pool.acquire() as conn:
            rows = await conn.fetch(select_query, *params)
        return [ProductWriteoffOperation(**dict(row)) for row in rows], total

    async def _fetch_count(self, query: str, params: list) -> int:
        async with self.pool.acquire() as conn:
            return await conn.fetchval(query, *params)

import json
from collections.abc import Iterable

from asyncpg import Connection

from app.models.return_of_goods import MarkCode


async def enqueue_kiz_returns(conn: Connection, marks: Iterable[MarkCode]) -> None:
    """Call inside the receipt transaction; preserve the original code bytes."""
    mark_codes = list(dict.fromkeys(
        mark.mark_code for mark in marks
        if mark.mark_code.strip() and mark.mark_code.strip().lower() != "broken"
    ))
    if mark_codes:
        await conn.execute(
            """
            INSERT INTO public.kiz_returns_outbox (payload)
            VALUES ($1::jsonb);
            """,
            json.dumps({"mark_codes": mark_codes}, ensure_ascii=False),
        )

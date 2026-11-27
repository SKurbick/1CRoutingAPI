import asyncio
import json
import logging
from contextlib import suppress

from asyncpg import Pool

from app.broker.kiz_returns import KizReturnsPublisher

logger = logging.getLogger(__name__)


class KizReturnsOutboxWorker:
    def __init__(self, pool: Pool, publisher: KizReturnsPublisher, poll_interval: float):
        self.pool = pool
        self.publisher = publisher
        self.poll_interval = poll_interval
        self.task = None

    def start(self) -> None:
        self.task = asyncio.create_task(self.run(), name="kiz-returns-outbox")

    async def close(self) -> None:
        if self.task is not None:
            self.task.cancel()
            with suppress(asyncio.CancelledError):
                await self.task
        await self.publisher.close()

    async def process_one(self) -> bool:
        async with self.pool.acquire() as conn:
            async with conn.transaction():
                # Keep the lock until confirmation/status update. Other API
                # processes skip it; a crash releases the lock for redelivery.
                row = await conn.fetchrow(
                    """
                    SELECT id, payload, attempts
                    FROM public.kiz_returns_outbox
                    WHERE sent_at IS NULL AND next_attempt_at <= NOW()
                    ORDER BY next_attempt_at, id
                    LIMIT 1
                    FOR UPDATE SKIP LOCKED;
                    """
                )
                if row is None:
                    return False
                try:
                    payload = row["payload"]
                    if isinstance(payload, str):
                        payload = json.loads(payload)
                    await self.publisher.publish(row["id"], payload)
                except Exception as exc:
                    # Do not store/log exception messages that may contain a URL
                    # with credentials or the marking codes themselves.
                    error_type = type(exc).__name__
                    delay = min(300, 2 ** min(row["attempts"] + 1, 9))
                    await conn.execute(
                        """
                        UPDATE public.kiz_returns_outbox
                        SET attempts = attempts + 1, last_error = $2,
                            next_attempt_at = clock_timestamp()
                                + $3 * INTERVAL '1 second'
                        WHERE id = $1;
                        """,
                        row["id"], error_type, delay,
                    )
                    logger.warning(
                        "KIZ outbox event_id=%s retry_in=%s error_type=%s",
                        row["id"], delay, error_type,
                    )
                else:
                    await conn.execute(
                        """
                        UPDATE public.kiz_returns_outbox
                        SET sent_at = clock_timestamp(), attempts = attempts + 1,
                            last_error = NULL
                        WHERE id = $1;
                        """,
                        row["id"],
                    )
                return True

    async def run(self) -> None:
        while True:
            try:
                if await self.process_one():
                    continue
            except Exception as exc:
                logger.error("KIZ outbox worker error_type=%s", type(exc).__name__)
            await asyncio.sleep(self.poll_interval)

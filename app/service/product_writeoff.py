import logging
from typing import List
from uuid import UUID, uuid4

from app.database.repositories.product_writeoff import ProductWriteoffRepository
from app.dependencies.config import settings
from app.infrastructure.ONE_C import ONECRouting
from app.models.product_writeoff import (
    ProductWriteoffItem,
    ProductWriteoffOperationsResponse,
    ProductWriteoffResponse,
)

logger = logging.getLogger(__name__)


class ProductWriteoffService:
    def __init__(self, repository: ProductWriteoffRepository):
        self.repository = repository

    async def process(self, data: List[ProductWriteoffItem]) -> ProductWriteoffResponse:
        request_id = uuid4()
        await self.repository.create_pending(request_id, data)
        return await self._send_to_one_c(request_id, data)

    async def retry(self, request_id: UUID) -> ProductWriteoffResponse:
        claim_status, data = await self.repository.claim_failed_for_retry(request_id)
        if claim_status == "not_found":
            return ProductWriteoffResponse(
                status=404,
                message="Операция списания не найдена",
                request_id=request_id,
                item_count=0,
                delivery_status=None,
            )
        if claim_status == "not_retryable":
            return ProductWriteoffResponse(
                status=409,
                message="Повторная отправка разрешена только для операции со статусом failed",
                request_id=request_id,
                item_count=0,
                delivery_status=None,
            )
        return await self._send_to_one_c(request_id, data)

    async def get_operations(
        self,
        product_id: str | None,
        statuses: List[str] | None,
        limit: int,
        offset: int,
    ) -> ProductWriteoffOperationsResponse:
        items, total = await self.repository.get_operations(
            product_id=product_id,
            statuses=statuses,
            limit=limit,
            offset=offset,
        )
        return ProductWriteoffOperationsResponse(
            items=items,
            total=total,
            limit=limit,
            offset=offset,
        )

    async def _send_to_one_c(
        self,
        request_id: UUID,
        data: List[ProductWriteoffItem],
    ) -> ProductWriteoffResponse:
        try:
            one_c = ONECRouting(
                base_url=settings.ONE_C_BASE_URL,
                login=settings.ONE_C_LOGIN,
                password=settings.ONE_C_PASSWORD,
            )
            response = await one_c.product_writeoff(data)
        except Exception as exc:
            error = f"{type(exc).__name__}: {exc}"
            await self.repository.mark_delivery_result(
                request_id, "failed", None, None, error
            )
            logger.exception(
                "event=product_writeoff_one_c_transport_error request_id=%s",
                request_id,
            )
            return ProductWriteoffResponse(
                status=502,
                message="Не удалось передать списание в 1С",
                request_id=request_id,
                item_count=len(data),
                delivery_status="failed",
                details=error,
            )

        response_body = response.body[:10000]
        if not 200 <= response.status < 300:
            await self.repository.mark_delivery_result(
                request_id, "failed", response.status, response_body, None
            )
            return ProductWriteoffResponse(
                status=502,
                message="1С отклонила списание",
                request_id=request_id,
                item_count=len(data),
                delivery_status="failed",
                details=f"1С вернула HTTP {response.status}: {response_body}",
            )

        await self.repository.mark_delivery_result(
            request_id, "sent", response.status, response_body, None
        )
        return ProductWriteoffResponse(
            status=201,
            message="Списание сохранено и передано в 1С",
            request_id=request_id,
            item_count=len(data),
            delivery_status="sent",
        )

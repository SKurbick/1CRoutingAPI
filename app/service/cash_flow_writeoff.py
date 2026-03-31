import logging
from typing import List

from app.database.repositories.cash_flow_writeoff import CashFlowWriteoffRepository
from app.models.cash_flow_writeoff import CashFlowWriteoff, CashFlowWriteoffResponse

logger = logging.getLogger(__name__)


class CashFlowWriteoffService:
    def __init__(self, repo: CashFlowWriteoffRepository):
        self.repo = repo

    async def process(self, data: List[CashFlowWriteoff]) -> CashFlowWriteoffResponse:
        try:
            await self.repo.update_data(data)
            return CashFlowWriteoffResponse(
                status=200,
                message="OK",
                details=f"{len(data)} records processed",
            )
        except Exception as e:
            logger.error("CashFlowWriteoffService.process error: %s", e, exc_info=True)
            return CashFlowWriteoffResponse(
                status=500,
                message="Internal error",
                details=str(e),
            )

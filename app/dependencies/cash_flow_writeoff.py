from starlette.requests import Request

from app.database.repositories.cash_flow_writeoff import CashFlowWriteoffRepository
from app.service.cash_flow_writeoff import CashFlowWriteoffService


async def get_cash_flow_writeoff_service(request: Request) -> CashFlowWriteoffService:
    pool = request.app.state.pool
    repo = CashFlowWriteoffRepository(pool)
    return CashFlowWriteoffService(repo)

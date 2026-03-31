from typing import List

from fastapi import APIRouter, Depends, HTTPException

from app.dependencies.cash_flow_writeoff import get_cash_flow_writeoff_service
from app.models.cash_flow_writeoff import CashFlowWriteoff, CashFlowWriteoffResponse
from app.service.cash_flow_writeoff import CashFlowWriteoffService

router = APIRouter(prefix="/cash_flow_writeoff", tags=["1C Cash Flow Writeoff"])


@router.post(
    "/update",
    response_model=CashFlowWriteoffResponse,
    summary="Приём списаний ДС из 1С",
    description=(
        "Принимает массив документов списания денежных средств из 1С и сохраняет их в БД.\n\n"
        "Данные поступают из 1С в формате JSON-массива объектов `CashFlowWriteoff`.\n\n"
        "Каждый документ идентифицируется по полю `guid`. "
        "При повторной отправке существующего `guid` запись обновляется (upsert).\n\n"
        "Поле `expense_item` необязательно — если не передано, в БД записывается `NULL`."
    ),
)
async def receive_writeoff_data(
    data: List[CashFlowWriteoff],
    service: CashFlowWriteoffService = Depends(get_cash_flow_writeoff_service),
) -> CashFlowWriteoffResponse:
    result = await service.process(data)

    if result.status >= 400:
        raise HTTPException(
            status_code=result.status,
            detail={
                "message": result.message,
                "details": result.details,
            },
        )

    return result

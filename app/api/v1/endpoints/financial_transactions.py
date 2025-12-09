from typing import List

from fastapi import APIRouter, Depends, status, Body, HTTPException
from app.models.financial_transactions import IncomeOnBankAccountUpdate, FinancialTransactionsResponse, example_income_on_bank_account_data, \
    WriteOffOfNonCashFunds, write_off_of_non_cash_funds_example, CashDisbursementOrder, cash_disbursement_order_example
from app.service.financial_transactions import IncomeOnBankAccountService
from app.dependencies import get_financial_transactions_service

# router = APIRouter(prefix="/income_on_bank_account", dependencies=[Depends(verify_service_token)])


router = APIRouter(prefix="/financial_transactions", tags=["Финансовые операции в 1С"])


@router.post("/income_on_bank_account", response_model=FinancialTransactionsResponse, status_code=status.HTTP_201_CREATED)
async def income_on_bank_account(
        data: List[IncomeOnBankAccountUpdate] = Body(example=example_income_on_bank_account_data),
        service: IncomeOnBankAccountService = Depends(get_financial_transactions_service)
):
    result = await service.add_income_on_bank_account(data)

    if result.status >= 400:
        raise HTTPException(
            status_code=result.status,
            detail={
                "message": result.message,
                "details": result.details
            }
        )

    return result



@router.post("/write_off_of_non_cash_funds", response_model=FinancialTransactionsResponse, status_code=status.HTTP_201_CREATED)
async def write_off_of_non_cash_funds(
        data: List[WriteOffOfNonCashFunds] = Body(example=write_off_of_non_cash_funds_example),
        service: IncomeOnBankAccountService = Depends(get_financial_transactions_service)
):
    result = await service.add_data_by_write_off_of_non_cash_funds(data)

    if result.status >= 400:
        raise HTTPException(
            status_code=result.status,
            detail={
                "message": result.message,
                "details": result.details
            }
        )

    return result


@router.post("/cash_disbursement_order", response_model=FinancialTransactionsResponse, status_code=status.HTTP_201_CREATED)
async def cash_disbursement_order(
        data: List[CashDisbursementOrder] = Body(example=cash_disbursement_order_example),
        service: IncomeOnBankAccountService = Depends(get_financial_transactions_service)
):
    result = await service.add_data_cash_disbursement_order(data)

    if result.status >= 400:
        raise HTTPException(
            status_code=result.status,
            detail={
                "message": result.message,
                "details": result.details
            }
        )

    return result
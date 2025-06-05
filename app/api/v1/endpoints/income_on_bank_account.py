from typing import List

from fastapi import APIRouter, Depends, status, Body, HTTPException
from app.models.income_on_bank_account import IncomeOnBankAccountUpdate, IncomeOnBankAccountResponse, example_income_on_bank_account_data
from app.service.income_on_bank_account import IncomeOnBankAccountService
from app.dependencies import get_income_on_bank_account_service
from app.dependencies.security import verify_service_token

# router = APIRouter(prefix="/income_on_bank_account", dependencies=[Depends(verify_service_token)])


router = APIRouter(prefix="/income_on_bank_account", tags=["Поступления на РС продавца"])


@router.post("/update", response_model=IncomeOnBankAccountResponse, status_code=status.HTTP_201_CREATED)
async def create_data(
        data: List[IncomeOnBankAccountUpdate] = Body(example=example_income_on_bank_account_data),
        service: IncomeOnBankAccountService = Depends(get_income_on_bank_account_service)
):
    result = await service.create_data(data)

    if result.status >= 400:
        raise HTTPException(
            status_code=result.status,
            detail={
                "message": result.message,
                "details": result.details
            }
        )

    return result

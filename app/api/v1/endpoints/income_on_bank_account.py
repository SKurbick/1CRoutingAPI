from typing import List

from fastapi import APIRouter, Depends, status, Body
from app.models.income_on_bank_account import IncomeOnBankAccountUpdate, IncomeOnBankAccountResponse, example_income_on_bank_account_data
from app.service.income_on_bank_account import IncomeOnBankAccountService
from app.dependencies import get_income_on_bank_account_service

# router = APIRouter(prefix="receipt_of_goods",dependencies=[Depends(verify_service_token)])

router = APIRouter(prefix="/income_on_bank_account")


@router.post("/update", response_model=IncomeOnBankAccountResponse, status_code=status.HTTP_201_CREATED)
async def create_data(
        data: List[IncomeOnBankAccountUpdate] = Body(example=example_income_on_bank_account_data),
        service: IncomeOnBankAccountService = Depends(get_income_on_bank_account_service)
):
    try:
        await service.create_data(data)
        return {"status": 201, "message": "Успешно"}
    except Exception as e:
        pass

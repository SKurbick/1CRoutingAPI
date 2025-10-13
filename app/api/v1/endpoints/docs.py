import datetime
from typing import List, Dict, Union

from fastapi import APIRouter, Depends, status, Body, HTTPException, Query, Request
from app.limiter import limiter

from app.models.docs import DocsData, docs_data_response_example
from app.service.docs import DocsService
from app.dependencies import get_docs_service


router = APIRouter(prefix="/docs", tags=["Документы"])
#responses={200: docs_data_response_example}
@router.get("/get_docs", response_model=List[Dict] , status_code=status.HTTP_200_OK
            )
@limiter.limit("0.2/second")
async def get_docs(
        request: Request,  # Добавляем request первым параметром
        account_name: str ,
        date_from: datetime.date = None,
        date_to: datetime.date = None,
        service: DocsService = Depends(get_docs_service)
):
    print(account_name)
    # if date_from is None or date_to is None:
    #     raise HTTPException(
    #         status_code=status.HTTP_400_BAD_REQUEST,
    #         detail="date_from and date_to are required."
    #     )

    return await service.get_docs(account_name=account_name, date_from=date_from, date_to=date_to)

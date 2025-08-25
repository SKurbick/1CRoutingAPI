import datetime
from typing import List

from fastapi import APIRouter, Depends, status, Body, HTTPException, Query
from app.models.docs import DocsData, docs_data_response_example
from app.service.docs import DocsService
from app.dependencies import get_docs_service

router = APIRouter(prefix="/docs", tags=["Документы"])
#responses={200: docs_data_response_example}
@router.get("/get_docs", response_model=List[DocsData] , status_code=status.HTTP_200_OK
            )
async def get_docs(
        date_from: datetime.date = None,
        date_to: datetime.date = None,
        service: DocsService = Depends(get_docs_service)
):
    # if date_from is None or date_to is None:
    #     raise HTTPException(
    #         status_code=status.HTTP_400_BAD_REQUEST,
    #         detail="date_from and date_to are required."
    #     )

    return await service.get_docs(date_from=date_from, date_to=date_to)

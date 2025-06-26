
from fastapi import APIRouter, Depends, status, Body
from app.models.local_barcode_generation import  example_goods_acceptance_certificate , GoodsAcceptanceCertificateCreate
from app.service.local_barcode_generation import LocalBarcodeGenerationService
from app.dependencies import local_barcode_generation_service
from fastapi.responses import StreamingResponse

from fastapi import BackgroundTasks
import gc
from io import BytesIO


router = APIRouter(prefix="/local_barcode_generation", tags=["Приемка товара и генерация штрихкода"])


@router.post("/update", status_code=status.HTTP_201_CREATED)
async def create_data(
        background_tasks: BackgroundTasks,
    data: GoodsAcceptanceCertificateCreate = Body(example=example_goods_acceptance_certificate),
    service: LocalBarcodeGenerationService = Depends(local_barcode_generation_service)
):
    img_buffer = await service.create_data(data)

    # Функция для очистки памяти после отправки
    def cleanup(buffer: BytesIO):
        buffer.close()
        gc.collect()

    background_tasks.add_task(cleanup, img_buffer)

    return StreamingResponse(
        img_buffer,
        media_type="image/png",
        headers={"Content-Disposition": "attachment; filename=barcodes.png"},
        status_code=201
    )


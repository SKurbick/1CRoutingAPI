from pydantic import BaseModel, Field


class BoxSize(BaseModel):
    "Размер короба."
    length: int = Field(..., gt=0, description="Длина, см")
    width: int = Field(..., gt=0, description="Ширина, см")
    height: int = Field(..., gt=0, description="Высота, см")


class BoxDataRequest(BaseModel):
    """Данные для одного короба."""
    name: str = Field(..., description="Название", max_length=128)
    article: str = Field(..., description="Артикул", max_length=16)
    color: str = Field(..., description="Цвет", max_length=64)
    gross_weight: float = Field(..., description="Вес брутто, кг", gt=0)
    net_weight: float = Field(..., description="Вес нетто, кг", gt=0)
    box_size: BoxSize = Field(..., description="Размер короба, см")
    produced_in: str = Field(..., description="Произведено в", max_length=64)
    proforma_number: str = Field(..., description="Номер проформы", max_length=128)
    items_per_box: int = Field(..., description="Количество в коробе", gt=0)
    total_boxes: int = Field(..., description="Количество коробов", gt=0, le=500)
    name_en: str = Field(..., description="Название, en", max_length=128)
    color_en: str = Field(..., description="Цвет, en", max_length=64)
    produced_in_en: str = Field(..., description="Произведено в, en", max_length=64)


class QRCodeData(BaseModel):
    """Данные для qr-кода."""
    article: str = Field(..., description="Артикул товара")
    proforma_number: str = Field(..., description="Номер проформы")
    items_per_box: int = Field(..., description="Количество в коробе")
    box_number: int = Field(..., description="Номер короба")
    total_boxes: int = Field(..., description="Количество коробов")


class StickerData(QRCodeData):
    """Данные для стикера."""
    name: str = Field(..., description="Название")
    color: str = Field(..., description="Цвет")
    produced_in: str = Field(..., description="Произведено в")
    gross_weight: float = Field(..., description="Вес брутто, кг")
    net_weight: float = Field(..., description="Вес нетто, кг")
    box_size: BoxSize = Field(..., description="Размер короба, см")
    name_en: str = Field(..., description="Название, en")
    color_en: str = Field(..., description="Цвет, en")
    produced_in_en: str = Field(..., description="Произведено в, en")

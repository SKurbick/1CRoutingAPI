from enum import Enum

from pydantic import BaseModel, Field


class StickerDocumentType(str, Enum):
    TRANSPORT = "TRANSPORT"
    INDIVIDUAL = "INDIVIDUAL"


class CertificationType(str, Enum):
    """Тип сертификата или знака соответствия."""
    EAC = "ЕАС"       # Евразийское соответствие
    STR = "СТР"       # Свидетельство о госрегистрации
    NONE = "NONE"     # Отсутствует / Не требуется


class BoxSize(BaseModel):
    "Размер короба."
    length: float = Field(..., gt=0, description="Длина, см")
    width: float = Field(..., gt=0, description="Ширина, см")
    height: float = Field(..., gt=0, description="Высота, см")


class BoxDataRequest(BaseModel):
    """Данные для одного короба."""
    name: str = Field(..., description="Название", max_length=128)
    article: str = Field(..., description="Артикул", max_length=16)
    color: str | None = Field(None, description="Цвет", max_length=64)
    gross_weight: float = Field(..., description="Вес брутто, кг", gt=0)
    net_weight: float = Field(..., description="Вес нетто, кг", gt=0)
    box_size: BoxSize = Field(..., description="Размер короба, см")
    produced_in: str | None = Field(None, description="Произведено в", max_length=64)
    proforma_number: str | None = Field(None, description="Номер проформы", max_length=128)
    items_per_box: int | None = Field(None, description="Количество в коробе", gt=0)
    total_boxes: int = Field(..., description="Количество коробов", gt=0, le=500)
    name_en: str | None = Field(None, description="Название, en", max_length=128)
    color_en: str | None = Field(None, description="Цвет, en", max_length=64)
    produced_in_en: str | None = Field(None, description="Произведено в, en", max_length=64)
    certification_type: CertificationType = Field(
        default=CertificationType.NONE, 
        description="Тип сертификата соответствия (ЕАС, СТР или отсутствует)"
    )


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
    certification_type: CertificationType = Field(
        default=CertificationType.NONE, 
        description="Тип сертификата соответствия (ЕАС, СТР или отсутствует)"
    )


class BoxStickerTemplate(BaseModel):
    """Шаблон стикера для одного короба."""
    article: str | None = Field(None, description="Артикул")
    name: str | None = Field(None, description="Название")
    name_en: str | None = Field(None, description="Название, en")
    color: str | None = Field(None, description="Цвет")
    color_en: str | None = Field(None, description="Цвет, en")
    gross_weight: float | None = Field(None, description="Вес брутто, кг")
    net_weight: float | None = Field(None, description="Вес нетто, кг")
    box_length: float | None = Field(None, gt=0, description="Длина, см")
    box_width: float | None = Field(None, gt=0, description="Ширина, см")
    box_height: float | None = Field(None, gt=0, description="Высота, см")
    items_per_box: int | None = Field(None, description="Количество в коробе")
    total_boxes: int | None = Field(None, description="Количество коробов")
    produced_in: str | None = Field(None, description="Произведено в")
    produced_in_en: str | None = Field(None, description="Произведено в, en")
    proforma_number: str | None = Field(None, description="Номер проформы")
    certification_type: CertificationType = Field(
        default=CertificationType.NONE, 
        description="Тип сертификата соответствия (ЕАС, СТР или отсутствует)"
    )


class BoxStickerTemplateShort(BaseModel):
    """Шаблон стикера с минимальной информацией."""
    article: str | None = Field(None, description="Артикул")
    name: str | None = Field(None, description="Название")



class StickerProductData(BaseModel):
    product_id: str = Field(None, description="Артикул")
    name: str = Field(None, description="Название")
    color: str | None = Field(None, description="Цвет")
    material: str | None = Field(None, description="Материал")
    gross_weight: float | None= Field(None, description="Вес брутто, кг")
    net_weight: float | None = Field(None, description="Вес нетто, кг")
    box_size: BoxSize | None = None
    produced_in: str | None = Field(None, description="Произведено в")
    certification_type: CertificationType = Field(
        default=CertificationType.NONE, 
        description="Тип сертификата соответствия (ЕАС, СТР или отсутствует)"
    )


class StickerLocalisationData(BaseModel):
    """Договорились не хранить русскую версию поля. Локализация!=перевод"""
    product_id: str
    field_name: str
    lang: str
    translation: str


class StickerUserTemplateData(BaseModel):
    product_id: str
    document_type: StickerDocumentType
    proforma_number: str | None = None
    items_per_box: int | None = None
    total_boxes: int | None = None
    produced_in: int | None = None
    importer_id: int | None = None

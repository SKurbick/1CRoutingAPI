from enum import Enum
from uuid import UUID

from pydantic import BaseModel, Field


class StickerType(str, Enum):
    TRANSPORT = "TRANSPORT"
    INDIVIDUAL = "INDIVIDUAL"


class CertificationType(str, Enum):
    """Тип сертификата или знака соответствия."""
    EAC = "ЕАС"       # Евразийское соответствие
    STR = "СТР"       # Свидетельство о госрегистрации
    NONE = "NONE"     # Отсутствует / Не требуется


class BoxSize(BaseModel):
    "Размер короба."
    box_length: float = Field(..., description="Длина, см")
    box_width: float = Field(..., description="Ширина, см")
    box_height: float = Field(..., description="Высота, см")


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
    """Данные товара (временно тянутся из гугл дока)"""
    product_id: str = Field(..., description="Артикул")
    name: str = Field(..., description="Название")
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
    translation: str | None = None


class StickerUserTemplateData(BaseModel):
    """Пользовательские данные шаблона"""
    product_id: str
    sticker_type: StickerType
    proforma_number: str | None = None
    items_per_box: int | None = None
    total_boxes: int | None = None
    produced_in: str | None = None
    gross_weight: float | None = None
    net_weight: float | None = None
    box_length: float | None = None
    box_width: float | None = None
    box_height: float | None = None
    certification_type: CertificationType | None = None


class BoxStickerTemplateView(BaseModel): #TODO: сделать обобщающий класс для стикеров на коробки и индивидуальных с общими полями для типизации в async def save_localisations
    """Форма для агрегации данных о товаре, сохраненных данных, дефолтных данных и ввода пользователя"""
    product_id: str
    name: str | None = None
    name_en: str | None = None
    color: str | None = None
    color_en: str | None = None
    gross_weight: float
    net_weight: float | None = None # TODO: в таблице в БД нет net_weight
    box_size: BoxSize
    items_per_box: int | None = None
    total_boxes: int | None = None
    produced_in: str | None = None
    produced_in_en: str | None = None
    proforma_number: str | None = None
    certification_type: CertificationType = CertificationType.NONE


class GenerationStatus(str, Enum):
    """
    Статус задачи.
    """
    PENDING = "pending"  # Запрос принят, задача ждёт в очереди
    PROCESSING = "processing"  # Воркер взял задачу, идёт генерация
    COMPLETED = "completed"  # Документ сохранён, ссылка готова
    FAILED = "failed"  # Ошибка генерации (retry исчерпаны или неустранимая)
    CANCELLED = "cancelled"  # Задача отменена пользователем или системой

class StickerGenerationTaskView(BaseModel):
    id: int
    product_id: str
    sticker_type: StickerType
    template_hash: str
    generation_status: GenerationStatus
    task_uuid: UUID
    document_path: str | None = None
    error_message: str | None = None


class StickerGenerationTaskResult(BaseModel):
    task_id: int
    generation_status: GenerationStatus
    document_path: str | None = None
    task_uuid: UUID|str
    error_message: str | None = None


class StickerGenerationTaskResultResponse(BaseModel):
    task_id: int
    product_id: str
    generation_status: GenerationStatus
    error_message: str | None = None
    document_url: str | None = None


class BoxStickerTemplateViewShort(BaseModel):
    """Шаблон стикера с минимальной информацией."""
    product_id: str | None = Field(None, description="Артикул")
    name: str | None = Field(None, description="Название")

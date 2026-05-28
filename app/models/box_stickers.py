from datetime import datetime
from enum import Enum
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, Field


class StickerType(str, Enum):
    TRANSPORT = "TRANSPORT"
    INDIVIDUAL = "INDIVIDUAL"


class CertificationType(str, Enum):
    """Тип сертификата или знака соответствия."""

    EAC = "ЕАС"  # Евразийское соответствие
    STR = "СТР"  # Свидетельство о госрегистрации
    NONE = "NONE"  # Отсутствует / Не требуется


class BoxSize(BaseModel):
    "Размер короба."

    box_length: float = Field(..., description="Длина, см")
    box_width: float = Field(..., description="Ширина, см")
    box_height: float = Field(..., description="Высота, см")


# class BoxStickerTemplateShort(BaseModel):
#     """Шаблон стикера с минимальной информацией."""
#     article: str | None = Field(None, description="Артикул")
#     name: str | None = Field(None, description="Название")


class StickerProductData(BaseModel):
    """Данные товара (временно тянутся из гугл дока)"""

    product_id: str = Field(..., description="Артикул")
    name: str = Field(..., description="Название")
    color: str | None = Field(None, description="Цвет")
    material: str | None = Field(None, description="Материал")
    gross_weight: float | None = Field(None, description="Вес брутто, кг")
    net_weight: float | None = Field(None, description="Вес нетто, кг")
    box_size: BoxSize | None = None
    produced_in: str | None = Field(None, description="Произведено в")
    items_per_box: int | None = None
    certification_type: CertificationType = Field(
        default=CertificationType.NONE,
        description="Тип сертификата соответствия (ЕАС, СТР или отсутствует)",
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
    # proforma_number: str | None = None
    items_per_box: int | None = None
    total_boxes: int | None = None
    produced_in: str | None = None
    gross_weight: float | None = None
    net_weight: float | None = None
    box_length: float | None = None
    box_width: float | None = None
    box_height: float | None = None
    certification_type: CertificationType | None = None


class BoxStickerTemplateView(BaseModel):
    """Форма для агрегации данных о товаре, сохраненных данных, дефолтных данных и ввода пользователя"""

    product_id: str
    name: str
    name_en: str
    color: str | None = None
    color_en: str | None = None
    gross_weight: float
    net_weight: float | None = None  # TODO: в таблице в БД нет net_weight
    box_size: BoxSize
    items_per_box: int | None = None
    total_boxes: int | None = None
    produced_in: str | None = None
    produced_in_en: str | None = None
    proforma_number: str | None = None
    certification_type: CertificationType = CertificationType.NONE
    limit: int | None = 0
    offset: int | None = 0


class BoxStickerTemplateViewRequest(BaseModel):
    """Форма для агрегации данных о товаре, сохраненных данных, дефолтных данных и ввода пользователя"""

    product_id: str
    name: str
    name_en: str
    color: str | None = None
    color_en: str | None = None
    gross_weight: float
    net_weight: float | None = None  # TODO: в таблице в БД нет net_weight
    box_size: BoxSize
    items_per_box: int | None = None
    # total_boxes: int | None = None
    produced_in: str | None = None
    produced_in_en: str | None = None
    proforma_number: str | None = None
    certification_type: CertificationType = CertificationType.NONE
    limit: int | None = 0
    # offset: int | None = 0


class GenerationStatus(str, Enum):
    """
    Статус задачи.
    """

    INITIATED = "initiated"  # Запрос создан и направлен на обработку
    PENDING = "pending"  # Запрос принят, задача ждёт в очереди
    PROCESSING = "processing"  # Воркер взял задачу, идёт генерация
    COMPLETED = "completed"  # Документ сохранён, ссылка готова
    FAILED = "failed"  # Ошибка генерации (retry исчерпаны или неустранимая)
    CANCELLED = "cancelled"  # Задача отменена пользователем или системой


class StickerGenerationTaskView(BaseModel):
    """Схема для работы с таблицей sticker_generation_tasks"""

    id: int
    product_id: str
    sticker_type: StickerType
    template_hash: str
    generation_status: GenerationStatus
    task_uuid: UUID
    document_path: str | None = None
    error_message: str | None = None
    created_at: datetime
    updated_at: datetime


class StickerGenerationTaskResult(BaseModel):
    task_id: int
    generation_status: GenerationStatus
    storage_key: str | None = None
    task_uuid: UUID | str
    error_message: str | None = None


class StickerGenerationTaskResultResponse(BaseModel):
    """Схема ответа сервиса в эндпоинтах"""

    task_id: int
    product_id: str
    generation_status: GenerationStatus
    error_message: str | None = None
    document_url: str | None = None


class StickerGenerationTaskInfo(BaseModel):
    """
    Информация о задаче по генерации стикеров
    """

    task_id: int = Field(..., description="ID задачи на генерацию.")
    product_id: str = Field(..., description="Артикул товара")
    generation_status: GenerationStatus = Field(..., description="Статус задачи")
    error_message: str | None = Field(
        None, description="Сообщение об ошибках во время выполнения задачи."
    )
    sticker_type: StickerType = Field(..., description="Тип стикеров в готовом файле")
    created_at: datetime = Field(..., description="Дата создания задачи")
    updated_at: datetime = Field(..., description="Дата обновления информации о задаче")


class StickerGenerationTaskEvent(str, Enum):
    """
    Тип события задачи генерации стикеров.
    """

    UPDATE_STATUS = "update_status"


class StickerGenerationTaskNotice(BaseModel):
    """
    Уведомление по задаче генерации стикеров.
    """

    event: StickerGenerationTaskEvent = Field(
        ..., description="Тип события в уведомлении."
    )
    task_data: StickerGenerationTaskInfo = Field(..., description="Информация о задаче")


class StickerTemplateViewShort(BaseModel):
    """Шаблон стикера с минимальной информацией."""

    product_id: str | None = Field(None, description="Артикул")
    name: str | None = Field(None, description="Название")


class ManufacturerView(BaseModel):
    """Схема данных по производителям"""

    id: int
    name: str


class ImporterView(BaseModel):
    """Схема данных по импортерам"""

    id: int
    name: str


# Individual stickers


class IndividualStickerTemplateView(BaseModel):
    product_id: str = Field(..., description="Артикул")
    name: str = Field(..., description="Название")
    color: str | None = Field(None, description="Цвет")
    material: str | None = Field(None, description="Материал")
    manufacturer: str = "NINGBO GENERAL UNION CO., LTD"
    importer_details: str = "ООО СТАРТ"
    produced_in: str = "Китай"
    production_date: str = Field(
        default_factory=lambda: datetime.now().strftime("%Y-%m-%d")
    )  # TODO: оставить как поле только в бд?
    certification_type: CertificationType = CertificationType.NONE
    quantity: int


class StickerIndividualUserData(BaseModel):
    """Модель пользовательских данных для индивидуального стикера"""

    product_id: str = Field(..., description="Артикул")
    name: str = Field(..., description="Название")
    manufacturer_id: int | None = Field(None, description="Изготовитель")
    color: str | None = Field(None, description="Цвет")
    material: str | None = Field(None, description="Материал")
    importer_details: str = Field(..., description="Импортер")
    produced_in: str = Field(default="Китай", description="Страна производства")
    certification_type: CertificationType = Field(
        default=CertificationType.NONE,
        description="Тип сертификации (ЕАС, СТР или отсутствует)",
    )
    production_date: datetime = Field(
        default_factory=datetime.now, description="Дата производства"
    )

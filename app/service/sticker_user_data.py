

from app.database.repositories.sticker_user_data import StickerUserDataRepository
from app.models.box_stickers import BoxStickerTemplateView, StickerType, StickerUserTemplateData


class StickerUserDataService:
    def __init__(self, repo: StickerUserDataRepository):
        self.repo = repo

    async def save_box_sticker_user_data(self, template_data: BoxStickerTemplateView) -> None:
        """Сохраняет данные по стикеру для коробки в БД"""
        data_to_save = StickerUserTemplateData(
            product_id=template_data.product_id,
            sticker_type=StickerType.TRANSPORT,
            proforma_number=template_data.proforma_number,
            items_per_box=template_data.items_per_box,
            total_boxes=template_data.total_boxes,
            produced_in=template_data.produced_in
        )
        await self.repo.upsert(data_to_save)


    async def save_individual_user_data(self, template_data) -> None: #TODO: template_data: IndividualStickerTemplateView
        """Сохраняет данные по индивидуальному стикеру в БД"""
        data_to_save = StickerUserTemplateData(
            product_id=template_data.product_id,
            sticker_type=StickerType.INDIVIDUAL,
            produced_in=template_data.produced_in,
        )
        await self.repo.upsert(data_to_save)
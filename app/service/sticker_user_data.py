

from app.database.repositories.manufacturers import ManufacturerRepository
from app.database.repositories.sticker_individual_user_data import IndividualUserDataRepository
from app.database.repositories.sticker_user_data import StickerUserDataRepository
from app.models.box_stickers import BoxStickerTemplateView, IndividualStickerTemplateView, StickerIndividualUserData, StickerType, StickerUserTemplateData


class StickerUserDataService:
    def __init__(self, 
        box_repo: StickerUserDataRepository,
        individual_repo: IndividualUserDataRepository,
        manufacturer_repo: ManufacturerRepository
    ):
        self.box_repo = box_repo
        self.individual_repo = individual_repo
        self.manufacturer_repo = manufacturer_repo

    async def save_box_sticker_user_data(self, template_data: BoxStickerTemplateView) -> None:
        """Сохраняет данные по стикеру для коробки в БД"""
        user_data = StickerUserTemplateData(
            product_id=template_data.product_id,
            sticker_type=StickerType.TRANSPORT,
            proforma_number=template_data.proforma_number,
            items_per_box=template_data.items_per_box,
            total_boxes=template_data.total_boxes,
            gross_weight=template_data.gross_weight,
            net_weight=template_data.net_weight,
            box_length=template_data.box_size.box_length,
            box_width=template_data.box_size.box_width,
            box_height=template_data.box_size.box_height,
            produced_in=template_data.produced_in,
            certification_type=template_data.certification_type
        )
        await self.box_repo.upsert(user_data)


    # async def save_individual_user_data(self, template_data) -> None: #TODO: template_data: IndividualStickerTemplateView
    #     """Сохраняет данные по индивидуальному стикеру в БД"""
    #     data_to_save = StickerUserTemplateData(
    #         product_id=template_data.product_id,
    #         sticker_type=StickerType.INDIVIDUAL,
    #         produced_in=template_data.produced_in,
    #     )
    #     await self.repo.upsert(data_to_save)


    async def save_unit_sticker_user_data(self, template_data: IndividualStickerTemplateView) -> None:
        """Сохранить данные по стикеру для индивидуального стикера в бд"""


        manufacturer_id = await self.manufacturer_repo.get_or_create(template_data.manufacturer)

        user_data = StickerIndividualUserData(
            product_id=template_data.product_id,
            name=template_data.name,
            manufacturer_id=manufacturer_id,
            color = template_data.color,
            material = template_data.material,
            importer_details = template_data.importer_details,
            produced_in = template_data.produced_in,
            certification_type = template_data.certification_type,
            production_date = template_data.production_date #TODO: не уверен, что поле тут нужно. Оно должно быть сегодняшним для любого стикера. Но мб так можно будет не генерировать новый стикер.
        )

        await self.individual_repo.upsert(user_data)



from app.models.box_stickers import BoxStickerTemplateView
from app.service.localisation import LocalisationService
from app.service.sticker_user_data import StickerUserDataService


class StickerTemplateSaveService:
    def __init__(self, user_data_service: StickerUserDataService, localisation_service: LocalisationService,
    ):
        self.user_data_service = user_data_service
        self.localisation_service = localisation_service


    async def save_box_sticker_template(self, template_data: BoxStickerTemplateView) -> BoxStickerTemplateView:
        await self.user_data_service.save_box_sticker_user_data(template_data)
        await self.localisation_service.save_localisations(template_data)
        return template_data
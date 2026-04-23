



from app.database.repositories.localisation import LocalisationRepository
from app.models.box_stickers import BoxStickerTemplateView, StickerLocalisationData


class LocalisationService:
    def __init__(self, repo: LocalisationRepository):
        self.repo = repo

    async def save_localisations(self, template_data) -> None:#template_data: BoxStickerTemplateView #TODO: сделать универсальный метод для всех видо стикеров(сохранять локлизацию для товара, а не для стикера)
        items: list[StickerLocalisationData] = []

        if template_data.name_en: # при удалении данных в шаблоне старый перевод не удалится в бд
            items.append(
                StickerLocalisationData(
                    product_id=template_data.product_id,
                    field_name="name",
                    lang="en",
                    translation=template_data.name_en,
                )
            )

        if template_data.color_en: # при удалении данных в шаблоне старый перевод не удалится в бд
            items.append(
                StickerLocalisationData(
                    product_id=template_data.product_id,
                    field_name="color",
                    lang="en",
                    translation=template_data.color_en,
                )
            )

        if template_data.produced_in_en: # при удалении данных в шаблоне старый перевод не удалится в бд
            items.append(
                StickerLocalisationData(
                    product_id=template_data.product_id,
                    field_name="produced_in",
                    lang="en",
                    translation=template_data.produced_in_en,
                )
            )

        await self.repo.upsert_many(items)

    async def save_individual_localisations(self, template_data) -> None:
        pass
  
from app.broker.publisher import publish_box_sticker_generation_task


class StickerGenerationPublisher:
    async def publish_generation_task(self, payload: dict) -> None:
        await publish_box_sticker_generation_task(payload)
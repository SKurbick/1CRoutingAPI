from app.broker.publisher import publish_box_sticker_generation_task, publish_individual_sticker_generation_task


class StickerGenerationPublisher:
    async def publish_generation_task(self, payload: dict) -> None:
        print("----publisher------"*4)
        print(payload)
        print("----publisher------"*4)
        await publish_box_sticker_generation_task(payload)

    async def publish_generation_task_for_individual(self, payload: dict) -> None:
        print("----publisher------"*4)
        print(payload)
        print("----publisher------"*4)
        await publish_individual_sticker_generation_task(payload)
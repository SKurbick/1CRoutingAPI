from math import floor
from typing import Optional

from app.database.repositories.containers import ContainerRepository
from app.models.containers import Container, ContainerCreate, ContainerUpdate


class ContainerService:
    def __init__(self, repository: ContainerRepository):
        self.repository = repository

    @staticmethod
    def calculate_boxes_per_pallet(
        length: float,
        width: float,
        height: float,
        pallet_length: float = 80.0,
        pallet_width: float = 120.0,
        pallet_max_height: float = 180.0,
        pallet_height: float = 14.5  # высота самой паллеты
    ) -> int:
        """Рассчитать, сколько коробок помещается на паллете."""
        if length <= 0 or width <= 0 or height <= 0:
            return 0

        # Доступная высота для коробок
        available_height = pallet_max_height - pallet_height

        boxes_by_length = floor(pallet_length / length) if length > 0 else 0
        boxes_by_width = floor(pallet_width / width) if width > 0 else 0
        boxes_by_height = floor(available_height / height) if height > 0 else 0

        if boxes_by_length == 0 or boxes_by_width == 0 or boxes_by_height == 0:
            return 0

        return boxes_by_length * boxes_by_width * boxes_by_height

    async def get_containers(
        self,
        is_active: Optional[bool] = True
    ) -> list[Container]:
        """Получить все контейнеры."""
        return await self.repository.get_all(is_active)

    async def get_container(self, container_id: int) -> Optional[Container]:
        """Получить контейнер по id."""
        return await self.repository.get_by_id(container_id)

    async def create_container(self, container: ContainerCreate) -> Container:
        """Создать новый контейнер."""
        if container.boxes_per_pallet is None:
            container.boxes_per_pallet = self.calculate_boxes_per_pallet(
                length=container.length,
                width=container.width,
                height=container.height,
            )

            return await self.repository.create(container=container)

        return await self.repository.create(container)

    async def update_container(
        self, 
        container_id: int, 
        container: ContainerUpdate
    ) -> Optional[Container]:
        """Обновить информацию о контейнере."""
        current_container = await self.get_container(container_id)

        if not current_container:
            return None

        container_dict = container.model_dump(exclude_unset=True)
        dimensions_changed = False

        if "length" in container_dict and container_dict["length"] != current_container.length:
            dimensions_changed = True
        if "width" in container_dict and container_dict["width"] != current_container.width:
            dimensions_changed = True
        if "height" in container_dict and container_dict["height"] != current_container.height:
            dimensions_changed = True

        new_length = container_dict.get("length", current_container.length)
        new_width = container_dict.get("width", current_container.width)
        new_height = container_dict.get("height", current_container.height)

        boxes_per_pallet_provided = "boxes_per_pallet" in container_dict

        calculate_boxes = False
        if not boxes_per_pallet_provided and current_container.boxes_per_pallet is None:
            calculate_boxes = True
        elif not boxes_per_pallet_provided:
            if dimensions_changed:
                calculate_boxes = True
            else:
                container_dict["boxes_per_pallet"] = current_container.boxes_per_pallet
        else:
            new_boxes = container_dict["boxes_per_pallet"]
            if dimensions_changed and new_boxes == current_container.boxes_per_pallet:
                calculate_boxes = True

        if calculate_boxes:
            container_dict["boxes_per_pallet"] = self.calculate_boxes_per_pallet(
                    length=new_length,
                    width=new_width,
                    height=new_height,
                )

        updated_container = ContainerUpdate(**container_dict)
        return await self.repository.update(container_id, updated_container)

    async def delete_container(self, container_id: int) -> bool:
        """Удалить контейнер."""
        return await self.repository.delete(container_id)

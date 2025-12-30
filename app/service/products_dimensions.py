from typing import Optional
from math import floor

from app.database.repositories.products_dimensions import ProductDimensionsRepository
from app.models.products_dimensions import ProductDimensions, ProductDimensionsUpdate
from app.service.containers import ContainerService


class ProductDimensionsService:
    def __init__(
        self,
        repository: ProductDimensionsRepository,
        container_service: ContainerService,
    ):
        self.repository = repository
        self.container_service = container_service

    async def get_all_product_dimensions(self) -> list[ProductDimensions]:
        """Получить все габариты товаров"""
        return await self.repository.get_all()

    async def get_product_dimensions(
        self, 
        product_id: str
    ) -> Optional[ProductDimensions]:
        """Получить габариты товара по ID"""
        return await self.repository.get_by_product_id(product_id)

    async def update_product_dimensions(
        self, 
        product_id: str, 
        update_data: ProductDimensionsUpdate
    ) -> Optional[ProductDimensions]:
        """Обновить габариты товара."""
        current_product_dimensions: ProductDimensions = await self.get_product_dimensions(product_id)

        if not current_product_dimensions:
            return None

        update_data_dict = update_data.model_dump(exclude_unset=True)
        
        # Проверяем, изменились ли габариты
        dimensions_changed = False

        if "length" in update_data_dict and update_data_dict["length"] != current_product_dimensions.length:
            dimensions_changed = True
        if "width" in update_data_dict and update_data_dict["width"] != current_product_dimensions.width:
            dimensions_changed = True
        if "height" in update_data_dict and update_data_dict["height"] != current_product_dimensions.height:
            dimensions_changed = True
        
        # Проверяем, изменилась ли коробка
        container_changed = False

        if "container_id" in update_data_dict and update_data_dict["container_id"] != current_product_dimensions.container_id:
            container_changed = True

        new_length = update_data_dict.get("length", current_product_dimensions.length)
        new_width = update_data_dict.get("width", current_product_dimensions.width)
        new_height = update_data_dict.get("height", current_product_dimensions.height)

        items_per_box_provided = "items_per_box" in update_data_dict

        calculate_items = False

        if not items_per_box_provided:
            if dimensions_changed or container_changed:
                calculate_items = True
            elif current_product_dimensions.items_per_box is not None:
                update_data_dict["items_per_box"] = current_product_dimensions.items_per_box
        else:
            new_items = update_data_dict["items_per_box"]

            if dimensions_changed and new_items == current_product_dimensions.items_per_box:
                calculate_items = True

        if calculate_items:
            container_id = update_data_dict.get("container_id", current_product_dimensions.container_id)

            if container_id:
                container = await self.container_service.get_container(container_id)

                if container:
                    items_per_box = self.calculate_items_per_box(
                        product_length=new_length,
                        product_width=new_width,
                        product_height=new_height,
                        container_length=container.length,
                        container_width=container.width,
                        container_height=container.height
                    )
                    update_data_dict["items_per_box"] = items_per_box
                else:
                    update_data_dict["items_per_box"] = None
            else:
                update_data_dict["items_per_box"] = None

        if "items_per_box" in update_data_dict:
            if update_data_dict["items_per_box"] == 0:
                # Товар не помещается в коробку
                update_data_dict["items_per_box"] = 0
            elif update_data_dict["items_per_box"] is None:
                # Не удалось рассчитать (нет габаритов товара или коробки)
                pass

        to_update = ProductDimensionsUpdate(**update_data_dict)
        return await self.repository.update(product_id, to_update)

    def calculate_items_per_box(
        self,
        product_length: Optional[int],
        product_width: Optional[int],
        product_height: Optional[int],
        container_length: Optional[float],
        container_width: Optional[float],
        container_height: Optional[float],
        allow_rotation: bool = True,
    ) -> Optional[int]:
        """Рассчитать, сколько товара помещается в коробку."""
        # Проверяем, что все данные присутствуют
        if not all([product_length, product_width, product_height]):
            return None
        if not all([container_length, container_width, container_height]):
            return None
        
        # Проверяем, что все размеры положительные
        if product_length <= 0 or product_width <= 0 or product_height <= 0:
            return None
        if container_length <= 0 or container_width <= 0 or container_height <= 0:
            return None

        # Конвертируем в мм для точности
        p_len_mm = product_length * 10
        p_wid_mm = product_width * 10
        p_hei_mm = product_height * 10
        c_len_mm = int(container_length * 10)
        c_wid_mm = int(container_width * 10)
        c_hei_mm = int(container_height * 10)

        best_result = 0

        if allow_rotation:
            # Все возможные ориентации товара (6 вариантов)
            orientations = [
                (p_len_mm, p_wid_mm, p_hei_mm),
                (p_len_mm, p_hei_mm, p_wid_mm),
                (p_wid_mm, p_len_mm, p_hei_mm),
                (p_wid_mm, p_hei_mm, p_len_mm),
                (p_hei_mm, p_len_mm, p_wid_mm),
                (p_hei_mm, p_wid_mm, p_len_mm),
            ]
        else:
            orientations = [(p_len_mm, p_wid_mm, p_hei_mm)]
        
        for p_len, p_wid, p_hei in orientations:
            # Проверяем, помещается ли вообще по каждому измерению
            if p_len > c_len_mm or p_wid > c_wid_mm or p_hei > c_hei_mm:
                continue

            # Рассчитываем количество по осям
            items_x = floor(c_len_mm / p_len)
            items_y = floor(c_wid_mm / p_wid)
            items_z = floor(c_hei_mm / p_hei)

            total = items_x * items_y * items_z
            best_result = max(best_result, total)

        # Если не помещается ни в какой ориентации
        if best_result == 0:
            return 0  # Товар не помещается в коробку
        
        return best_result

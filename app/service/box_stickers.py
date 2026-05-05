import asyncio
from concurrent.futures import ProcessPoolExecutor
import io
from pathlib import Path

import qrcode
import pymupdf
from PIL import Image, ImageDraw, ImageFont

from app.database.repositories.localisation import LocalisationRepository
from app.database.repositories.sticker_user_data import StickerUserDataRepository
from app.database.repositories.stickers_storage import StickersStorageRepository
from app.models.box_stickers import BoxDataRequest, BoxSize, BoxStickerTemplateView, BoxStickerTemplateViewShort, StickerData, QRCodeData, CertificationType, BoxStickerTemplate, BoxStickerTemplateShort, StickerType
from app.database.repositories.box_stickers_templates import BoxStickersTemplateRepository
from app.service.goods_information import GoodsInformationService
from app.service.translate_manager import translation_manager


class StickerCreator:
    """Генератор изображений стикеров."""

    def __init__(
        self,
        width: int,
        height: int,
        icons_dir: str | None = None
    ):
        self._width = width
        self._height = height
        self._half_width = width // 2
        self._qr_code_version = None
        self._qr_code_box_size = 10
        self._qr_code_border = 1
        self._dpi = 4

        if icons_dir is None:
            icons_dir = Path(__file__).parents[1] / "icons"

        self._meta_icon_height = int(height * 0.1)
        self._certificate_icon_height = int(height * 0.25)
        self._icons = self._load_icons(icons_dir)
        self._cyrillic_font_path = self._find_cyrillic_font()

        if not self._cyrillic_font_path:
            print("Не найден шрифт с поддержкой кириллицы. Кириллические символы могут не отображаться.")

    def _find_cyrillic_font(self) -> str | None:
        """Найти системный шрифт с поддержкой кириллицы."""
        candidates = [
            "arial.ttf",  # Windows
            "verdana.ttf",
            "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",  # Linux
            "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf",
        ]

        for path in candidates:
            try:
                font = ImageFont.truetype(path, size=12)
                img = Image.new("RGB", (100, 100), "white")
                draw = ImageDraw.Draw(img)
                draw.text((0, 0), "АБВ", font=font, fill="black")
                return path
            except:
                continue

        return None

    def _load_icons(self, icons_dir: Path) -> dict[str, Image.Image]:
        """Загрузить иконки из директории."""
        icons = {}
        icon_files = {
            "moisture": "berech-ot-vlagi.png",
            "fragile": "hrupkoe.png",
            "eac": "eac.png",
            "rostest": "rostest.png",
        }

        meta_icons_names = {"moisture", "fragile"}
        certificate_icons = {"eac", "rostest"}
    
        for icon_key, filename in icon_files.items():
            icon_path = icons_dir / filename
            if icon_path.exists():
                try:
                    icon_img = Image.open(icon_path).convert("RGBA")
                    if icon_key in meta_icons_names:
                        icon_hight = self._meta_icon_height
                    elif icon_key in certificate_icons:
                        icon_hight = self._certificate_icon_height

                    icon_ratio = icon_hight / icon_img.height
                    icon_width = int(icon_img.width * icon_ratio)
                    icon_img = icon_img.resize((icon_width, icon_hight), Image.Resampling.LANCZOS)
                    icons[icon_key] = icon_img
                except Exception as e:
                    print(f"Ошибка загрузки иконки '{filename}': {e}")
        return icons

    def create_sticker_image(self, payload: StickerData) -> io.BytesIO:
        """Создать изображение стикера."""
        default_margin = int(self._half_width * 0.05)

        image = Image.new("RGB", (self._width, self._height), color="white")
        draw = ImageDraw.Draw(image)

        # Добавление иконок
        icon_y = default_margin
        meta_icons = [self._icons[k] for k in ["moisture", "fragile"] if k in self._icons]

        certificate_icon = None

        if payload.certification_type == CertificationType.EAC:
            certificate_icon = self._icons["eac"]
        elif payload.certification_type == CertificationType.STR:
            certificate_icon = self._icons["rostest"]
        
        if certificate_icon is not None:
            certificate_icon_size, _ = certificate_icon.size
            certificate_icon_x = self._width - default_margin - certificate_icon_size
            certificate_icon_y = self._height - certificate_icon_size - default_margin
            image.paste(certificate_icon, (certificate_icon_x, certificate_icon_y), certificate_icon)
            certificate_icon_x -= self._half_width
            image.paste(certificate_icon, (certificate_icon_x, certificate_icon_y), certificate_icon)

        if meta_icons:
            total_width = sum(icon.width for icon in meta_icons)
            spacing = (self._half_width - total_width) // (len(meta_icons))
            current_x = spacing

            for icon in meta_icons:
                image.paste(icon, (current_x, icon_y), icon)
                current_x += icon.width

            current_x = self._half_width + spacing
            for icon in meta_icons:
                image.paste(icon, (current_x, icon_y), icon)
                current_x += icon.width

        # добавление текстовых изображений
        ru_lines = [
            f"Название: {payload.name}",
            f"Артикул: {payload.article}",
            f"Цвет: {payload.color}",
            f"Вес брутто: {payload.gross_weight}кг",
            f"Вес нетто: {payload.net_weight}кг",
            f"Размер короба: {payload.box_size.length}×{payload.box_size.width}×{payload.box_size.height}см",
            f"Произведено: {payload.produced_in}",
            f"\nДок: {payload.proforma_number}",
            f"Количество: {payload.items_per_box} шт в коробе",
            f"Номер короба: {payload.box_number}/{payload.total_boxes}"
        ]

        en_lines = [
            f"Product: {payload.name_en}",
            f"Item No: {payload.article}",
            f"Color: {payload.color_en}",
            f"G. W.: {payload.gross_weight}kg",
            f"N. W: {payload.net_weight}kg",
            f"Carton Size: {payload.box_size.length}×{payload.box_size.width}×{payload.box_size.height}cm",
            f"Made in: {payload.produced_in_en}",
            f"\nQty: {payload.items_per_box} per box",
            f"N: {payload.box_number}/{payload.total_boxes}",
            ""
        ]

        ru_text = "\n".join(ru_lines)
        en_text = "\n".join(en_lines)

        ru_text_image = self._draw_text_boxed(
            text=ru_text,
            width=self._half_width - (default_margin * 2),
            height=int(self._height * 0.5)
        )

        en_text_image = self._draw_text_boxed(
            text=en_text,
            width=self._half_width - (default_margin * 2),
            height=int(self._height * 0.5)
        )

        text_y_start = icon_y + self._meta_icon_height + default_margin
        text_en_x = default_margin
        text_ru_x = self._half_width + (default_margin)

        image.paste(en_text_image, (text_en_x, text_y_start))
        image.paste(ru_text_image, (text_ru_x, text_y_start))

        # Добавление QR-кода
        qr_image = self._create_qr_code_image(
            data=QRCodeData(
                article=payload.article,
                items_per_box=payload.items_per_box,
                proforma_number=payload.proforma_number,
                box_number=payload.box_number,
                total_boxes=payload.total_boxes
            )
        )

        if qr_image.mode != "RGB":
            qr_image = qr_image.convert("RGB")

        qr_size, _ = qr_image.size
        qr_x = default_margin + self._half_width
        qr_y = self._height - qr_size - default_margin
        image.paste(qr_image, (qr_x, qr_y))
        qr_x = default_margin
        image.paste(qr_image, (qr_x, qr_y))

        # Отрисовка рамок
        draw.rectangle(
            [(0, 0), (self._width - 1, self._height - 1)],
            outline="black",
            width=2
        )

        center_x = self._half_width
        draw.line(
            [(center_x, 0), (center_x, self._height)],
            fill="black",
            width=2
        )

        # Сохранение стикера
        buffer = io.BytesIO()
        image.save(buffer, format="PNG", dpi=(self._dpi * 25.4, self._dpi * 25.4), compress_level=2, optimize=True)
        buffer.seek(0)
        return buffer

    def _draw_text_boxed(self, text: str, width: int, height: int) -> Image:
        """Сгенерировать блок с текстовым содержимым."""
        image = Image.new("RGB", (width, height), "white")
        draw = ImageDraw.Draw(image)
        max_font_size = 24
        best_font = None
        best_lines = []
        best_line_height = 0
        font_size = 6

        while font_size <= max_font_size:
            try:
                font = self._create_font(font_size=font_size)
                line_height = font.getbbox("A")[3] + 3

                lines = self._get_lines_for_text_boxed(
                    text=text,
                    width=width,
                    font=font,
                    draw=draw
                )

                total_height = len(lines) * line_height

                if total_height <= height - 8:
                    best_font = font
                    best_lines = lines
                    best_line_height = line_height
                    font_size += 1
                else:
                    break

            except Exception:
                break

        y = 0

        for line in best_lines:
            draw.text((0, y), line, font=best_font, fill="black")
            y += best_line_height

        return image

    def _create_font(self, font_size: int) -> ImageFont.FreeTypeFont:
        """Создать шрифт для тектового изображения."""
        if self._cyrillic_font_path:
            return ImageFont.truetype(self._cyrillic_font_path, size=font_size)

        return ImageFont.load_default(size=font_size)

    def _get_lines_for_text_boxed(
            self, 
            text: str,
            width: int,
            font: ImageFont.FreeTypeFont, 
            draw: ImageDraw.Draw
    ) -> list[str]:
        """Разбить текст на строки с переносом слов."""
        paragraphs = text.split("\n")
        lines = []

        for paragraph in paragraphs:
            if not paragraph.strip():
                lines.append("")
                continue

            words = paragraph.split()
            current_line = []

            for word in words:
                test_line = " ".join(current_line + [word]) if current_line else word
                bbox = draw.textbbox((0, 0), test_line, font=font)
                text_width = bbox[2] - bbox[0]

                if text_width <= width - 8:
                    current_line.append(word)
                else:
                    if current_line:
                        lines.append(" ".join(current_line))
                    current_line = [word]

            if current_line:
                lines.append(" ".join(current_line))

        return lines

    def _create_qr_code_image(self,  data: QRCodeData) -> Image.Image:
        """Сгенерировать изображение QR кода."""
        qr_info = [
            f"Артикул/Item No: {data.article}",
            f"Doc: {data.proforma_number}",
            f"Кол-во/Qty: {data.items_per_box} шт./p.b.",
            f"Номер короба/N: {data.box_number}/{data.total_boxes}"
        ]

        qr_data = "\n".join(qr_info)

        qr = qrcode.QRCode(
            version=self._qr_code_version,
            error_correction=qrcode.ERROR_CORRECT_M,
            box_size=self._qr_code_box_size,
            border=self._qr_code_border,
        )

        qr.add_data(qr_data)
        qr.make(fit=True)

        img = qr.make_image(fill_color="black", back_color="white")
        pil_img = img.get_image() 
        qr_width = int(self._half_width * 0.45)
        qr_image = pil_img.resize((qr_width, qr_width), Image.Resampling.NEAREST)

        return qr_image


class PDFStickerGenerator:
    """Генератор PDF документа со стикерами."""

    def __init__(self, sticker_width_mm: int = 140, sticker_height_mm: int = 100):
        self._sticker_width_mm = sticker_width_mm
        self._sticker_height_mm = sticker_height_mm
        self._a4_width_mm = 297
        self._a4_height_mm = 210
        self.document = pymupdf.open()
        self._stickers_per_row = 2
        self._stickers_per_column = 2
        self._stickers_per_page = self._stickers_per_row * self._stickers_per_column

    def _write_page(self, images: list[io.BytesIO]):
        """Добавить стикеры на одну страницу А4."""
        page = self.document.new_page(width=self._a4_width_mm, height=self._a4_height_mm)

        total_width = self._stickers_per_row * self._sticker_width_mm
        total_height = self._stickers_per_column * self._sticker_height_mm
        margin_x = (self._a4_width_mm - total_width) / (self._stickers_per_row + 1)
        margin_y = (self._a4_height_mm - total_height) / (self._stickers_per_column + 1)

        for idx, image in enumerate(images):
            col = idx % self._stickers_per_row
            row = idx // self._stickers_per_row
            x = margin_x + col * (self._sticker_width_mm + margin_x)
            y = margin_y + row * (self._sticker_height_mm + margin_y)

            page.insert_image(
                pymupdf.Rect(x, y, x + self._sticker_width_mm, y + self._sticker_height_mm),
                stream=image.getvalue(),
                keep_proportion=False,
            )

    def create_document(self, images: list[io.BytesIO]):
        """Создать документ из готовых изображений."""
        for i in range(0, len(images), self._stickers_per_page):
            page_images = images[i:i + self._stickers_per_page]
            self._write_page(page_images)

    def get_bytes_and_close(self) -> bytes:
        """Вернуть PDF как байты и закрыть все ресурсы."""
        buffer = io.BytesIO()
        self.document.save(
            buffer,
            garbage=4,
            clean=True,
            deflate=True,
            deflate_images=True,
            expand=0
        )
        self.document.close()
        buffer.seek(0)
        return buffer.getvalue()


class BoxStickerService:
    """Сервис для генерации стикеров коробов."""

    def __init__(self,
            template_repo: BoxStickersTemplateRepository,
            goods_info_service: GoodsInformationService,
            process_pool: ProcessPoolExecutor,
    ):
        self._process_pool = process_pool
        self._template_repo = template_repo
        self._goods_service = goods_info_service
        self._sticker_width_mm = 140
        self._sticker_hight_mm = 100

    async def get_list_templates(self) -> list[BoxStickerTemplateShort]:
        """Получить список шаблонов для стикеров."""
        return await self._template_repo.get_list()

    async def get_template(self, article: str) -> BoxStickerTemplate:
        """Получить шаблон стикера по артикулу."""
        template = await self._template_repo.get(article)

        if not template:
            template = BoxStickerTemplate()
            product_data = await self._goods_service.get_product(article)

            if not product_data:
                return template

            template.article = product_data.id
            template.name = product_data.name
        
        if not template.color:
            parts = product_data.name.split()

            for item in parts:
                colors = translation_manager.colors
                if item.lower() in colors:
                    template.color = item.capitalize()
                    template.color_en = translation_manager.translate_color(template.color)

        if not template.color_en:
            template.color_en = translation_manager.translate_color(template.color or "") or None
        
        if not template.name_en:
            template.name_en = translation_manager.transliterate_string(template.name or "") or None
        
        if not template.produced_in_en:
            template.produced_in_en = translation_manager.translate_country(template.produced_in or "") or None

        return template

    async def generate_stickers(self,  data: BoxDataRequest) -> bytes:
        """Сгенерировать документ со стикерами."""
        template = BoxStickerTemplate(
            article=data.article,
            name=data.name,
            name_en=data.name_en,
            color=data.color,
            color_en=data.color_en,
            gross_weight=data.gross_weight,
            net_weight=data.net_weight,
            box_length=data.box_size.length,
            box_height=data.box_size.height,
            box_width=data.box_size.width,
            items_per_box=data.items_per_box,
            total_boxes=data.total_boxes,
            produced_in=data.produced_in,
            produced_in_en=data.produced_in_en,
            proforma_number=data.proforma_number,
            certification_type=data.certification_type,
        )

        await self._template_repo.update(template)

        payloads = [
            StickerData(
                name=data.name,
                name_en=data.name_en,
                article=data.article,
                color=data.color,
                color_en=data.color_en,
                gross_weight=data.gross_weight,
                net_weight=data.net_weight,
                box_size=data.box_size,
                produced_in=data.produced_in,
                produced_in_en=data.produced_in_en,
                proforma_number=data.proforma_number,
                items_per_box=data.items_per_box,
                box_number=i,
                total_boxes=data.total_boxes,
                certification_type=data.certification_type
            )
            for i in range(1, data.total_boxes + 1)
        ]

        if len(payloads) <= 50:
            return await self._generate_document(payloads)

        return await self._generate_large_document(payloads)

    async def _generate_document(self,  data: list[StickerData]) -> bytes:
        """Сгенерировать документ со стикерами в отдельном процессе."""
        loop = asyncio.get_running_loop()
        images = await loop.run_in_executor(
            self._process_pool,
            self._create_sticker_batch,
            data,
            self._sticker_width_mm,
            self._sticker_hight_mm
        )

        result = await loop.run_in_executor(
            self._process_pool,
            self._create_pdf_file,
            images,
            self._sticker_width_mm,
            self._sticker_hight_mm,
        )

        return result

    async def _generate_large_document(self,  data: list[StickerData]) -> bytes:
        """
        Сгенерировать документ со стикерами в отдельном процессе.

        Генерация стикеров разбивается по процессам.
        """
        loop = asyncio.get_running_loop()
        batch_size = 50

        tasks = []
        for i in range(0, len(data), batch_size):
            batch = data[i:i+batch_size]
            tasks.append(
                loop.run_in_executor(
                    self._process_pool,
                    self._create_sticker_batch,
                    batch,
                    self._sticker_width_mm,
                    self._sticker_hight_mm,
                )
            )

        results = await asyncio.gather(*tasks)
        images = [img for batch in results for img in batch]

        result = await loop.run_in_executor(
            self._process_pool,
            self._create_pdf_file,
            images,
            self._sticker_width_mm,
            self._sticker_hight_mm,
        )

        return result

    @staticmethod
    def _create_sticker_batch(
            payloads: list[StickerData],
            width_mm: int,
            height_mm: int,
    ) -> list[io.BytesIO]:
        """Создать стикеры коробов."""
        creator = StickerCreator(
            width=int(width_mm * 4),
            height=int(height_mm * 4),
        )
        return [creator.create_sticker_image(p) for p in payloads]

    @staticmethod
    def _create_pdf_file(
            images: list[io.BytesIO],
            sticker_width: int,
            sticker_hight: int,
    ) -> io.BytesIO:
        """Создать PDF-документ со стикерами."""
        generator = PDFStickerGenerator(
            sticker_width_mm=sticker_width,
            sticker_height_mm=sticker_hight
        )

        generator.create_document(images)
        return generator.get_bytes_and_close()
    

class StickerTemplateBuilderService:

    def __init__(
        self,
        products_repo: StickersStorageRepository,
        localisation_repo: LocalisationRepository,
        user_data_repo: StickerUserDataRepository,
    ):
        self.products_repo = products_repo
        self.localisation_repo = localisation_repo
        self.user_data_repo = user_data_repo


    async def get_box_sticker_template(self, product_id: str) -> BoxStickerTemplateView:

        #собираю данный по товару из таблицы stickers_storage
        product = await self.products_repo.get_by_product_id(product_id)
        if not product:
            raise ValueError("Товар не найден")
        #собираю данные по ранее заполненными пользователем поля для данного товара
        user_data = await self.user_data_repo.get_last(
            product_id=product.product_id,
            sticker_type=StickerType.TRANSPORT,
        )
        #собираю данные по локализации, если были сохранены ранее
        localisations = await self.localisation_repo.get_by_product_id(product.product_id)
        translations = {
            (item.field_name, item.lang): item.translation
            for item in localisations
        }

        user_box_size = None
        if user_data and all([user_data.box_length, user_data.box_width, user_data.box_height]):
            user_box_size = BoxSize(
                box_length=user_data.box_length,
                box_width=user_data.box_width,
                box_height=user_data.box_height
            )

        # return BoxStickerTemplateView(
        #     product_id=product.product_id,
        #     name=product.name,
        #     name_en=translations.get(("name", "en")),
        #     color=product.color,
        #     color_en=translations.get(("color", "en")),
        #     gross_weight=product.gross_weight or 0,
        #     net_weight=product.net_weight,
        #     box_size=product.box_size,
        #     items_per_box=user_data.items_per_box if user_data and user_data.items_per_box else 1,
        #     total_boxes=user_data.total_boxes if user_data and user_data.total_boxes else 1,
        #     produced_in=(user_data.produced_in if user_data and user_data.produced_in else product.produced_in),
        #     produced_in_en=translations.get(("produced_in", "en")),
        #     proforma_number=user_data.proforma_number if user_data else None,
        #     certification_type=product.certification_type,
        # )
        return BoxStickerTemplateView(
            product_id=product.product_id,
            name=translations.get(("name", "ru")) or product.name,
            name_en=translations.get(("name", "en")),
            color=translations.get(("color", "ru")) or product.color,
            color_en=translations.get(("color", "en")),
            gross_weight=(user_data.gross_weight if user_data and user_data.gross_weight is not None 
                        else (product.gross_weight or 0)),
            net_weight=(user_data.net_weight if user_data and user_data.net_weight is not None 
                        else product.net_weight),
            box_size=user_box_size or product.box_size,
            items_per_box=user_data.items_per_box if user_data and user_data.items_per_box else 1,
            total_boxes=user_data.total_boxes if user_data and user_data.total_boxes else 1,
            proforma_number=user_data.proforma_number if user_data else None,
            produced_in=(translations.get(("produced_in", "ru")) or #TODO: реализация в локализации
                        (user_data.produced_in if user_data and user_data.produced_in else product.produced_in)),
            produced_in_en=translations.get(("produced_in", "en")),
            certification_type=(user_data.certification_type if user_data and user_data.certification_type 
                                else product.certification_type),
        )
    
    async def get_list_templates(self) -> list[BoxStickerTemplateViewShort]:
        """Получить список шаблонов для стикеров."""
        return await self.products_repo.get_list()
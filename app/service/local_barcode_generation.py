import datetime
from io import BytesIO
from typing import List

from app.models import GoodsAcceptanceCertificateCreate
from app.database.repositories import LocalBarcodeGenerationRepository
from app.models.local_barcode_generation import LocalBarcodeGenerationResponse


from barcode import Code128
from barcode.writer import ImageWriter
from PIL import Image, ImageDraw, ImageFont
import os


class LocalBarcodeGenerationService:
    def __init__(
            self,
            local_barcode_generation_repository: LocalBarcodeGenerationRepository,
    ):
        self.local_barcode_generation_repository = local_barcode_generation_repository

    async def create_data(self, data: GoodsAcceptanceCertificateCreate):
        result = await self.local_barcode_generation_repository.create_data(data)
        # await self.generate_all_barcodes(result)
        img_buffer =await self.create_barcode_image(result)

        return img_buffer

    async def create_barcode_image(self, data):
        # Параметры изображения
        width = 300
        height = 250  # Высота одного блока
        margin = 10
        text_margin = 5  # Дополнительный отступ для текста

        # Создаем шрифт
        font_path = "DejaVuSans.ttf"  # Используем системный шрифт
        font_size = 12
        try:
            font = ImageFont.truetype(font_path, font_size)
        except OSError:
            # Если шрифт не найден, используем встроенный шрифт
            font = ImageFont.load_default()

        # Создаем основное изображение для всех штрихкодов
        total_height = len(data) * (height + margin)
        final_image = Image.new('RGB', (width, total_height), color='white')
        draw = ImageDraw.Draw(final_image)

        y_offset = 0
        for item in data:
            # Создаем временное изображение для штрихкода
            barcode = Code128(item['local_barcode'], writer=ImageWriter())
            barcode_image = barcode.render()

            # Обрезаем изображение штрихкода
            barcode_width, barcode_height = barcode_image.size
            barcode_image = barcode_image.crop((0, 0, barcode_width, barcode_height // 2))
            barcode_height = barcode_height // 2  # Обновляем высоту после обрезки

            # Создаем новое изображение для текущего товара
            product_image = Image.new('RGB', (width, height), color='white')
            product_draw = ImageDraw.Draw(product_image)

            # Рассчитываем позиции для текста и штрихкода
            text_block_height = 4 * (font_size + text_margin)  # Высота блока с текстом (3 строки)
            barcode_y = text_block_height + margin  # Позиция штрихкода ниже текста

            # Добавляем текст (ID, Product, Quantity) в верхней части
            text_y = margin

            # Центрируем "Продукт"
            product_text = f"Продукт: {item['product']}"
            product_width = font.getlength(product_text)
            product_draw.text(
                ((width - product_width) / 2, text_y + font_size + text_margin),
                product_text,
                font=font,
                fill='black'
            )

            # Центрируем "Количество"
            quantity_text = f"Количество: {int(item['beginning_quantity'])}"
            quantity_width = font.getlength(quantity_text)
            product_draw.text(
                ((width - quantity_width) / 2, text_y + 2 * (font_size + text_margin)),
                quantity_text,
                font=font,
                fill='black'
            )

            product_name_text = str(item['product_name'][:41])
            product_name_width = font.getlength(product_name_text)
            product_draw.text(
                ((width - product_name_width) / 2, text_y + 3 * (font_size + text_margin)),
                product_name_text,
                font=font,
                fill='black'
            )

            # Вставляем штрихкод ниже текста
            barcode_x = (width - barcode_width) // 2  # Центрируем штрихкод
            product_image.paste(barcode_image, (barcode_x, barcode_y))

            # Добавляем local_barcode под штрихкодом
            barcode_text_y = barcode_y + barcode_height + 5  # Располагаем под штрихкодом
            product_draw.text((width // 2, barcode_text_y), item['local_barcode'], font=font, fill='black', anchor="mt")

            # Вставляем изображение товара в основное изображение
            final_image.paste(product_image, (0, y_offset))

            y_offset += height + margin

        # Сохраняем итоговое изображение
        # final_image.save("all_barcodes_dpi.png", dpi=(1000, 1000))

        # отправляем изображение в буффер оперативной памяти
        img_buffer = BytesIO()
        final_image.save(img_buffer, format="PNG", dpi=(1000, 1000))
        img_buffer.seek(0)  # Важно: переводим указатель в начало буфера

        return img_buffer

    # async def create_barcode_image(self,data):
    #     # Параметры изображения
    #     width = 300
    #     height = 250  # Высота одного блока
    #     margin = 10
    #
    #     # Создаем шрифт
    #     font_path = "DejaVuSans.ttf"  # Используем системный шрифт
    #     font_size = 12
    #     try:
    #         font = ImageFont.truetype(font_path, font_size)
    #     except OSError:
    #         # Если шрифт не найден, используем встроенный шрифт
    #         font = ImageFont.load_default()
    #
    #     # Создаем основное изображение для всех штрихкодов
    #     total_height = len(data) * (height + margin)
    #     final_image = Image.new('RGB', (width, total_height), color='white')
    #     draw = ImageDraw.Draw(final_image)
    #
    #     y_offset = 0
    #     for item in data:
    #         # Создаем временное изображение для штрихкода
    #         barcode = Code128(item['local_barcode'], writer=ImageWriter())
    #         barcode_image = barcode.render()
    #
    #         # Обрезаем изображение штрихкода
    #         barcode_width, barcode_height = barcode_image.size
    #         barcode_image = barcode_image.crop((0, 0, barcode_width, barcode_height // 2))
    #
    #         # Создаем новое изображение для текущего товара
    #         product_image = Image.new('RGB', (width, height), color='white')
    #         product_draw = ImageDraw.Draw(product_image)
    #
    #         # Вставляем штрихкод
    #         barcode_x = (width - barcode_width) // 2  # Центрируем штрихкод
    #         product_image.paste(barcode_image, (barcode_x, margin))
    #
    #         # Добавляем local_barcode под штрихкодом
    #         barcode_text_y = margin + barcode_height // 2 + 5  # Располагаем под штрихкодом
    #         product_draw.text((width // 2, barcode_text_y), item['local_barcode'], font=font, fill='black', anchor="mt")
    #
    #         # Добавляем текст (ID, Product, Quantity) выше штрихкода
    #         text_y = margin
    #         product_draw.text((margin, text_y), f"ID: {item['id']}", font=font, fill='black')
    #         product_draw.text((margin, text_y + font_size + 5), f"Product: {item['product']}", font=font, fill='black')
    #         product_draw.text((margin, text_y + 2 * (font_size + 5)), f"Quantity: {item['beginning_quantity']}", font=font, fill='black')
    #
    #         # Вставляем изображение товара в основное изображение
    #         final_image.paste(product_image, (0, y_offset))
    #
    #         y_offset += height + margin
    #
    #     # Сохраняем итоговое изображение
    #     final_image.save("all_barcodes.png")





    # async def generate_combined_barcode_image(self,data_list: list, output_filename: str = "combined_barcodes.png"):
    #     """Генерация штрихкодов с правильным расположением элементов"""
    #
    #     # =============================================
    #     # НАСТРОЙКИ (можно менять)
    #     # =============================================
    #     CONFIG = {
    #         'barcode': {
    #             'height': 100,  # Высота штрихов (пиксели)
    #             'module_width': 0.3,  # Толщина штрихов
    #             'font_size': 0,  # 0 - отключаем встроенные цифры
    #             'quiet_zone': 15  # Пустое пространство по бокам
    #         },
    #         'text': {
    #             'product_size': 40,  # Размер шрифта названия
    #             'quantity_size': 30,  # Размер шрифта количества
    #             'barcode_num_size': 35,  # Размер шрифта цифр штрихкода
    #             'margin': 20  # Отступы между элементами
    #         }
    #     }
    #
    #     # =============================================
    #     # 1. ПОДГОТОВКА ШРИФТОВ (основная проблема была здесь)
    #     # =============================================
    #     try:
    #         # Явно указываем пути к шрифтам для Windows/Linux
    #         font_paths = [
    #             'arial.ttf',
    #             '/usr/share/fonts/truetype/arial.ttf',
    #             'C:/Windows/Fonts/arial.ttf'
    #         ]
    #
    #         for path in font_paths:
    #             try:
    #                 font_product = ImageFont.truetype(path, CONFIG['text']['product_size'])
    #                 font_quantity = ImageFont.truetype(path, CONFIG['text']['quantity_size'])
    #                 font_barcode_num = ImageFont.truetype(path, CONFIG['text']['barcode_num_size'])
    #                 break
    #             except:
    #                 continue
    #         else:
    #             raise Exception("Шрифт не найден")
    #     except:
    #         # Создаем шрифт вручную если не нашли системный
    #         font_product = ImageFont.load_default()
    #         font_quantity = ImageFont.load_default()
    #         font_barcode_num = ImageFont.load_default()
    #         # Принудительно увеличиваем размер
    #         font_product.size = CONFIG['text']['product_size']
    #         font_quantity.size = CONFIG['text']['quantity_size']
    #
    #     # =============================================
    #     # 2. ГЕНЕРАЦИЯ ШТРИХКОДОВ (с отключенными цифрами)
    #     # =============================================
    #     barcode_options = {
    #         'module_width': CONFIG['barcode']['module_width'],
    #         'module_height': CONFIG['barcode']['height'] / 10,
    #         'font_size': CONFIG['barcode']['font_size'],  # Отключаем встроенные цифры
    #         'text_distance': 0,
    #         'quiet_zone': CONFIG['barcode']['quiet_zone']
    #     }
    #
    #     barcode_images = []
    #     for data in data_list:
    #         code = Code128(data['local_barcode'], writer=ImageWriter())
    #         temp_file = code.save("temp_barcode", barcode_options)
    #         barcode_img = Image.open(temp_file)
    #         os.remove(temp_file)
    #         barcode_images.append(barcode_img)
    #
    #     # =============================================
    #     # 3. РАСЧЕТ РАЗМЕРОВ (новый правильный расчет)
    #     # =============================================
    #     max_barcode_width = max(img.width for img in barcode_images)
    #
    #     # Высота одной секции (1 штрихкод + текст)
    #     section_height = (
    #             CONFIG['barcode']['height'] +
    #             CONFIG['text']['product_size'] +
    #             CONFIG['text']['quantity_size'] +
    #             CONFIG['text']['barcode_num_size'] +
    #             CONFIG['text']['margin'] * 4
    #     )
    #
    #     # Общие размеры изображения
    #     total_width = max_barcode_width + CONFIG['text']['margin'] * 2
    #     total_height = section_height * len(data_list)
    #
    #     # =============================================
    #     # 4. СОЗДАНИЕ ИЗОБРАЖЕНИЯ (с правильным расположением)
    #     # =============================================
    #     result_image = Image.new('RGB', (total_width, total_height), 'white')
    #     draw = ImageDraw.Draw(result_image)
    #
    #     y_position = CONFIG['text']['margin']
    #
    #     for data, barcode_img in zip(data_list, barcode_images):
    #         # Название товара (вверху)
    #         product_text = f"{data['product']}"
    #         text_width = draw.textlength(product_text, font=font_product)
    #         draw.text(
    #             ((total_width - text_width) // 2, y_position),
    #             product_text,
    #             fill="black",
    #             font=font_product
    #         )
    #         y_position += CONFIG['text']['product_size'] + CONFIG['text']['margin']
    #
    #         # Сам штрихкод (по центру)
    #         x_position = (total_width - barcode_img.width) // 2
    #         result_image.paste(barcode_img, (x_position, y_position))
    #         y_position += barcode_img.height + CONFIG['text']['margin']
    #
    #         # Цифры штрихкода (под штрихкодом)
    #         barcode_num_text = data['local_barcode']
    #         text_width = draw.textlength(barcode_num_text, font=font_barcode_num)
    #         draw.text(
    #             ((total_width - text_width) // 2, y_position),
    #             barcode_num_text,
    #             fill="black",
    #             font=font_barcode_num
    #         )
    #         y_position += CONFIG['text']['barcode_num_size'] + CONFIG['text']['margin']
    #
    #         # Количество товара (в самом низу секции)
    #         qty_text = f"Кол-во: {float(data['beginning_quantity']):g}"
    #         text_width = draw.textlength(qty_text, font=font_quantity)
    #         draw.text(
    #             ((total_width - text_width) // 2, y_position),
    #             qty_text,
    #             fill="black",
    #             font=font_quantity
    #         )
    #         y_position += CONFIG['text']['quantity_size'] + CONFIG['text']['margin'] * 2
    #
    #     # =============================================
    #     # 5. СОХРАНЕНИЕ РЕЗУЛЬТАТА
    #     # =============================================
    #     result_image.save(output_filename, dpi=(300, 300))
    #     return output_filename
    #
    #
    #
    #
    # def generate_barcode_image(self, data: dict, output_dir: str = "barcodes"):
    #     """
    #     Генерирует изображение штрихкода с подписями
    #
    #     :param data: Словарь с данными {
    #         'local_barcode': str,
    #         'product': str,
    #         'beginning_quantity': Decimal
    #     }
    #     :param output_dir: Директория для сохранения
    #     :return: Путь к сохраненному файлу
    #     """
    #     # Создаем директорию, если не существует
    #     os.makedirs(output_dir, exist_ok=True)
    #
    #     # 1. Генерируем штрихкод
    #     code = Code128(data['local_barcode'], writer=ImageWriter())
    #     filename = f"{output_dir}/{data['local_barcode']}"
    #
    #     # Настройки для изображения
    #     options = {
    #         'module_width': 0.4,  # Ширина штриха
    #         'module_height': 15,  # Высота штрихкода
    #         'font_size': 12,  # Размер шрифта цифр
    #         'text_distance': 1,  # Отступ текста от штрихкода
    #         'quiet_zone': 10  # Пустое пространство вокруг
    #     }
    #
    #     # Сохраняем временный файл штрихкода
    #     temp_file = code.save(filename, options)
    #
    #     # 2. Добавляем текст к изображению
    #     with Image.open(temp_file) as img:
    #         # Создаем новое изображение с дополнительным местом для текста
    #         new_height = img.height + 60  # Место для двух строк текста
    #         new_img = Image.new('RGB', (img.width, new_height), 'white')
    #         new_img.paste(img, (0, 0))
    #
    #         draw = ImageDraw.Draw(new_img)
    #
    #         try:
    #             # Пытаемся использовать шрифт Arial, если доступен
    #             font = ImageFont.truetype("arial.ttf", 16)
    #         except:
    #             # Fallback на стандартный шрифт
    #             font = ImageFont.load_default()
    #
    #         # Текст продукта (верхняя строка)
    #         product_text = f"{data['product']}"
    #         text_width = draw.textlength(product_text, font=font)
    #         draw.text(
    #             ((img.width - text_width) / 2, img.height + 10),
    #             product_text,
    #             fill="black",
    #             font=font
    #         )
    #
    #         # Текст количества (нижняя строка)
    #         qty_text = f"Кол-во: {data['beginning_quantity']}"
    #         text_width = draw.textlength(qty_text, font=font)
    #         draw.text(
    #             ((img.width - text_width) / 2, img.height + 40),
    #             qty_text,
    #             fill="black",
    #             font=font
    #         )
    #
    #         # Сохраняем финальное изображение
    #         final_filename = f"{filename}_labeled.png"
    #         new_img.save(final_filename)
    #
    #     # Удаляем временный файл без текста
    #     os.remove(temp_file)
    #
    #     return final_filename
    #
    #
    # async def generate_all_barcodes(self, barcode_data: list):
    #     """
    #     Генерирует изображения для всех штрихкодов в списке
    #
    #     :param barcode_data: Список словарей с данными
    #     :return: Список путей к созданным файлам
    #     """
    #     generated_files = []
    #     for item in barcode_data:
    #         # Преобразуем Decimal в строку для корректного отображения
    #         item['beginning_quantity'] = str(int(item['beginning_quantity']))
    #         filepath = self.generate_barcode_image(item)
    #         generated_files.append(filepath)
    #
    #     return generated_files

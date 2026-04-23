import hashlib
import json



class StickerTemplateHashService:
    @staticmethod
    def calculate(template_data: dict) -> str:
        """Формирует хэш для переданного словаря"""
        raw = json.dumps(template_data, sort_keys=True, ensure_ascii=False)
        return hashlib.sha256(raw.encode("utf-8")).hexdigest()


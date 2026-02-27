from functools import lru_cache
import json
from pathlib import Path


class TranslationManager:
    def __init__(self, data_dir: str = "data"):
        self.data_dir = Path(__file__).parents[1] / data_dir
        self._colors = None
        self._countries = None
        self._alphabet_map = None

    @property
    @lru_cache()
    def colors(self) -> dict:
        if self._colors is None:
            self._colors = self._load_json("colors_locale.json")
        return self._colors

    @property
    @lru_cache()
    def countries(self) -> dict:
        if self._countries is None:
            self._countries = self._load_json("countries_locale.json")
        return self._countries

    @property
    @lru_cache
    def alphabet_map(self):
        if self._alphabet_map is None:
            alphabet = self._load_json("ru_en_transliterate.json")
            self._alphabet_map = str.maketrans(alphabet)
        return self._alphabet_map

    def _load_json(self, filename: str) -> dict:
        with open(self.data_dir / filename, "r", encoding="utf-8") as f:
            return json.load(f)

    def translate_color(self, color: str) -> str | None:
        en_color = self.colors.get(color.lower().strip())

        if en_color:
            if color.istitle():
                return en_color.capitalize()

            if color.isupper():
                return en_color.upper()

            return en_color

        return self.transliterate_string(color)

    def translate_country(self, country: str) -> str | None:
        en_country = self.countries.get(country.strip())

        if en_country:
            if country.istitle():
                return en_country.capitalize()

            if country.isupper():
                return en_country.upper()

            return en_country

        return self.transliterate_string(country)

    def transliterate_string(self, text: str) -> str | None:
        return text.translate(self.alphabet_map)

translation_manager = TranslationManager()

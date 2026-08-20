import re
import requests

from interfaces.skill import Skill


class WeatherSkill(Skill):
    @property
    def name(self) -> str:
        return "Weather"

    @property
    def skill_id(self) -> str:
        return "system.weather"

    def execute(self, text: str = "", **kwargs) -> str:
        text = text.lower()

        city = "Минск"

        # Конструкция (?:в\s+)? делает предлог "в" необязательным
        match = re.search(r'погод[ау]\s+(?:в\s+)?([а-яёa-z\-]+)', text)
        if match:
            city = match.group(1)

        try:
            url = f"https://wttr.in/{city}?format=%t+%C"
            headers = {"Accept-Language": "ru"}

            response = requests.get(url, headers=headers, timeout=5)

            if response.status_code == 200:
                weather_data = response.text.strip()
                return f"Погода в городе {city.title()}: {weather_data}."

            return "Не смог получить данные о погоде."

        except requests.RequestException:
            return "Ошибка сети. Проверь подключение к интернету."
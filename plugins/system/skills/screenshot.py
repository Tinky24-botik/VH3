import os
from datetime import datetime
import pyautogui

from interfaces.skill import Skill


class ScreenshotSkill(Skill):
    """
    Навык для создания скриншотов экрана.
    Берет только основной монитор.
    """

    @property
    def name(self) -> str:
        return "Screenshot"

    @property
    def skill_id(self) -> str:
        return "system.screenshot"

    def execute(self, **kwargs) -> str:
        folder_name = "screenshots"
        
        if not os.path.exists(folder_name):
            try:
                os.makedirs(folder_name)
            except Exception as e:
                return f"Ошибка при создании папки: {e}"
        
        filename = datetime.now().strftime("screenshot_%Y-%m-%d_%H-%M-%S.png")
        filepath = os.path.join(folder_name, filename)
        
        try:
            screen_width, screen_height = pyautogui.size()
            pyautogui.screenshot(filepath, region=(0, 0, screen_width, screen_height))
            
            return f"Скриншот основного экрана успешно сохранен: {filename}"
        except Exception as e:
            return f"Не удалось сделать скриншот: {e}"
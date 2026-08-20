import pyautogui

from interfaces.skill import Skill


class MediaControlSkill(Skill):
    """
    Навык для мультимедийных кнопок. 
    Использует Пробел/Стрелки для активного окна (браузер/YouTube).
    """

    @property
    def name(self) -> str:
        return "Media Control"

    @property
    def skill_id(self) -> str:
        return "system.media"

    def execute(self, text: str = "", **kwargs) -> str:
        text = text.lower()
        
        if any(w in text for w in ["фул", "экран", "полн"]):
            pyautogui.press('f')
            return "Нажала 'F' для перехода в полноэкранный режим."
            
        elif any(w in text for w in ["пауз", "стоп", "продолж", "плей", "игра"]):
            # Нажимаем пробел - это на 100% остановит активное видео в любом плеере или браузере
            pyautogui.press('space')
            return "Нажала Пробел (пауза/воспроизведение)."
            
        elif any(w in text for w in ["след", "вперед", "дальш"]):
            # В YouTube Shift+N переключает на следующее видео
            pyautogui.hotkey('shift', 'n')
            return "Следующий трек/видео."
            
        elif any(w in text for w in ["предыд", "прошл", "назад"]):
            # В YouTube Shift+P переключает на предыдущее
            pyautogui.hotkey('shift', 'p')
            return "Предыдущий трек/видео."
            
        return "Не распознала медиа-команду."
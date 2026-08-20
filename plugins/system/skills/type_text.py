import time
import pyautogui
import pyperclip

from interfaces.skill import Skill


class TypeTextSkill(Skill):
    """
    Навык для диктовки и ввода текста с клавиатуры.
    Обходит баги раскладки Windows через буфер обмена.
    """

    @property
    def name(self) -> str:
        return "Type Text"

    @property
    def skill_id(self) -> str:
        return "system.type_text"

    def execute(self, text: str = "", **kwargs) -> str:
        text = text.strip()

        if not text:
            return "Текст для диктовки не передан."

        old_clipboard = pyperclip.paste()
        
        try:
            pyperclip.copy(text)
            time.sleep(0.1)
            
            pyautogui.hotkey('ctrl', 'v')
            time.sleep(0.1)
            
            return f"Текст напечатан: {text}"
        except Exception as e:
            return f"Ошибка при вводе текста: {e}"
        finally:
            pyperclip.copy(old_clipboard)
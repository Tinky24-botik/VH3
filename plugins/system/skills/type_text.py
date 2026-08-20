import time

import pyautogui
import pyperclip

from interfaces.skill import Skill


class TypeTextSkill(Skill):
    """
    Диктовка и вставка текста в активное поле.

    Используется:

        "напечатай привет"

    Текст вставляется через буфер обмена,
    поэтому русская раскладка Windows
    не мешает вводу.
    """

    @property
    def name(self) -> str:
        return "Type Text"

    @property
    def skill_id(self) -> str:
        return "system.type_text"

    def execute(
        self,
        text: str = "",
        **kwargs,
    ) -> str:

        text = text.strip()

        if not text:
            return (
                "Текст для диктовки "
                "не передан."
            )

        # Сохраняем старый буфер обмена,
        # чтобы помощник его не уничтожил.
        try:
            old_clipboard = (
                pyperclip.paste()
            )
        except Exception:
            old_clipboard = ""

        try:
            # Кладём текст в буфер.
            pyperclip.copy(text)

            # Небольшая задержка нужна,
            # чтобы Windows успела обновить
            # clipboard.
            time.sleep(0.1)

            # Вставляем в активное окно.
            pyautogui.hotkey(
                "ctrl",
                "v",
            )

            time.sleep(0.1)

            return (
                f"Текст напечатан: {text}"
            )

        except Exception as error:
            return (
                "Ошибка при вводе текста: "
                f"{error}"
            )

        finally:
            # Возвращаем старый clipboard.
            try:
                pyperclip.copy(
                    old_clipboard
                )
            except Exception:
                pass

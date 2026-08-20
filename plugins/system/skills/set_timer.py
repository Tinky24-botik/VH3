import threading
import re
import time

from interfaces.skill import Skill

# Подключаем уведомления
try:
    from core.notifier import notify
except ImportError:
    notify = print

# Импортируем наш новый приятный колокольчик
try:
    from core.sound import play_ding
except ImportError:
    def play_ding(): pass


class SetTimerSkill(Skill):
    """
    Навык для создания фоновых таймеров и напоминаний.
    Использует threading.Timer (daemon), чтобы не блокировать основной поток.
    """

    @property
    def name(self) -> str:
        return "Set Timer"

    @property
    def skill_id(self) -> str:
        return "system.set_timer"

    def _parse_time_and_message(self, text: str) -> tuple[int, str]:
        """
        Умный парсер, который вытаскивает время (в секундах) 
        и текст напоминания из общей фразы.
        """
        nums = {
            "одну": 1, "один": 1, "одна": 1, "два": 2, "две": 2, "три": 3, 
            "четыре": 4, "пять": 5, "шесть": 6, "семь": 7, "восемь": 8, 
            "девять": 9, "десять": 10, "одиннадцать": 11, "двенадцать": 12, 
            "тринадцать": 13, "четырнадцать": 14, "пятнадцать": 15, 
            "двадцать": 20, "тридцать": 30, "сорок": 40, "пятьдесят": 50, 
            "шестьдесят": 60, "полчаса": 30
        }
        
        # Делаем предлог "через" необязательным с помощью (?:через\s+)?
        match = re.search(r'(?:через\s+)?(.*?)\s+(секунд\w*|сек\w*|минут\w*|мин\w*|час\w*)', text)
        
        if not match:
            match_half = re.search(r'(?:через\s+)?(полчаса)', text)
            if not match_half:
                return 0, ""
            val_str = "30"
            unit = "минут"
            full_match = match_half.group(0)
        else:
            val_str = match.group(1)
            unit = match.group(2)
            full_match = match.group(0)
            
        val = 0
        for w in val_str.split():
            if w.isdigit():
                val += int(w)
            elif w in nums:
                val += nums[w]
        
        if val == 0:
            val = 1 
            
        multiplier = 1
        if unit.startswith("мин"): 
            multiplier = 60
        elif unit.startswith("час"): 
            multiplier = 3600
        
        seconds = val * multiplier
        
        # Удаляем конструкцию времени из фразы, чтобы получить чистый текст напоминания
        message = text.replace(full_match, "").strip()
        
        # Убираем все стартовые глаголы
        message = re.sub(r'^(напомни|поставить таймер|таймер|засеки)\s+', '', message).strip()

        # Если слов кроме времени не было, ставим дефолтный текст
        if not message:
            message = "Время вышло!"
            
        return seconds, message

    def execute(self, text: str = "", **kwargs) -> str:
        text = text.strip()

        if not text:
            return "Не указано время или текст напоминания."

        seconds, message = self._parse_time_and_message(text)
        
        if seconds <= 0:
            return "Не смогла понять время. Скажи, например: 'напомни через 5 минут'."

        # Callback-функция, которая сработает по истечении таймера
        def alarm():
            # Выводим окошко
            notify(message, kind="info")
            # Запускаем синтезированный звук колокольчика
            play_ding() 
            print(f"\n[Таймер сработал]: {message}")

        # Запускаем таймер в daemon-режиме, чтобы он не мешал закрытию программы
        t = threading.Timer(seconds, alarm)
        t.daemon = True 
        t.start()

        # Формируем красивый ответ для пользователя
        mins = seconds // 60
        secs = seconds % 60
        time_str = ""
        if mins > 0: time_str += f"{mins} мин. "
        if secs > 0: time_str += f"{secs} сек."
        
        return f"Поставила таймер на {time_str.strip()}."
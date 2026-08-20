import re
import difflib
from ctypes import cast, POINTER
from comtypes import CLSCTX_ALL
from pycaw.pycaw import AudioUtilities, IAudioEndpointVolume

from interfaces.skill import Skill


class VolumeControlSkill(Skill):
    """
    Навык для управления системной громкостью Windows (pycaw).
    Понимает как цифры, так и текстовые числительные с помощью difflib.
    """

    @property
    def name(self) -> str:
        return "Volume Control"

    @property
    def skill_id(self) -> str:
        return "system.volume"

    def _extract_number(self, text: str) -> int | None:
        nums = {
            "один": 1, "одну": 1, "два": 2, "две": 2, "три": 3, "четыре": 4, 
            "пять": 5, "шесть": 6, "семь": 7, "восемь": 8, "девять": 9, 
            "десять": 10, "одиннадцать": 11, "двенадцать": 12, "тринадцать": 13, 
            "четырнадцать": 14, "пятнадцать": 15, "двадцать": 20, "тридцать": 30, 
            "сорок": 40, "пятьдесят": 50, "шестьдесят": 60, "семьдесят": 70, 
            "восемьдесят": 80, "девяносто": 90, "сто": 100
        }
        
        # Сначала ищем обычные цифры
        digits = re.findall(r'\d+', text)
        if digits:
            return int(digits[0])
            
        # Разбиваем на слова
        words = text.split()
        
        # 1. Сначала ищем точное совпадение
        for word in words:
            if word in nums:
                return nums[word]
                
        # 2. Если точного нет, прогоняем через нечеткий поиск
        for word in words:
            matches = difflib.get_close_matches(word, nums.keys(), n=1, cutoff=0.75)
            if matches:
                return nums[matches[0]]
                
        return None

    def execute(self, text: str = "", **kwargs) -> str:
        text = text.lower()
        
        try:
            devices = AudioUtilities.GetSpeakers()
            
            if hasattr(devices, 'Activate'):
                interface = devices.Activate(IAudioEndpointVolume._iid_, CLSCTX_ALL, None)
                volume = cast(interface, POINTER(IAudioEndpointVolume))
            else:
                volume = devices.EndpointVolume
            
            if any(w in text for w in ["выключ", "беззвуч", "мут", "убери"]):
                volume.SetMute(1, None)
                return "Звук полностью выключен."
            elif any(w in text for w in ["включи", "верни"]):
                volume.SetMute(0, None)
            
            level = self._extract_number(text)
            if level is not None:
                level = max(0, min(100, level)) 
                volume.SetMasterVolumeLevelScalar(level / 100.0, None)
                volume.SetMute(0, None)
                return f"Громкость установлена на {level}%."
            
            if any(w in text for w in ["тише", "убавь", "меньше"]):
                current = round(volume.GetMasterVolumeLevelScalar() * 100)
                new_level = max(0, current - 10)
                volume.SetMasterVolumeLevelScalar(new_level / 100.0, None)
                return f"Сделала потише. Громкость {new_level}%."
                
            elif any(w in text for w in ["громче", "прибавь", "больше"]):
                current = round(volume.GetMasterVolumeLevelScalar() * 100)
                new_level = min(100, current + 10)
                volume.SetMasterVolumeLevelScalar(new_level / 100.0, None)
                return f"Сделала погромче. Громкость {new_level}%."
            
            return "Не совсем поняла, как именно изменить звук."
            
        except Exception as e:
            return f"Ошибка при обращении к микшеру Windows: {e}"
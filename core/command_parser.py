import difflib
import re

from core.router import Command


class CommandParser:
    OPEN_WORDS = {
        "открой", "запусти", "запустить", "открыть"
    }
    CLOSE_WORDS = {
        "закрой", "закрыть", "выключи"
    }
    SEARCH_WORDS = {
        "найди", "найти", "поищи"
    }
    SEND_WORDS = {
        "напиши", "отправь"
    }
    TYPE_WORDS = {
        "напечатай", "введи", "продиктуй"
    }
    DO_WORDS = {
        "сделай", "создай", "поставь"
    }
    REMIND_WORDS = {
        "напомни", "таймер", "засеки"
    }
    VOLUME_WORDS = {
        "громкость", "звук", "тише", "громче", "потише", "погромче", "убавь", "прибавь"
    }
    MEDIA_WORDS = {
        "пауза", "продолжи", "фуллскрин", "экран", "плей", "стоп", "трек"
    }
    WEATHER_WORDS = {
        "погода", "погоду"
    }

    MATCH_CUTOFF = 0.7

    def parse(self, text: str) -> Command | None:
        text = text.lower().strip()

        if not text:
            return None

        words = re.split(r"\s+", text)

        if not words:
            return None

        # --- ГЛОБАЛЬНЫЙ ПЕРЕХВАТ ---
        # Если в фразе есть "погода", сразу отрабатывает навык погоды
        if any(self._is_similar(w, self.WEATHER_WORDS) for w in words):
            return Command(
                skill_id="system.weather",
                arguments={"text": text},
            )

        action = words[0]
        rest_words = words[1:]

        if rest_words and self._is_similar(rest_words[0], {"сообщение", "смс"}):
            rest_words = rest_words[1:]

        rest = " ".join(rest_words).strip()
        matched = self._match_action(action)

        if matched is None:
            return None

        category, _ = matched

        if category == "open":
            if not rest_words:
                return None

            if any(self._is_similar(w, {"фуллскрин", "экран", "полный"}) for w in rest_words):
                return Command(
                    skill_id="system.media",
                    arguments={"text": text},
                )

            if self._is_similar(rest_words[0], {"видео", "фильм", "ролик", "клип"}):
                query = " ".join(rest_words[1:]).strip()
                if not query:
                    return None
                return Command(
                    skill_id="youtube.search",
                    arguments={"query": query},
                )

            return Command(
                skill_id="system.open_program",
                arguments={"name": rest},
            )

        if category == "close":
            if not rest:
                return None

            return Command(
                skill_id="system.close_program",
                arguments={"name": rest},
            )

        if category == "search":
            if not rest_words:
                return None

            if self._is_similar(rest_words[0], {"видео", "фильм", "ролик", "клип"}):
                query = " ".join(rest_words[1:]).strip()
                if not query:
                    return None
                return Command(
                    skill_id="youtube.search",
                    arguments={"query": query},
                )

            query = " ".join(rest_words).strip()
            if not query:
                return None

            return Command(
                skill_id="browser.search",
                arguments={"query": query},
            )

        if category == "send":
            if len(rest_words) < 2:
                return None

            recipient = rest_words[0]
            message_text = " ".join(rest_words[1:]).strip()

            if not message_text:
                return None

            return Command(
                skill_id="telegram.send_message",
                arguments={
                    "recipient": recipient,
                    "text": message_text,
                },
            )

        if category == "type":
            if not rest:
                return None

            return Command(
                skill_id="system.type_text",
                arguments={"text": rest},
            )

        if category == "do":
            if not rest_words:
                return None

            if self._is_similar(rest_words[0], {"скриншот", "скрин", "снимок"}):
                return Command(
                    skill_id="system.screenshot",
                    arguments={},
                )
                
            if any(self._is_similar(w, self.VOLUME_WORDS) for w in rest_words):
                return Command(
                    skill_id="system.volume",
                    arguments={"text": text},
                )
                
            if any(self._is_similar(w, self.MEDIA_WORDS) for w in rest_words):
                return Command(
                    skill_id="system.media",
                    arguments={"text": text},
                )

        if category == "remind":
            if not rest:
                return None
            
            return Command(
                skill_id="system.set_timer",
                arguments={"text": text},
            )
            
        if category == "volume":
            return Command(
                skill_id="system.volume",
                arguments={"text": text},
            )

        if category == "media":
            return Command(
                skill_id="system.media",
                arguments={"text": text},
            )

        return None

    def _match_action(self, action: str) -> tuple[str, str] | None:
        all_words = {word: "open" for word in self.OPEN_WORDS}
        all_words.update({word: "close" for word in self.CLOSE_WORDS})
        all_words.update({word: "search" for word in self.SEARCH_WORDS})
        all_words.update({word: "send" for word in self.SEND_WORDS})
        all_words.update({word: "type" for word in self.TYPE_WORDS})
        all_words.update({word: "do" for word in self.DO_WORDS})
        all_words.update({word: "remind" for word in self.REMIND_WORDS})
        all_words.update({word: "volume" for word in self.VOLUME_WORDS})
        all_words.update({word: "media" for word in self.MEDIA_WORDS})
        all_words.update({word: "weather" for word in self.WEATHER_WORDS})

        if action in all_words:
            return (all_words[action], action)

        close = difflib.get_close_matches(
            action,
            all_words.keys(),
            n=1,
            cutoff=self.MATCH_CUTOFF,
        )

        if close:
            matched_word = close[0]
            return (all_words[matched_word], matched_word)

        return None

    def _is_similar(self, word: str, candidates: set[str]) -> bool:
        if word in candidates:
            return True
            
        close = difflib.get_close_matches(
            word,
            candidates,
            n=1,
            cutoff=self.MATCH_CUTOFF,
        )
        return bool(close)
import difflib
import re

from core.router import Command


class CommandParser:
    OPEN_WORDS = {
        "открой",
        "запусти",
        "запустить",
        "открыть",
    }

    CLOSE_WORDS = {
        "закрой",
        "закрыть",
        "выключи",
    }

    SEARCH_WORDS = {
        "найди",
        "найти",
        "поищи",
    }

    SEND_WORDS = {
        "напиши",
        "отправь",
    }

    TYPE_WORDS = {
        "напечатай",
        "введи",
        "продиктуй",
    }

    DO_WORDS = {
        "сделай",
        "создай",
        "поставь",
    }

    REMIND_WORDS = {
        "напомни",
        "таймер",
        "засеки",
    }

    VOLUME_WORDS = {
        "громкость",
        "звук",
        "тише",
        "громче",
        "потише",
        "погромче",
        "убавь",
        "прибавь",
    }

    MEDIA_WORDS = {
        "пауза",
        "продолжи",
        "фуллскрин",
        "экран",
        "плей",
        "стоп",
        "трек",
    }

    WEATHER_WORDS = {
        "погода",
        "погоду",
    }

    MATCH_CUTOFF = 0.7

    # ==================================================
    # ОДНА КОМАНДА
    # ==================================================

    def parse(self, text: str) -> Command | None:
        """
        Преобразует одну текстовую фразу
        в один нормализованный Command.
        """

        text = text.lower().strip()

        if not text:
            return None

        words = re.split(r"\s+", text)

        if not words:
            return None

        # --------------------------------------------------
        # Глобальный перехват погоды
        # --------------------------------------------------

        if any(
            self._is_similar(word, self.WEATHER_WORDS)
            for word in words
        ):
            return Command(
                skill_id="system.weather",
                arguments={
                    "text": text,
                },
            )

        action = words[0]
        rest_words = words[1:]

        # --------------------------------------------------
        # Убираем "сообщение"/"смс"
        # --------------------------------------------------

        if (
            rest_words
            and self._is_similar(
                rest_words[0],
                {"сообщение", "смс"},
            )
        ):
            rest_words = rest_words[1:]

        rest = " ".join(rest_words).strip()

        matched = self._match_action(action)

        if matched is None:
            return None

        category, _ = matched

        # ==================================================
        # OPEN
        # ==================================================

        if category == "open":
            if not rest_words:
                return None

            # Полноэкранный режим
            if any(
                self._is_similar(
                    word,
                    {
                        "фуллскрин",
                        "экран",
                        "полный",
                    },
                )
                for word in rest_words
            ):
                return Command(
                    skill_id="system.media",
                    arguments={
                        "text": text,
                    },
                )

            # "открой видео ..."
            if self._is_similar(
                rest_words[0],
                {
                    "видео",
                    "фильм",
                    "ролик",
                    "клип",
                },
            ):
                query = " ".join(
                    rest_words[1:]
                ).strip()

                if not query:
                    return None

                return Command(
                    skill_id="youtube.search",
                    arguments={
                        "query": query,
                    },
                )

            return Command(
                skill_id="system.open_program",
                arguments={
                    "name": rest,
                },
            )

        # ==================================================
        # CLOSE
        # ==================================================

        if category == "close":
            if not rest:
                return None

            return Command(
                skill_id="system.close_program",
                arguments={
                    "name": rest,
                },
            )

        # ==================================================
        # SEARCH
        # ==================================================

        if category == "search":
            if not rest_words:
                return None

            # "найди видео ..."
            if self._is_similar(
                rest_words[0],
                {
                    "видео",
                    "фильм",
                    "ролик",
                    "клип",
                },
            ):
                query = " ".join(
                    rest_words[1:]
                ).strip()

                if not query:
                    return None

                return Command(
                    skill_id="youtube.search",
                    arguments={
                        "query": query,
                    },
                )

            query = " ".join(
                rest_words
            ).strip()

            if not query:
                return None

            return Command(
                skill_id="browser.search",
                arguments={
                    "query": query,
                },
            )

        # ==================================================
        # SEND
        # ==================================================

        if category == "send":
            if len(rest_words) < 2:
                return None

            recipient = rest_words[0]

            message_text = " ".join(
                rest_words[1:]
            ).strip()

            if not message_text:
                return None

            return Command(
                skill_id="telegram.send_message",
                arguments={
                    "recipient": recipient,
                    "text": message_text,
                },
            )

        # ==================================================
        # TYPE TEXT
        # ==================================================

        if category == "type":
            if not rest:
                return None

            return Command(
                skill_id="system.type_text",
                arguments={
                    "text": rest,
                },
            )

        # ==================================================
        # DO
        # ==================================================

        if category == "do":
            if not rest_words:
                return None

            # Скриншот
            if self._is_similar(
                rest_words[0],
                {
                    "скриншот",
                    "скрин",
                    "снимок",
                },
            ):
                return Command(
                    skill_id="system.screenshot",
                    arguments={},
                )

            # Громкость
            if any(
                self._is_similar(
                    word,
                    self.VOLUME_WORDS,
                )
                for word in rest_words
            ):
                return Command(
                    skill_id="system.volume",
                    arguments={
                        "text": text,
                    },
                )

            # Медиа
            if any(
                self._is_similar(
                    word,
                    self.MEDIA_WORDS,
                )
                for word in rest_words
            ):
                return Command(
                    skill_id="system.media",
                    arguments={
                        "text": text,
                    },
                )

        # ==================================================
        # REMINDER / TIMER
        # ==================================================

        if category == "remind":
            if not rest:
                return None

            return Command(
                skill_id="system.set_timer",
                arguments={
                    "text": text,
                },
            )

        # ==================================================
        # VOLUME
        # ==================================================

        if category == "volume":
            return Command(
                skill_id="system.volume",
                arguments={
                    "text": text,
                },
            )

        # ==================================================
        # MEDIA
        # ==================================================

        if category == "media":
            return Command(
                skill_id="system.media",
                arguments={
                    "text": text,
                },
            )

        return None

    # ==================================================
    # СОСТАВНЫЕ КОМАНДЫ
    # ==================================================

    def parse_many(
        self,
        text: str,
    ) -> list[Command] | None:
        """
        Разбирает фразу, которая может содержать
        несколько последовательных команд.

        Примеры:

            открой хром и фотошоп

        -> [
            system.open_program(chrome),
            system.open_program(photoshop)
        ]

        Или:

            открой ютуб и найди видео котики

        -> [
            system.open_program(youtube),
            youtube.search(котики)
        ]

        Важный принцип:

        Мы НЕ разделяем каждое "и" подряд.

        Например:

            найди котиков и собак

        должно остаться одним поисковым запросом.

        Разделение происходит только тогда, когда
        "и" действительно похоже на границу двух команд.
        """

        text = text.strip()

        if not text:
            return None

        # --------------------------------------------------
        # Находим части
        # --------------------------------------------------

        parts = self._split_compound_text(text)

        # Обычная одиночная команда
        if len(parts) == 1:
            command = self.parse(parts[0])

            if command is None:
                return None

            return [command]

        # --------------------------------------------------
        # Разбираем каждую часть
        # --------------------------------------------------

        commands: list[Command] = []

        for part in parts:
            command = self.parse(part)

            if command is None:
                # Если хотя бы одна часть не разобрана,
                # НЕ выполняем половину команды.
                return None

            commands.append(command)

        return commands

    # ==================================================
    # РАЗДЕЛЕНИЕ СОСТАВНЫХ ФРАЗ
    # ==================================================

    def _split_compound_text(
        self,
        text: str,
    ) -> list[str]:
        """
        Определяет реальные границы команд.

        Поддерживает:

            открой хром и фотошоп

            открой хром и найди видео котики

            поставь таймер и открой хром

            найди котиков и открой браузер

        Но НЕ ломает:

            найди котиков и собак

            напечатай привет и хорошего дня
        """

        words = re.split(
            r"\s+",
            text.strip(),
        )

        if len(words) < 3:
            return [text.strip()]

        first_match = self._match_action(
            words[0].lower()
        )

        if first_match is None:
            return [text.strip()]

        first_category, _ = first_match

        boundaries: list[int] = []

        for index in range(
            1,
            len(words) - 1,
        ):
            word = words[index].lower()

            if word != "и":
                continue

            next_word = words[index + 1].lower()

            # --------------------------------------------------
            # Вариант 1:
            # после "и" начинается новая команда
            #
            # открой хром и найди видео
            #                 ^
            # --------------------------------------------------

            next_match = self._match_action(
                next_word
            )

            if next_match is not None:
                boundaries.append(index)
                continue

            # --------------------------------------------------
            # Вариант 2:
            #
            # открой хром и фотошоп
            #
            # Для open/close допускаем список объектов.
            # --------------------------------------------------

            if first_category in {
                "open",
                "close",
            }:
                boundaries.append(index)

        # --------------------------------------------------
        # Ничего не нашли
        # --------------------------------------------------

        if not boundaries:
            return [text.strip()]

        # --------------------------------------------------
        # Собираем части
        # --------------------------------------------------

        parts: list[str] = []

        start = 0

        for boundary in boundaries:
            part = " ".join(
                words[start:boundary]
            ).strip()

            if part:
                parts.append(part)

            start = boundary + 1

        last_part = " ".join(
            words[start:]
        ).strip()

        if last_part:
            parts.append(last_part)

        return parts

    # ==================================================
    # ACTION MATCHING
    # ==================================================

    def _match_action(
        self,
        action: str,
    ) -> tuple[str, str] | None:

        all_words = {
            word: "open"
            for word in self.OPEN_WORDS
        }

        all_words.update({
            word: "close"
            for word in self.CLOSE_WORDS
        })

        all_words.update({
            word: "search"
            for word in self.SEARCH_WORDS
        })

        all_words.update({
            word: "send"
            for word in self.SEND_WORDS
        })

        all_words.update({
            word: "type"
            for word in self.TYPE_WORDS
        })

        all_words.update({
            word: "do"
            for word in self.DO_WORDS
        })

        all_words.update({
            word: "remind"
            for word in self.REMIND_WORDS
        })

        all_words.update({
            word: "volume"
            for word in self.VOLUME_WORDS
        })

        all_words.update({
            word: "media"
            for word in self.MEDIA_WORDS
        })

        all_words.update({
            word: "weather"
            for word in self.WEATHER_WORDS
        })

        if action in all_words:
            return (
                all_words[action],
                action,
            )

        close = difflib.get_close_matches(
            action,
            all_words.keys(),
            n=1,
            cutoff=self.MATCH_CUTOFF,
        )

        if close:
            matched_word = close[0]

            return (
                all_words[matched_word],
                matched_word,
            )

        return None

    # ==================================================
    # FUZZY WORD MATCH
    # ==================================================

    def _is_similar(
        self,
        word: str,
        candidates: set[str],
    ) -> bool:

        if word in candidates:
            return True

        close = difflib.get_close_matches(
            word,
            candidates,
            n=1,
            cutoff=self.MATCH_CUTOFF,
        )

        return bool(close)

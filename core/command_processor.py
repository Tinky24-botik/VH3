import threading
import time

from core.router import Command
from core.selection import resolve_selection
from core.fuzzy_match import (
    NeedsConfirmation,
    NeedsSelection,
)


PENDING_TIMEOUT_SECONDS = 15


class CommandProcessor:
    """
    Единая точка выполнения команд.

    Поддерживает:

    - обычные команды;
    - составные команды;
    - подтверждения;
    - выбор вариантов;
    - последовательное выполнение;
    - состояние для голосового listener;
    """

    def __init__(
        self,
        router,
        parser,
        on_state_change=None,
        on_show_info=None,
    ):
        self.router = router
        self.parser = parser

        self.on_state_change = on_state_change
        self.on_show_info = on_show_info

        self._pending_timer = None

        self.pending_command = None

        # Очередь оставшихся команд
        # составной фразы.
        self._command_queue: list[Command] = []

        # Защищаем состояние processor
        # от одновременного доступа
        # текстового и голосового потоков.
        self._lock = threading.RLock()

    # ==================================================
    # STATE
    # ==================================================

    def has_pending(self) -> bool:
        """
        Есть ли активный вопрос:

        - подтверждение;
        - выбор варианта.
        """

        with self._lock:
            return self.pending_command is not None

    def clear_pending(self):
        """
        Сбрасывает ожидающий вопрос.
        """

        with self._lock:
            self.pending_command = None
            self._cancel_pending_timer()

    # ==================================================
    # MAIN PROCESS
    # ==================================================

    def process(
        self,
        text: str,
    ):
        """
        Главная точка обработки текста.

        Текст может прийти:

        - из UI;
        - из Vosk;
        - из Groq;
        - из другого STT.
        """

        text = text.strip()

        if not text:
            return

        # --------------------------------------------------
        # Если сейчас ждём ответ на вопрос
        # --------------------------------------------------

        if self.has_pending():
            self._handle_pending_response(text)
            return

        # --------------------------------------------------
        # Если уже есть очередь команд
        # --------------------------------------------------

        with self._lock:
            if self._command_queue:
                self._show_info(
                    "Сейчас выполняется предыдущая команда."
                )
                return

        # --------------------------------------------------
        # Пытаемся разобрать составную команду
        # --------------------------------------------------

        commands = self.parser.parse_many(text)

        if not commands:
            self._handle_error(text)
            return

        print(
            "[Processor] -> Распознано команд: "
            f"{len(commands)}"
        )

        for command in commands:
            print(
                "[Processor] -> "
                f"{command.skill_id}"
            )

        # --------------------------------------------------
        # Одиночная или составная команда
        # --------------------------------------------------

        with self._lock:
            self._command_queue = list(commands)

        self._execute_next()

    # ==================================================
    # EXECUTE QUEUE
    # ==================================================

    def _execute_next(self):
        """
        Берёт следующую команду из очереди
        и выполняет её.

        Если Skill создаёт NeedsConfirmation
        или NeedsSelection — выполнение очереди
        временно останавливается.
        """

        with self._lock:
            if not self._command_queue:
                return

            command = self._command_queue.pop(0)

        self._execute_async(command)

    # ==================================================
    # ASYNC EXECUTION
    # ==================================================

    def _execute_async(
        self,
        command: Command,
    ):
        def task():
            try:
                if self.on_state_change:
                    self.on_state_change(
                        "executing"
                    )

                time.sleep(0.2)

                result = self.router.route(
                    command
                )

                # --------------------------------------------------
                # Нужна дополнительная информация
                # --------------------------------------------------

                if isinstance(
                    result,
                    (
                        NeedsConfirmation,
                        NeedsSelection,
                    ),
                ):
                    self._set_pending(
                        result
                    )

                    self._show_info(
                        result.question
                    )

                    if self.on_state_change:
                        self.on_state_change(
                            "passive"
                        )

                    return

                # --------------------------------------------------
                # Обычный результат
                # --------------------------------------------------

                self._show_info(
                    str(result)
                )

                is_failure = str(result).startswith(
                    (
                        "Не знаю",
                        "Не указан",
                        "Не найден",
                        "Ошибка выполнения",
                        "Неизвестная команда",
                        "Не понял",
                    )
                )

                if is_failure:
                    if self.on_state_change:
                        self.on_state_change(
                            "error"
                        )

                    # Если команда провалилась,
                    # остальные всё равно выполняем.
                    self._execute_next()

                    return

                if self.on_state_change:
                    self.on_state_change(
                        "passive"
                    )

                # --------------------------------------------------
                # Следующая команда
                # --------------------------------------------------

                self._execute_next()

            except Exception as error:
                message = (
                    "Ошибка выполнения команды: "
                    f"{error}"
                )

                print(
                    f"[Processor] -> {message}"
                )

                self._show_info(
                    message
                )

                if self.on_state_change:
                    self.on_state_change(
                        "error"
                    )

                # Не оставляем очередь зависшей
                self._execute_next()

        threading.Thread(
            target=task,
            daemon=True,
        ).start()

    # ==================================================
    # PENDING RESPONSE
    # ==================================================

    def _handle_pending_response(
        self,
        text: str,
    ):
        with self._lock:
            pending = self.pending_command

        if pending is None:
            return

        # ==================================================
        # CONFIRMATION
        # ==================================================

        if isinstance(
            pending,
            NeedsConfirmation,
        ):
            answer = (
                text
                .strip()
                .lower()
            )

            if answer in {
                "да",
                "ага",
                "верно",
                "точно",
            }:
                self.clear_pending()

                self._execute_async(
                    Command(
                        skill_id=pending.skill_id,
                        arguments={
                            **pending.arguments,
                            "confirmed": True,
                        },
                    )
                )

                return

            if answer in {
                "нет",
                "неа",
            }:
                self.clear_pending()

                self._execute_async(
                    Command(
                        skill_id=pending.skill_id,
                        arguments={
                            **pending.arguments,
                            "exclude": {
                                pending.guessed_key
                            },
                        },
                    )
                )

                return

            self._show_info(
                "Ответь «да» или «нет»."
            )

            return

        # ==================================================
        # SELECTION
        # ==================================================

        if isinstance(
            pending,
            NeedsSelection,
        ):
            selected = resolve_selection(
                text,
                pending.options,
            )

            if selected is None:
                self._show_info(
                    "Не понял, какой вариант выбрать."
                )

                return

            self.clear_pending()

            self._execute_async(
                Command(
                    skill_id=pending.skill_id,
                    arguments={
                        **pending.arguments,
                        "selected_index": selected,
                        "video_map": pending.video_map,
                    },
                )
            )

            return

        # ==================================================
        # UNKNOWN
        # ==================================================

        self.clear_pending()

    # ==================================================
    # PENDING STATE
    # ==================================================

    def _set_pending(
        self,
        pending,
    ):
        with self._lock:
            self.pending_command = pending

            self._cancel_pending_timer()

            self._pending_timer = threading.Timer(
                PENDING_TIMEOUT_SECONDS,
                self._on_pending_timeout,
            )

            self._pending_timer.daemon = True
            self._pending_timer.start()

    def _cancel_pending_timer(self):
        if self._pending_timer:
            self._pending_timer.cancel()
            self._pending_timer = None

    def _on_pending_timeout(self):
        with self._lock:
            self.pending_command = None
            self._pending_timer = None

        self._show_info(
            "Не дождался ответа, отменил вопрос."
        )

        if self.on_state_change:
            self.on_state_change(
                "passive"
            )

        # Если после вопроса были ещё команды,
        # продолжаем очередь.
        self._execute_next()

    # ==================================================
    # INFO
    # ==================================================

    def _show_info(
        self,
        text: str,
    ):
        print(
            f"[Processor] -> Результат: {text}"
        )

        if self.on_show_info:
            self.on_show_info(
                text
            )

    # ==================================================
    # ERROR
    # ==================================================

    def _handle_error(
        self,
        text: str,
    ):
        def task():
            if self.on_state_change:
                self.on_state_change(
                    "error"
                )

            print(
                "[Processor] -> Ошибка: "
                f"Не смог перевести фразу "
                f"'{text}' в команду."
            )

            self._show_info(
                "Не понял команду."
            )

            time.sleep(0.8)

            if self.on_state_change:
                self.on_state_change(
                    "passive"
                )

        threading.Thread(
            target=task,
            daemon=True,
        ).start()

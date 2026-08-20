import time
import threading
import threading

PENDING_TIMEOUT_SECONDS = 15

from core.router import Command
from core.selection import resolve_selection
from core.fuzzy_match import NeedsConfirmation, NeedsSelection


class CommandProcessor:

    def __init__(self, router, parser, on_state_change=None, on_show_info=None):
        self.router = router
        self.parser = parser
        self._pending_timer = None
        self.on_state_change = on_state_change
        self.on_show_info = on_show_info
        self.pending_command = None  # NeedsConfirmation | NeedsSelection | None

    def has_pending(self) -> bool:
        return self.pending_command is not None

    def clear_pending(self):
        self.pending_command = None
        self._cancel_pending_timer()

    def process(self, text: str):
        if self.pending_command is not None:
            self._handle_pending_response(text)
            return

        command = self.parser.parse(text)

        if command is None:
            self._handle_error(text)
            return

        print(f"[Processor] -> Успех! Фраза переведена в навык: '{command.skill_id}'")
        self._execute_async(command)

    def _handle_pending_response(self, text: str):
        pending = self.pending_command

        if isinstance(pending, NeedsConfirmation):
            answer = text.strip().lower()

            if answer in {"да", "ага", "верно", "точно"}:
                self.clear_pending()
                self._execute_async(Command(
                    skill_id=pending.skill_id,
                    arguments={**pending.arguments, "confirmed": True},
                ))
                return

            if answer in {"нет", "неа"}:
                self.pending_command = None
                self._execute_async(Command(
                    skill_id=pending.skill_id,
                    arguments={**pending.arguments, "exclude": {pending.guessed_key}},
                ))
                return

            self._show_info("Ответь «да» или «нет».")
            return

        if isinstance(pending, NeedsSelection):
            selected = resolve_selection(text, pending.options)

            self.pending_command = None

            if selected is None:
                self._show_info("Не понял, какой вариант — начни заново.")
                return

            self._execute_async(Command(
                skill_id=pending.skill_id,
                arguments={
                    **pending.arguments,
                    "selected_index": selected,
                    "video_map": pending.video_map,
                },
            ))
            return

        self.pending_command = None

    def _execute_async(self, command):
        def task():
            if self.on_state_change:
                self.on_state_change("executing")

            time.sleep(0.2)

            result = self.router.route(command)

            if isinstance(result, (NeedsConfirmation, NeedsSelection)):
                self._set_pending(result)
                self._show_info(result.question)

                if self.on_state_change:
                    self.on_state_change("passive")
                return

            self._show_info(str(result))

            is_failure = str(result).startswith((
                "Не знаю", "Не указан", "Не найден",
                "Ошибка выполнения", "Неизвестная команда",
                "Не понял",
            ))

            if self.on_state_change:
                self.on_state_change("error" if is_failure else "passive")

        threading.Thread(target=task, daemon=True).start()

    def _show_info(self, text: str):
        print(f"[Processor] -> Результат: {text}")

        if self.on_show_info:
            self.on_show_info(text)
    def _set_pending(self, pending):
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
        self.pending_command = None
        self._show_info("Не дождался ответа, отменил вопрос.")

        if self.on_state_change:
            self.on_state_change("passive")

    def _handle_error(self, text):
        def task():
            if self.on_state_change:
                self.on_state_change("error")

            print(f"[Processor] -> Ошибка: Не смог перевести фразу '{text}' в команду.")
            self._show_info("Не понял команду.")

            time.sleep(0.8)

            if self.on_state_change:
                self.on_state_change("passive")

        threading.Thread(target=task, daemon=True).start()
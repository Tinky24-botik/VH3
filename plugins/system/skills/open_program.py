import json
import os

from interfaces.skill import Skill
from core.fuzzy_match import find_match, NeedsConfirmation
from core.shortcut_finder import find_shortcuts


class OpenProgramSkill(Skill):

    @property
    def skill_id(self) -> str:
        return "system.open_program"

    @property
    def name(self) -> str:
        return "Открытие программы"

    def execute(self, **kwargs):
        program_name = kwargs.get("name")
        confirmed = kwargs.get("confirmed", False)
        exclude = kwargs.get("exclude", set())

        if not program_name:
            return "Не указано имя программы"

        programs = self._load_programs()
        program_name_lower = program_name.lower()

        # ------------------------------------------
        # 1. Явно заданные программы
        # ------------------------------------------

        match = find_match(
            program_name_lower,
            programs,
            exclude=exclude,
        )

        if match.value is not None:
            if match.needs_confirmation and not confirmed:
                return NeedsConfirmation(
                    question=f"Ты имел в виду «{match.matched_key}»?",
                    skill_id=self.skill_id,
                    arguments={"name": program_name},
                    guessed_key=match.matched_key,
                )

            os.startfile(match.value)

            if match.matched_key != program_name_lower:
                return (
                    f"Открываю {match.matched_key} "
                    f"(расслышал как «{program_name}»)"
                )

            return f"Открываю {match.matched_key}"

        # ------------------------------------------
        # 2. Сайты
        # ------------------------------------------

        sites = self._load_sites()
        site_match = find_match(
            program_name_lower,
            sites,
            exclude=exclude,
        )

        if site_match.value is not None:
            if site_match.needs_confirmation and not confirmed:
                return NeedsConfirmation(
                    question=f"Ты имел в виду сайт «{site_match.matched_key}»?",
                    skill_id=self.skill_id,
                    arguments={"name": program_name},
                    guessed_key=site_match.matched_key,
                )

            import webbrowser
            webbrowser.open(site_match.value)

            if site_match.matched_key != program_name_lower:
                return (
                    f"Открываю {site_match.matched_key} "
                    f"(расслышал как «{program_name}»)"
                )

            return f"Открываю {site_match.matched_key}"

        # ------------------------------------------
        # 3. Alias + поиск по ярлыкам
        #    (меню Пуск / рабочий стол)
        # ------------------------------------------

        aliases = self._load_aliases()
        alias_match = find_match(
            program_name_lower,
            aliases,
            exclude=exclude,
        )

        if alias_match.value is not None:
            keyword = alias_match.value.lower()
            shortcuts = find_shortcuts()

            found_path = None
            found_name = None

            for shortcut_name, shortcut_path in shortcuts.items():
                if keyword in shortcut_name:
                    found_path = shortcut_path
                    found_name = shortcut_name
                    break

            if found_path:
                os.startfile(found_path)
                return f"Открываю {found_name} (нашёл по ярлыку)"

        return (
            f"Не знаю программу «{program_name}», "
            f"добавь её в settings.json"
        )

    def _load_programs(self):
        with open(
            "config/settings.json",
            "r",
            encoding="utf-8"
        ) as f:
            data = json.load(f)
        return data.get("programs", {})

    def _load_sites(self):
        with open(
            "config/settings.json",
            "r",
            encoding="utf-8"
        ) as f:
            data = json.load(f)
        return data.get("sites", {})

    def _load_aliases(self):
        with open(
            "config/settings.json",
            "r",
            encoding="utf-8"
        ) as f:
            data = json.load(f)
        return data.get("aliases", {})
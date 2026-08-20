from interfaces.plugin import Plugin
from interfaces.skill import Skill
from plugins.system.skills.volume import VolumeControlSkill
from plugins.system.skills.media import MediaControlSkill
from plugins.system.skills.set_timer import SetTimerSkill
from plugins.system.skills.open_program import OpenProgramSkill
from plugins.system.skills.close_program import CloseProgramSkill
from plugins.system.skills.type_text import TypeTextSkill
from plugins.system.skills.screenshot import ScreenshotSkill
from plugins.system.skills.weather import WeatherSkill

class PluginImpl(Plugin):

    @property
    def plugin_id(self) -> str:
        return "system"

    def initialize(self) -> None:
        pass

    def shutdown(self) -> None:
        pass

    def get_skills(self) -> list[Skill]:
        return [
            OpenProgramSkill(),
            CloseProgramSkill(),
            TypeTextSkill(),
            ScreenshotSkill(),
         SetTimerSkill(),
         VolumeControlSkill(),
         MediaControlSkill(),
         WeatherSkill(),   
        ]
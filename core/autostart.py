import sys
import os
import winreg


APP_NAME = "VoiceHelper"
RUN_KEY_PATH = r"Software\Microsoft\Windows\CurrentVersion\Run"


def _get_run_command() -> str:
    python_exe = sys.executable
    script_path = os.path.abspath("main.py")
    return f'"{python_exe}" "{script_path}" --autostart'


def is_enabled() -> bool:
    try:
        key = winreg.OpenKey(
            winreg.HKEY_CURRENT_USER, RUN_KEY_PATH, 0, winreg.KEY_READ
        )
        try:
            winreg.QueryValueEx(key, APP_NAME)
            return True
        except FileNotFoundError:
            return False
        finally:
            winreg.CloseKey(key)
    except OSError:
        return False


def enable():
    key = winreg.OpenKey(
        winreg.HKEY_CURRENT_USER, RUN_KEY_PATH, 0, winreg.KEY_SET_VALUE
    )
    winreg.SetValueEx(key, APP_NAME, 0, winreg.REG_SZ, _get_run_command())
    winreg.CloseKey(key)


def disable():
    try:
        key = winreg.OpenKey(
            winreg.HKEY_CURRENT_USER, RUN_KEY_PATH, 0, winreg.KEY_SET_VALUE
        )
        winreg.DeleteValue(key, APP_NAME)
        winreg.CloseKey(key)
    except FileNotFoundError:
        pass
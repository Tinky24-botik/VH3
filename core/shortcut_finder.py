import os

try:
    import win32com.client
except ImportError:
    win32com = None


def _search_dirs() -> list:
    return [
        os.path.join(
            os.environ.get("PROGRAMDATA", ""),
            "Microsoft", "Windows", "Start Menu", "Programs",
        ),
        os.path.join(
            os.environ.get("APPDATA", ""),
            "Microsoft", "Windows", "Start Menu", "Programs",
        ),
        os.path.join(os.path.expanduser("~"), "Desktop"),
        r"C:\Users\Public\Desktop",
    ]


def _resolve_shortcut(lnk_path: str):
    if win32com is None:
        return None

    try:
        shell = win32com.client.Dispatch("WScript.Shell")
        shortcut = shell.CreateShortcut(lnk_path)
        target = shortcut.Targetpath
        return target if target else None

    except Exception:
        return None


_cache = None


def find_shortcuts(force_refresh: bool = False) -> dict:
    """
    Возвращает {название_ярлыка_в_нижнем_регистре: путь_к_exe}
    по всем .lnk из меню Пуск и рабочего стола (рекурсивно).

    Результат кешируется в памяти — сканирование диска
    происходит только один раз за запуск программы,
    а не при каждой голосовой команде.
    """

    global _cache

    if _cache is not None and not force_refresh:
        return _cache

    results = {}

    for base_dir in _search_dirs():
        if not base_dir or not os.path.isdir(base_dir):
            continue

        for root, _dirs, files in os.walk(base_dir):
            for filename in files:
                if not filename.lower().endswith(".lnk"):
                    continue

                lnk_path = os.path.join(root, filename)
                target = _resolve_shortcut(lnk_path)

                if not target or not os.path.exists(target):
                    continue

                display_name = filename[:-4].lower()
                results[display_name] = target

    _cache = results
    return results
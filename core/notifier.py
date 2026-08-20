_callback = None

def start():
    pass

def set_callback(cb):
    global _callback
    _callback = cb

def notify(text: str, kind: str = "info"):
    # ЯРКИЙ МАЯЧОК В КОНСОЛЬ
    print(f"\n---> [DEBUG NOTIFIER] Пришел текст: {text} <---\n")
    
    if _callback:
        _callback(text)
    else:
        print(f"[Notifier] {kind.upper()}: {text}")
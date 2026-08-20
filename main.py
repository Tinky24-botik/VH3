import sys
import signal
import threading

import numpy as np
import sounddevice as sd
from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import QObject, pyqtSignal

import json
from core.engine import VoiceHelperEngine
from core.notifier import set_callback as set_notifier_callback
from ui.overlays import SensorOverlay, TextInputOverlay, InfoOverlay
from ui.main_window import MainWindow


class UIManager(QObject):
    change_state = pyqtSignal(str)
    show_info_text = pyqtSignal(str)

    def __init__(self):
        super().__init__()
        self.text_input = None
        self.info_overlay = None
        self.change_state.connect(self._play_state_sound)
        self.show_info_text.connect(self._display_info_slot)

    def _play_state_sound(self, state: str):
        def beep():
            samplerate = 44100
            if state == "processing":
                return
            elif state == "executing":
                duration, freq = 0.3, 1000
                t = np.linspace(0, duration, int(samplerate * duration), False)
                envelope = np.exp(-10 * t / duration)
                wave = 0.4 * np.sin(2 * np.pi * freq * t) * envelope
            elif state == "error":
                duration = 0.35
                t = np.linspace(0, duration, int(samplerate * duration), False)
                envelope = np.exp(-3 * t / duration)
                wave = 0.6 * ((np.sin(2 * np.pi * 300 * t) + np.sin(2 * np.pi * 330 * t)) / 2) * envelope
            else:
                return

            sd.play(wave, samplerate)
            sd.wait()

        threading.Thread(target=beep, daemon=True).start()

    def _display_info_slot(self, text: str):
        if not self.info_overlay or not self.text_input:
            return

        info_height = self.info_overlay.calculate_height(text)

        screen_height = QApplication.primaryScreen().availableGeometry().height()
        x = self.text_input.x()

        if (self.text_input.y() + self.text_input.height() + 5 + info_height) > screen_height:
            y = self.text_input.y() - info_height - 5
        else:
            y = self.text_input.y() + self.text_input.height() + 5

        y = max(0, min(y, screen_height - info_height))

        self.info_overlay.show_message_at(text, x, y)


def main():
    signal.signal(signal.SIGINT, signal.SIG_DFL)
    from ui.log_stream import QtLogStream
    log_stream = QtLogStream()
    sys.stdout = log_stream
    app = QApplication(sys.argv)

    ui_manager = UIManager()

    sensor = SensorOverlay(start_x=20, start_y=20)
    text_input = TextInputOverlay(start_y=20)
    info_overlay = InfoOverlay(target_width=text_input.width())

    ui_manager.text_input = text_input
    ui_manager.info_overlay = info_overlay

    set_notifier_callback(ui_manager.show_info_text.emit)
    ui_manager.change_state.connect(sensor.set_state)

    engine = VoiceHelperEngine(
        on_state_change=ui_manager.change_state.emit,
        on_show_info=ui_manager.show_info_text.emit,
    )

    text_input.callback = engine.handle_text_command

    window = MainWindow(
        engine=engine,
        log_stream=log_stream,
        sensor=sensor,
        text_input=text_input,
    )
    window.show()

    with open("config/settings.json", "r", encoding="utf-8") as f:
        startup_settings = json.load(f)

    if startup_settings.get("show_indicator", True):
        sensor.show()

    if startup_settings.get("show_chat", True):
        text_input.show()

    is_autostart = "--autostart" in sys.argv

    if is_autostart:
        engine.start()
        window.notify_autostarted()

    try:
        exit_code = app.exec()
    except KeyboardInterrupt:
        exit_code = 0
    finally:
        print("\nЗавершение работы...")
        engine.stop()
        sys.exit(exit_code)


if __name__ == "__main__":
    main()
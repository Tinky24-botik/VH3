import sys
from PyQt6.QtCore import QObject, pyqtSignal


class QtLogStream(QObject):
    """
    Перехватывает print() из Python и одновременно
    дублирует его в оригинальную консоль (ничего не
    теряется) и рассылает как Qt-сигнал для панели
    терминала внутри приложения.
    """

    message = pyqtSignal(str)

    def __init__(self):
        super().__init__()
        self._original_stdout = sys.stdout

    def write(self, text: str):
        if text.strip():
            self.message.emit(text)
        self._original_stdout.write(text)

    def flush(self):
        self._original_stdout.flush()
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QPushButton, QTextEdit,
)
from PyQt6.QtCore import Qt

from ui.power_button import PowerButton


class HomePage(QWidget):

    MAX_LOG_LINES = 500

    def __init__(self, engine, log_stream=None, on_toggle=None):
        super().__init__()

        self.engine = engine
        self.on_toggle = on_toggle

        layout = QVBoxLayout()
        layout.setAlignment(Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignHCenter)
        layout.setSpacing(15)
        layout.setContentsMargins(30, 40, 30, 20)

        self.status_label = QLabel("Помощник выключен")
        self.status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.status_label.setStyleSheet("font-size: 15px; color: #aaaaaa;")

        self.power_button = PowerButton(size=180)
        self.power_button.clicked.connect(self._on_click)

        self.log_toggle_button = QPushButton("Показать журнал ▾")
        self.log_toggle_button.setFixedWidth(200)
        self.log_toggle_button.clicked.connect(self._toggle_log)

        self.log_view = QTextEdit()
        self.log_view.setReadOnly(True)
        self.log_view.setFixedHeight(220)
        self.log_view.setStyleSheet("""
            QTextEdit {
                background-color: rgba(20, 20, 20, 220);
                color: #cccccc;
                border: 1px solid gray;
                border-radius: 10px;
                font-family: Consolas, monospace;
                font-size: 12px;
            }
        """)
        self.log_view.hide()

        layout.addWidget(self.status_label)
        layout.addWidget(self.power_button, alignment=Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.log_toggle_button, alignment=Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.log_view)

        self.setLayout(layout)

        if log_stream:
            log_stream.message.connect(self._append_log)

    def _on_click(self):
        if self.engine.is_running():
            self.engine.stop()
            self._set_running_state(False)
        else:
            self.engine.start()
            self._set_running_state(True)

        if self.on_toggle:
            self.on_toggle(self.engine.is_running())

    def _set_running_state(self, running: bool):
        self.power_button.set_on(running)
        self.status_label.setText(
            "Помощник включён" if running else "Помощник выключен"
        )

    def set_autostarted(self):
        self._set_running_state(True)

    def _toggle_log(self):
        if self.log_view.isVisible():
            self.log_view.hide()
            self.log_toggle_button.setText("Показать журнал ▾")
        else:
            self.log_view.show()
            self.log_toggle_button.setText("Скрыть журнал ▴")

    def _append_log(self, text: str):
        self.log_view.append(text.rstrip())

        if self.log_view.document().blockCount() > self.MAX_LOG_LINES:
            cursor = self.log_view.textCursor()
            cursor.movePosition(cursor.MoveOperation.Start)
            cursor.select(cursor.SelectionType.LineUnderCursor)
            cursor.removeSelectedText()
            cursor.deleteChar()

        scrollbar = self.log_view.verticalScrollBar()
        scrollbar.setValue(scrollbar.maximum())
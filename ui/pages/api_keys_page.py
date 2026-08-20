import os

from dotenv import dotenv_values, set_key
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QFormLayout, QLineEdit,
    QPushButton, QLabel, QCheckBox,
)


ENV_PATH = ".env"

FIELDS = [
    ("YOUTUBE_API_KEY", "YouTube API-ключ"),
    ("TELEGRAM_API_ID", "Telegram api_id"),
    ("TELEGRAM_API_HASH", "Telegram api_hash"),
    ("GROQ_API_KEY", "Groq API-ключ"),
]


class ApiKeysPage(QWidget):

    def __init__(self):
        super().__init__()

        self.inputs = {}

        layout = QVBoxLayout()

        title = QLabel("API-ключи внешних сервисов")
        title.setStyleSheet("font-size: 16px; font-weight: bold; margin-bottom: 10px;")
        layout.addWidget(title)

        hint = QLabel(
            "Ключи сохраняются в локальный файл .env и "
            "никогда не попадают в репозиторий (он уже в .gitignore)."
        )
        hint.setWordWrap(True)
        hint.setStyleSheet("color: #aaaaaa; margin-bottom: 15px;")
        layout.addWidget(hint)

        form = QFormLayout()

        for key, label in FIELDS:
            field = QLineEdit()
            field.setEchoMode(QLineEdit.EchoMode.Password)
            field.setPlaceholderText(f"Вставь {label} сюда")
            self.inputs[key] = field
            form.addRow(label + ":", field)

        layout.addLayout(form)

        self.show_checkbox = QCheckBox("Показать значения")
        self.show_checkbox.stateChanged.connect(self._toggle_visibility)
        layout.addWidget(self.show_checkbox)

        save_button = QPushButton("Сохранить")
        save_button.clicked.connect(self._save)
        layout.addWidget(save_button)

        self.status_label = QLabel("")
        self.status_label.setStyleSheet("color: #2ecc71;")
        layout.addWidget(self.status_label)

        layout.addStretch()
        self.setLayout(layout)

        self._load_existing_values()

    def _load_existing_values(self):
        if not os.path.exists(ENV_PATH):
            return

        values = dotenv_values(ENV_PATH)

        for key, field in self.inputs.items():
            if values.get(key):
                field.setText(values[key])

    def _toggle_visibility(self, state):
        mode = (
            QLineEdit.EchoMode.Normal
            if state
            else QLineEdit.EchoMode.Password
        )
        for field in self.inputs.values():
            field.setEchoMode(mode)

    def _save(self):
        if not os.path.exists(ENV_PATH):
            open(ENV_PATH, "a", encoding="utf-8").close()

        for key, field in self.inputs.items():
            value = field.text().strip()

            if value:
                set_key(ENV_PATH, key, value)
                os.environ[key] = value

        self.status_label.setText("Сохранено и применено сразу же.")
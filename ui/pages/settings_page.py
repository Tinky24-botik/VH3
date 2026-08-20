import json

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QPushButton, QComboBox, QCheckBox, QFrame,
)

from core import autostart


SETTINGS_PATH = "config/settings.json"

STT_MODE_LABELS = {
    "auto": "Авто (Groq при наличии интернета, иначе офлайн)",
    "online": "Всегда онлайн (Groq)",
    "offline": "Всегда офлайн (локальная модель)",
}


class SettingsPage(QWidget):

    def __init__(self, sensor=None, text_input=None):
        super().__init__()

        self.sensor = sensor
        self.text_input = text_input

        self.is_dirty = False
        self._loading = False

        layout = QVBoxLayout()
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(16)

        title = QLabel("Настройки")
        title.setStyleSheet("font-size: 16px; font-weight: bold;")
        layout.addWidget(title)

        # ==================================================
        # Кодовое слово / режим распознавания (Save/Cancel)
        # ==================================================

        trigger_label = QLabel("Кодовое слово")
        trigger_label.setStyleSheet("color: #888888; font-size: 12px;")
        layout.addWidget(trigger_label)

        self.trigger_field = QLineEdit()
        self.trigger_field.setPlaceholderText("лёня")
        self.trigger_field.textChanged.connect(self._mark_dirty)
        layout.addWidget(self.trigger_field)

        trigger_hint = QLabel(
            "Изменение применится после перезапуска помощника "
            "(выключи и включи кнопкой на Главной)."
        )
        trigger_hint.setWordWrap(True)
        trigger_hint.setStyleSheet("color: #666666; font-size: 11px;")
        layout.addWidget(trigger_hint)

        stt_label = QLabel("Режим распознавания речи")
        stt_label.setStyleSheet("color: #888888; font-size: 12px; margin-top: 10px;")
        layout.addWidget(stt_label)

        self.stt_combo = QComboBox()
        for value, label in STT_MODE_LABELS.items():
            self.stt_combo.addItem(label, userData=value)
        self.stt_combo.currentIndexChanged.connect(self._mark_dirty)

        self.stt_combo.view().setStyleSheet("""
            background-color: #2a2a2a;
            color: white;
            border: 1px solid gray;
            selection-background-color: rgba(46, 204, 113, 200);
            outline: none;
        """)

        layout.addWidget(self.stt_combo)

        stt_hint = QLabel("Тоже применится после перезапуска помощника.")
        stt_hint.setStyleSheet("color: #666666; font-size: 11px;")
        layout.addWidget(stt_hint)

        buttons_layout = QHBoxLayout()
        buttons_layout.addStretch(1)

        self.cancel_button = QPushButton("Отмена")
        self.cancel_button.setEnabled(False)
        self.cancel_button.clicked.connect(self._cancel)
        buttons_layout.addWidget(self.cancel_button)

        self.save_button = QPushButton("Сохранить")
        self.save_button.setEnabled(False)
        self.save_button.clicked.connect(self._save)
        buttons_layout.addWidget(self.save_button)

        layout.addLayout(buttons_layout)

        self.status_label = QLabel("")
        self.status_label.setStyleSheet("color: #2ecc71; font-size: 12px;")
        layout.addWidget(self.status_label)

        # ==================================================
        # Разделитель
        # ==================================================

        separator = QFrame()
        separator.setFrameShape(QFrame.Shape.HLine)
        separator.setStyleSheet("background-color: #333333; margin-top: 10px;")
        layout.addWidget(separator)

        # ==================================================
        # Мгновенные переключатели (без Save/Cancel)
        # ==================================================

        instant_label = QLabel("Применяется сразу")
        instant_label.setStyleSheet("color: #666666; font-size: 11px;")
        layout.addWidget(instant_label)

        self.autostart_checkbox = QCheckBox("Запускать при включении компьютера")
        self.autostart_checkbox.stateChanged.connect(self._on_autostart_toggled)
        layout.addWidget(self.autostart_checkbox)

        self.indicator_checkbox = QCheckBox("Показывать индикатор состояния")
        self.indicator_checkbox.stateChanged.connect(self._on_indicator_toggled)
        layout.addWidget(self.indicator_checkbox)

        self.chat_checkbox = QCheckBox("Показывать окно ввода текста")
        self.chat_checkbox.stateChanged.connect(self._on_chat_toggled)
        layout.addWidget(self.chat_checkbox)

        layout.addStretch(1)
        self.setLayout(layout)

        self._load_existing()

    # ==================================================
    # DIRTY STATE (только для кодового слова / режима)
    # ==================================================

    def _mark_dirty(self):
        if not self._loading:
            self.is_dirty = True
            self.save_button.setEnabled(True)
            self.cancel_button.setEnabled(True)
            self.status_label.setText("")

    def _mark_clean(self):
        self.is_dirty = False
        self.save_button.setEnabled(False)
        self.cancel_button.setEnabled(False)

    def _cancel(self):
        self._load_existing()
        self._mark_clean()
        self.status_label.setText("Изменения отменены.")

    # ==================================================
    # LOAD / SAVE
    # ==================================================

    def _read_settings(self) -> dict:
        try:
            with open(SETTINGS_PATH, "r", encoding="utf-8") as f:
                return json.load(f)
        except FileNotFoundError:
            return {}

    def _write_settings(self, data: dict):
        with open(SETTINGS_PATH, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=4)

    def _load_existing(self):
        self._loading = True

        data = self._read_settings()

        self.trigger_field.setText(data.get("trigger", "лёня"))

        current_mode = data.get("stt_mode", "auto")
        index = self.stt_combo.findData(current_mode)
        if index >= 0:
            self.stt_combo.setCurrentIndex(index)

        self.autostart_checkbox.setChecked(autostart.is_enabled())
        self.indicator_checkbox.setChecked(data.get("show_indicator", True))
        self.chat_checkbox.setChecked(data.get("show_chat", True))

        self._loading = False

    def _save(self):
        data = self._read_settings()

        trigger = self.trigger_field.text().strip().lower()
        if trigger:
            data["trigger"] = trigger

        data["stt_mode"] = self.stt_combo.currentData()

        self._write_settings(data)

        self._mark_clean()
        self.status_label.setText("Сохранено. Перезапусти помощника, чтобы применить.")

    # ==================================================
    # МГНОВЕННЫЕ ПЕРЕКЛЮЧАТЕЛИ
    # ==================================================

    def _on_autostart_toggled(self, state):
        if self._loading:
            return

        if state:
            autostart.enable()
        else:
            autostart.disable()

    def _on_indicator_toggled(self, state):
        if self._loading:
            return

        is_checked = bool(state)

        if self.sensor:
            if is_checked:
                self.sensor.show()
            else:
                self.sensor.hide()

        data = self._read_settings()
        data["show_indicator"] = is_checked
        self._write_settings(data)

    def _on_chat_toggled(self, state):
        if self._loading:
            return

        is_checked = bool(state)

        if self.text_input:
            if is_checked:
                self.text_input.show()
            else:
                self.text_input.hide()

        data = self._read_settings()
        data["show_chat"] = is_checked
        self._write_settings(data)
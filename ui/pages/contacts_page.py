import json

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QPushButton, QScrollArea, QFrame,
)


SETTINGS_PATH = "config/settings.json"


class ContactsPage(QWidget):

    def __init__(self):
        super().__init__()

        self.rows = []
        self.is_dirty = False

        layout = QVBoxLayout()
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(10)

        title = QLabel("Контакты Telegram")
        title.setStyleSheet("font-size: 16px; font-weight: bold;")
        layout.addWidget(title)

        hint = QLabel(
            "Используется навыком «напиши/отправь» — назови имя "
            "голосом, бот отправит сообщение указанному контакту."
        )
        hint.setWordWrap(True)
        hint.setStyleSheet("color: #aaaaaa; font-size: 12px;")
        layout.addWidget(hint)

        header_layout = QHBoxLayout()
        name_header = QLabel("Имя (как будешь называть голосом)")
        target_header = QLabel("@username или номер телефона")
        name_header.setStyleSheet("color: #888888; font-size: 12px;")
        target_header.setStyleSheet("color: #888888; font-size: 12px;")
        header_layout.addWidget(name_header, 1)
        header_layout.addWidget(target_header, 1)
        header_layout.addSpacing(34)
        layout.addLayout(header_layout)

        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setFrameShape(QFrame.Shape.NoFrame)
        self.scroll_area.setStyleSheet("""
            QScrollArea {
                background-color: transparent;
                border: none;
            }
            QScrollArea > QWidget > QWidget {
                background-color: transparent;
            }
        """)

        self.rows_container = QWidget()
        self.rows_container.setStyleSheet("background-color: transparent;")
        self.rows_layout = QVBoxLayout()
        self.rows_layout.setContentsMargins(0, 0, 0, 0)
        self.rows_layout.setSpacing(6)
        self.rows_layout.addStretch(1)
        self.rows_container.setLayout(self.rows_layout)

        self.scroll_area.setWidget(self.rows_container)
        layout.addWidget(self.scroll_area, 1)

        buttons_layout = QHBoxLayout()

        add_button = QPushButton("+ Добавить контакт")
        add_button.clicked.connect(lambda: self._add_row("", "", mark_dirty=True))
        buttons_layout.addWidget(add_button)

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

        self.setLayout(layout)

        self._load_existing()

    # ==================================================
    # DIRTY STATE
    # ==================================================

    def _mark_dirty(self):
        self.is_dirty = True
        self.save_button.setEnabled(True)
        self.cancel_button.setEnabled(True)
        self.status_label.setText("")

    def _mark_clean(self):
        self.is_dirty = False
        self.save_button.setEnabled(False)
        self.cancel_button.setEnabled(False)

    def _cancel(self):
        self._clear_rows()
        self._load_existing()
        self._mark_clean()
        self.status_label.setText("Изменения отменены.")

    def _clear_rows(self):
        for _, _, row_widget in self.rows:
            row_widget.setParent(None)
            row_widget.deleteLater()
        self.rows = []

    # ==================================================
    # LOAD / ROWS
    # ==================================================

    def _load_existing(self):
        contacts = self._read_contacts()

        if not contacts:
            self._add_row("", "", mark_dirty=False)
            return

        for name, target in contacts.items():
            self._add_row(name, target, mark_dirty=False)

    def _add_row(self, name_value: str, target_value: str, mark_dirty: bool):
        row_widget = QWidget()
        row_widget.setStyleSheet("background-color: transparent;")
        row_layout = QHBoxLayout()
        row_layout.setContentsMargins(0, 0, 0, 0)
        row_layout.setSpacing(8)
        row_widget.setLayout(row_layout)

        name_field = QLineEdit(name_value)
        name_field.setPlaceholderText("любимка")
        name_field.textChanged.connect(self._mark_dirty)

        target_field = QLineEdit(target_value)
        target_field.setPlaceholderText("@username или +375...")
        target_field.textChanged.connect(self._mark_dirty)

        delete_button = QPushButton("✕")
        delete_button.setFixedSize(30, 30)
        delete_button.setStyleSheet("""
            QPushButton {
                background-color: rgba(60, 30, 30, 220);
                color: #ff6b6b;
                border: 1px solid #a03030;
                border-radius: 8px;
                font-size: 14px;
                font-weight: bold;
                padding: 0px;
            }
            QPushButton:hover {
                background-color: rgba(90, 30, 30, 220);
            }
        """)
        delete_button.clicked.connect(lambda: self._remove_row(row_widget))

        row_layout.addWidget(name_field, 1)
        row_layout.addWidget(target_field, 1)
        row_layout.addWidget(delete_button)

        self.rows_layout.insertWidget(self.rows_layout.count() - 1, row_widget)
        self.rows.append((name_field, target_field, row_widget))

        if mark_dirty:
            self._mark_dirty()

    def _remove_row(self, row_widget: QWidget):
        self.rows = [
            (name, target, w) for (name, target, w) in self.rows if w is not row_widget
        ]
        row_widget.setParent(None)
        row_widget.deleteLater()
        self._mark_dirty()

    # ==================================================
    # SAVE / READ
    # ==================================================

    def _read_contacts(self) -> dict:
        try:
            with open(SETTINGS_PATH, "r", encoding="utf-8") as f:
                data = json.load(f)
            return data.get("contacts", {})
        except FileNotFoundError:
            return {}

    def _save(self):
        try:
            with open(SETTINGS_PATH, "r", encoding="utf-8") as f:
                data = json.load(f)
        except FileNotFoundError:
            data = {}

        contacts = {}

        for name_field, target_field, _ in self.rows:
            name = name_field.text().strip().lower()
            target = target_field.text().strip()

            if name and target:
                contacts[name] = target

        data["contacts"] = contacts

        with open(SETTINGS_PATH, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=4)

        self._mark_clean()
        self.status_label.setText("Сохранено.")
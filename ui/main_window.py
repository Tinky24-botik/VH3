from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QFrame, QPushButton, QButtonGroup,
)
from PyQt6.QtCore import Qt, QTimer, QPropertyAnimation, QEasingCurve

from ui.animated_stack import AnimatedStackedWidget
from ui.pages.home_page import HomePage
from ui.pages.api_keys_page import ApiKeysPage
from ui.pages.dictionary_page import DictionaryPage
from ui.pages.contacts_page import ContactsPage
from ui.pages.settings_page import SettingsPage
from ui.pages.instructions_page import InstructionsPage


DARK_STYLESHEET = """
    QMainWindow, QWidget#central {
        background-color: #1a1a1a;
    }
    QLabel {
        color: white;
    }
    QLineEdit, QTextEdit {
        background-color: rgba(30, 30, 30, 200);
        color: white;
        border: 1px solid gray;
        border-radius: 10px;
        padding: 5px 10px;
        font-size: 14px;
    }
    QPushButton {
        background-color: rgba(45, 45, 45, 220);
        color: white;
        border: 1px solid gray;
        border-radius: 8px;
        padding: 6px 14px;
    }
    QPushButton:hover {
        background-color: rgba(65, 65, 65, 220);
    }
    QPushButton:disabled {
        background-color: rgba(30, 30, 30, 180);
        color: #666666;
        border: 1px solid #444444;
    }
    QComboBox {
        background-color: rgba(30, 30, 30, 200);
        color: white;
        border: 1px solid gray;
        border-radius: 10px;
        padding: 5px 10px;
        font-size: 14px;
    }
    QComboBox::drop-down {
        border: none;
    }
    QFrame#navBar {
        background-color: rgba(30, 30, 30, 220);
        border: 1px solid gray;
        border-radius: 16px;
    }
    QPushButton#navTab {
        background-color: transparent;
        color: white;
        border: none;
        border-radius: 12px;
        padding: 8px 18px;
        font-size: 13px;
    }
    QPushButton#navTab:hover {
        background-color: rgba(255, 255, 255, 15);
    }
"""


class NavIndicator(QWidget):
    """
    Зелёный "пузырь", который плавно скользит
    к активной вкладке при переключении.
    """

    def __init__(self, parent):
        super().__init__(parent)
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        self.setStyleSheet("""
            background-color: rgba(39, 214, 105, 230);
            border-radius: 12px;
        """)


class MainWindow(QMainWindow):

    def __init__(self, engine, log_stream=None, sensor=None, text_input=None):
        super().__init__()

        self.engine = engine
        self._nav_animation = None

        self.setWindowTitle("VoiceHelper")
        self.resize(820, 560)
        self.setStyleSheet(DARK_STYLESHEET)

        central = QWidget()
        central.setObjectName("central")
        self.setCentralWidget(central)

        outer_layout = QVBoxLayout()
        outer_layout.setContentsMargins(15, 15, 15, 15)
        outer_layout.setSpacing(10)
        central.setLayout(outer_layout)

        top_bar = QHBoxLayout()

        self.nav_frame = QFrame()
        self.nav_frame.setObjectName("navBar")
        self.nav_frame.setFixedHeight(44)

        self.nav_indicator = NavIndicator(self.nav_frame)
        self.nav_indicator.hide()

        nav_layout = QHBoxLayout()
        nav_layout.setContentsMargins(6, 4, 6, 4)
        nav_layout.setSpacing(4)
        self.nav_frame.setLayout(nav_layout)

        self.nav_group = QButtonGroup(self)
        self.nav_group.setExclusive(True)
        self.nav_group.idClicked.connect(self._on_nav_changed)

        top_bar.addStretch(1)
        top_bar.addWidget(self.nav_frame)
        top_bar.addStretch(1)

        outer_layout.addLayout(top_bar)

        self.pages = AnimatedStackedWidget()
        outer_layout.addWidget(self.pages)

        self.home_page = HomePage(engine=self.engine, log_stream=log_stream)
        self._add_page("Главная", self.home_page, nav_layout)
        self._add_page("Словарь", DictionaryPage(), nav_layout)
        self._add_page("Telegram-контакты", ContactsPage(), nav_layout)
        self._add_page("API-ключи", ApiKeysPage(), nav_layout)
        self._add_page(
            "Настройки",
            SettingsPage(sensor=sensor, text_input=text_input),
            nav_layout,
        )
        self._add_page("Инструкция", InstructionsPage(), nav_layout)

        first_button = self.nav_group.button(0)
        if first_button:
            first_button.setChecked(True)

    def showEvent(self, event):
        super().showEvent(event)
        self._move_indicator_to(self.nav_group.checkedId(), animate=False)

    def _add_page(self, title: str, widget: QWidget, nav_layout: QHBoxLayout):
        index = self.pages.count()

        button = QPushButton(title)
        button.setObjectName("navTab")
        button.setCheckable(True)

        self.nav_group.addButton(button, index)
        nav_layout.addWidget(button)

        self.pages.addWidget(widget)

    def _on_nav_changed(self, index: int):
        self.pages.setCurrentIndex(index)
        self._move_indicator_to(index, animate=True)

    def _move_indicator_to(self, index: int, animate: bool = True):
        button = self.nav_group.button(index)

        if not button:
            return

        target_rect = button.geometry()

        if not animate or not self.nav_indicator.isVisible():
            self.nav_indicator.setGeometry(target_rect)
            self.nav_indicator.show()
            self.nav_indicator.lower()
            return

        self._nav_animation = QPropertyAnimation(self.nav_indicator, b"geometry")
        self._nav_animation.setDuration(220)
        self._nav_animation.setStartValue(self.nav_indicator.geometry())
        self._nav_animation.setEndValue(target_rect)
        self._nav_animation.setEasingCurve(QEasingCurve.Type.OutCubic)
        self._nav_animation.start()

    def notify_autostarted(self):
        self.home_page.set_autostarted()
import sys
import signal
from PyQt6.QtWidgets import QWidget, QLineEdit, QVBoxLayout, QApplication, QLabel
from PyQt6.QtCore import Qt, QTimer, QPoint, QEvent, QRect
from PyQt6.QtGui import QPainter, QColor, QBrush, QFontMetrics

class SensorOverlay(QWidget):
    def __init__(self, start_x=20, start_y=20, custom_colors=None):
        super().__init__()
        self.setWindowFlags(Qt.WindowType.WindowStaysOnTopHint | Qt.WindowType.FramelessWindowHint | Qt.WindowType.Tool)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setGeometry(start_x, start_y, 60, 60)
        
        default_colors = {
            "passive": ((180, 180, 180), (100, 100, 100)),
            "processing": ((255, 200, 0), (180, 140, 0)),
            "executing": ((38, 147, 42), (25, 98, 28)),   
            "error": ((212, 28, 28), (141, 18, 18))       
        }
        self.color_map = custom_colors if custom_colors else default_colors
        self.current_state = "passive"
        self.wave_timer = QTimer(self)
        self.wave_timer.timeout.connect(self._animate_wave)
        self.wave_radius = 10
        self.wave_alpha = 0
        self.drag_position = None

    def set_state(self, state: str):
        if state in self.color_map:
            self.current_state = state
            if state == "processing":
                self.wave_radius = 10
                self.wave_alpha = 200
                self.wave_timer.start(60)
            else:
                self.wave_timer.stop()
                self.wave_radius = 10
                self.wave_alpha = 0
            self.update()

    def _animate_wave(self):
        self.wave_radius += 0.5
        self.wave_alpha = max(0, int(200 - ((self.wave_radius - 10) * 13)))
        if self.wave_radius >= 25:
            self.wave_radius = 10
            self.wave_alpha = 200
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.setPen(Qt.PenStyle.NoPen)
        center_x, center_y = 30, 30
        inner_rgb, outer_rgb = self.color_map[self.current_state]
        base_alpha = 127 if self.current_state == "passive" else 165
        
        if self.current_state == "processing" and self.wave_alpha > 0:
            painter.setBrush(QBrush(QColor(*inner_rgb, self.wave_alpha)))
            painter.drawEllipse(int(center_x - self.wave_radius), int(center_y - self.wave_radius), int(self.wave_radius * 2), int(self.wave_radius * 2))

        painter.setBrush(QBrush(QColor(*outer_rgb, base_alpha)))
        painter.drawEllipse(center_x - 15, center_y - 15, 30, 30)
        painter.setBrush(QBrush(QColor(*inner_rgb, base_alpha)))
        painter.drawEllipse(center_x - 10, center_y - 10, 20, 20)

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.drag_position = event.globalPosition().toPoint() - self.frameGeometry().topLeft()
            event.accept()

    def mouseMoveEvent(self, event):
        if event.buttons() == Qt.MouseButton.LeftButton and self.drag_position is not None:
            self.move(event.globalPosition().toPoint() - self.drag_position)
            event.accept()

class TextInputOverlay(QWidget):
    def __init__(self, start_x=None, start_y=20, callback=None):
        super().__init__()
        self.callback = callback
        self.setWindowFlags(Qt.WindowType.WindowStaysOnTopHint | Qt.WindowType.FramelessWindowHint | Qt.WindowType.Tool)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        
        screen = QApplication.primaryScreen().availableGeometry()
        self.widget_width = 320
        self.widget_height = 60
        
        if start_x is None:
            start_x = screen.width() - self.widget_width - 20
            
        self.setGeometry(start_x, start_y, self.widget_width, self.widget_height)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        
        self.input_field = QLineEdit()
        self.input_field.setPlaceholderText("Введите команду...")
        self.input_field.returnPressed.connect(self._on_enter)
        self.input_field.installEventFilter(self)
        layout.addWidget(self.input_field)

        self.drag_position = None
        self.is_locked = False
        self._update_style()

    def _update_style(self):
        border_color = "rgba(50, 50, 50, 150)" if self.is_locked else "gray"
        self.input_field.setStyleSheet(f"""
            QLineEdit {{
                background-color: rgba(30, 30, 30, 200);
                color: white;
                border: 1px solid {border_color};
                border-radius: 10px;
                padding: 5px 10px;
                font-size: 14px;
            }}
        """)

    def _on_enter(self):
        text = self.input_field.text().strip()
        if text and self.callback:
            self.callback(text)
        self.input_field.clear()

    def eventFilter(self, obj, event):
        if obj == self.input_field:
            if event.type() == QEvent.Type.ContextMenu: return True
            if event.type() == QEvent.Type.MouseButtonPress:
                if event.button() == Qt.MouseButton.MiddleButton:
                    self.is_locked = not self.is_locked
                    self._update_style()
                    return True
                elif event.button() == Qt.MouseButton.RightButton and not self.is_locked:
                    self.drag_position = event.globalPosition().toPoint() - self.frameGeometry().topLeft()
                    return True
            elif event.type() == QEvent.Type.MouseMove:
                if event.buttons() == Qt.MouseButton.RightButton and self.drag_position is not None and not self.is_locked:
                    self.move(event.globalPosition().toPoint() - self.drag_position)
                    return True
            elif event.type() == QEvent.Type.MouseButtonRelease:
                if event.button() == Qt.MouseButton.RightButton:
                    self.drag_position = None
                    return True
        return super().eventFilter(obj, event)

class InfoOverlay(QWidget):
    def __init__(self, target_width=300):
        super().__init__()
        self.setWindowFlags(Qt.WindowType.WindowStaysOnTopHint | Qt.WindowType.FramelessWindowHint | Qt.WindowType.Tool | Qt.WindowType.WindowTransparentForInput)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(10, 0, 10, 10)
        
        self.label = QLabel("")
        self.label.setWordWrap(True)
        self.label.setStyleSheet("""
            QLabel {
                background-color: rgba(30, 30, 30, 210);
                color: white;
                border: 1px solid gray;
                border-radius: 10px;
                padding: 12px;
                font-size: 15px;
                font-weight: bold;
            }
        """)
        self.layout.addWidget(self.label)
        self.setFixedWidth(target_width)
        
        self.hide_timer = QTimer(self)
        self.hide_timer.setSingleShot(True)
        self.hide_timer.timeout.connect(self.hide)
        self.hide()

    def calculate_height(self, text: str) -> int:
        LABEL_PADDING = 12  # см. padding: 12px в стилях self.label

        margins = self.layout.contentsMargins()

        available_width = (
            self.width()
            - margins.left()
            - margins.right()
            - LABEL_PADDING * 2
        )

        metrics = QFontMetrics(self.label.font())
        text_rect = metrics.boundingRect(
            QRect(0, 0, max(available_width, 50), 0),
            Qt.TextFlag.TextWordWrap,
            text,
        )

        return (
            text_rect.height()
            + LABEL_PADDING * 2
            + margins.top()
            + margins.bottom()
        )
    def show_message_at(self, text, x_pos, y_pos):
        self.label.setText(text)

        # Сбрасываем старые ограничения по высоте перед
        # тем, как задать новую — иначе Windows иногда
        # "помнит" прошлый максимум ещё пару кадров.
        self.setMinimumHeight(0)
        self.setMaximumHeight(16777215)

        self.setFixedHeight(self.calculate_height(text))
        self.move(x_pos, y_pos)
        self.show()
        self.hide_timer.start(5000)
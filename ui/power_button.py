from PyQt6.QtWidgets import QWidget
from PyQt6.QtGui import QPainter, QColor, QBrush, QPen, QRadialGradient
from PyQt6.QtCore import Qt, pyqtSignal, QPointF


class PowerButton(QWidget):
    clicked = pyqtSignal()

    def __init__(self, size: int = 140, parent=None):
        super().__init__(parent)

        self._size = size
        self._on = False
        self._pressed = False

        # Запас по краям под ручное свечение,
        # чтобы оно не обрезалось границей виджета.
        self.setFixedSize(size + 50, size + 50)
        self.setCursor(Qt.CursorShape.PointingHandCursor)

    def set_on(self, on: bool):
        self._on = on
        self.update()

    def is_on(self) -> bool:
        return self._on

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        center = QPointF(self.width() / 2, self.height() / 2)
        radius = (self._size - 12) / 2

        if self._on:
            fill = QColor(38, 147, 42)
            border = QColor(46, 204, 113)

            glow = QRadialGradient(center, radius + 28)
            glow.setColorAt(0.0, QColor(46, 204, 113, 130))
            glow.setColorAt(1.0, QColor(46, 204, 113, 0))
            painter.setBrush(QBrush(glow))
            painter.setPen(Qt.PenStyle.NoPen)
            painter.drawEllipse(center, radius + 28, radius + 28)
        else:
            fill = QColor(40, 40, 40)
            border = QColor(120, 120, 120)

        if self._pressed:
            fill = fill.darker(140)

        painter.setBrush(QBrush(fill))
        painter.setPen(QPen(border, 3))
        painter.drawEllipse(center, radius, radius)

        painter.setPen(QColor(255, 255, 255))
        font = painter.font()
        font.setBold(True)
        font.setPointSize(11)
        painter.setFont(font)
        painter.drawText(
            self.rect(),
            Qt.AlignmentFlag.AlignCenter,
            "ВКЛ" if self._on else "ВЫКЛ",
        )

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self._pressed = True
            self.update()

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton and self._pressed:
            self._pressed = False
            self.update()

            if self.rect().contains(event.pos()):
                self.clicked.emit()
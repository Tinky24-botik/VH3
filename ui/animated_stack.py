from PyQt6.QtWidgets import QStackedWidget, QGraphicsOpacityEffect
from PyQt6.QtCore import QPropertyAnimation, QEasingCurve


class AnimatedStackedWidget(QStackedWidget):

    def __init__(self, parent=None, duration: int = 180):
        super().__init__(parent)
        self._duration = duration
        self._animation = None

    def setCurrentIndex(self, index: int):
        if index == self.currentIndex():
            return

        next_widget = self.widget(index)

        if next_widget is None:
            super().setCurrentIndex(index)
            return

        effect = QGraphicsOpacityEffect(next_widget)
        next_widget.setGraphicsEffect(effect)
        effect.setOpacity(0)

        super().setCurrentIndex(index)

        self._animation = QPropertyAnimation(effect, b"opacity")
        self._animation.setDuration(self._duration)
        self._animation.setStartValue(0)
        self._animation.setEndValue(1)
        self._animation.setEasingCurve(QEasingCurve.Type.OutCubic)
        self._animation.finished.connect(
            lambda: next_widget.setGraphicsEffect(None)
        )
        self._animation.start()
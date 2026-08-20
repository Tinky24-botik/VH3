from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLabel
from PyQt6.QtCore import Qt


class InstructionsPage(QWidget):

    def __init__(self):
        super().__init__()

        layout = QVBoxLayout()
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        label = QLabel("Инструкция")
        label.setStyleSheet("color: #888888; font-size: 14px;")

        layout.addWidget(label)
        self.setLayout(layout)
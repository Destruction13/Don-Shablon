from PySide6.QtWidgets import QPushButton
from PySide6.QtCore import QTimer, Qt
from PySide6.QtGui import QPainter, QPen, QColor, QBrush, QConicalGradient


class RainbowButton(QPushButton):
    """Button with animated rainbow border."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._angle = 0
        self._timer = QTimer(self)
        self._timer.timeout.connect(self._advance)
        self._timer.start(50)
        self.setCursor(Qt.PointingHandCursor)

    def _advance(self):
        self._angle = (self._angle + 5) % 360
        self.update()

    def paintEvent(self, event):
        super().paintEvent(event)
        painter = QPainter(self)
        rect = self.rect().adjusted(2, 2, -2, -2)
        gradient = QConicalGradient(rect.center(), self._angle)
        for i in range(6):
            hue = (self._angle + i * 60) % 360
            gradient.setColorAt(i / 6, QColor.fromHsv(hue, 255, 255))
        pen = QPen(QBrush(gradient), 4)
        painter.setPen(pen)
        painter.setBrush(Qt.NoBrush)
        painter.drawRoundedRect(rect, 8, 8)


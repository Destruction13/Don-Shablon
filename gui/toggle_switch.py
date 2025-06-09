from PySide6.QtWidgets import QCheckBox
from PySide6.QtCore import QSize, Qt, QRectF
from PySide6.QtGui import QPainter, QColor

class ToggleSwitch(QCheckBox):
    """Simple on/off switch widget."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.setCursor(Qt.PointingHandCursor)
        self.setChecked(False)
        self.toggled.connect(self._update_tooltip)
        self._update_tooltip(self.isChecked())

    def _update_tooltip(self, checked: bool) -> None:
        self.setToolTip("Женский" if checked else "Мужской")

    def sizeHint(self) -> QSize:
        return QSize(40, 20)

    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        track_rect = self.rect().adjusted(1, 5, -1, -5)
        knob_diam = track_rect.height()
        p.setPen(Qt.NoPen)
        p.setBrush(QColor("#4caf50") if self.isChecked() else QColor("#999"))
        p.drawRoundedRect(track_rect, track_rect.height() / 2, track_rect.height() / 2)
        knob_x = track_rect.right() - knob_diam if self.isChecked() else track_rect.left()
        p.setBrush(QColor("#fff"))
        p.drawEllipse(QRectF(knob_x, track_rect.top(), knob_diam, knob_diam))
        p.end()

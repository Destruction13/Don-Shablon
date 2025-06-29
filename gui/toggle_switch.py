from PySide6.QtWidgets import QCheckBox
from PySide6.QtCore import QSize, Qt, QRectF, QPoint
from PySide6.QtGui import QPainter, QColor

class ToggleSwitch(QCheckBox):
    """Простой переключатель с настраиваемыми подсказками."""

    def __init__(self, tooltip_off: str = "Мужской", tooltip_on: str = "Женский", *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.tooltip_off = tooltip_off
        self.tooltip_on = tooltip_on
        self.setCursor(Qt.PointingHandCursor)
        self.setChecked(False)
        self.toggled.connect(self._update_tooltip)
        self._update_tooltip(self.isChecked())

    def _update_tooltip(self, checked: bool) -> None:
        """Обновить подсказку в зависимости от состояния."""
        self.setToolTip(self.tooltip_on if checked else self.tooltip_off)

    def sizeHint(self) -> QSize:
        """Минимальный рекомендуемый размер переключателя."""
        return QSize(50, 24)

    def hitButton(self, pos: QPoint) -> bool:
        """Делает кликабельной всю область виджета."""
        return True

    def paintEvent(self, event):
        """Отрисовать переключатель."""
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

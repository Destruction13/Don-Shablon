from __future__ import annotations

from PySide6.QtWidgets import QPushButton
from PySide6.QtCore import QPoint


class HoverButton(QPushButton):
    """QPushButton with radial highlight following the mouse."""

    def __init__(self, text: str = "", parent=None):
        super().__init__(text, parent)
        self._base_style = ""
        self._base_color = "#ffffff"
        self._highlight = "rgba(255,255,255,0.3)"
        self.setMouseTracking(True)

    def setup_theme(self, base_style: str, base_color: str, highlight: str = "rgba(255,255,255,0.3)") -> None:
        """Apply base style from theme."""
        self._base_style = base_style
        self._base_color = base_color
        self._highlight = highlight
        self.setStyleSheet(f"{base_style}background-color: {base_color};")

    def leaveEvent(self, event):
        self.setStyleSheet(f"{self._base_style}background-color: {self._base_color};")
        super().leaveEvent(event)

    def enterEvent(self, event):
        self._update_gradient(event.pos())
        super().enterEvent(event)

    def mouseMoveEvent(self, event):
        self._update_gradient(event.pos())
        super().mouseMoveEvent(event)

    def _update_gradient(self, pos: QPoint) -> None:
        if not self._base_style:
            return
        cx = pos.x() / max(1, self.width())
        cy = pos.y() / max(1, self.height())
        grad = (
            f"qradialgradient(cx:{cx:.2f}, cy:{cy:.2f}, radius:1, stop:0 {self._highlight}, stop:1 {self._base_color})"
        )
        self.setStyleSheet(f"{self._base_style}background-color: {grad};")

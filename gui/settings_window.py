from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel,
    QComboBox, QPushButton, QWidget
)

from logic.app_state import UIContext


class SettingsDialog(QDialog):
    """Simple settings dialog with extensible layout."""

    def __init__(self, ctx: UIContext, parent=None):
        super().__init__(parent)
        self.ctx = ctx
        self.setWindowTitle("Настройки")

        main_layout = QVBoxLayout(self)
        self.settings_frame = QWidget()
        self.settings_layout = QVBoxLayout(self.settings_frame)
        main_layout.addWidget(self.settings_frame)

        # OCR mode selector
        row = QHBoxLayout()
        row.addWidget(QLabel("OCR режим:"))
        self.ocr_mode_combo = QComboBox()
        self.ocr_mode_combo.addItems(["CPU", "GPU"])
        self.ocr_mode_combo.setCurrentText(ctx.ocr_mode)
        self.ocr_mode_combo.currentTextChanged.connect(self._on_mode_changed)
        row.addWidget(self.ocr_mode_combo)
        self.settings_layout.addLayout(row)

        ok_btn = QPushButton("OK")
        ok_btn.clicked.connect(self.accept)
        main_layout.addWidget(ok_btn)

    def _on_mode_changed(self, mode: str) -> None:
        self.ctx.ocr_mode = mode

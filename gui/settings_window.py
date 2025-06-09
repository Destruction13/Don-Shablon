from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel,
    QComboBox, QPushButton, QWidget, QCheckBox, QSlider
)
from PySide6.QtCore import Qt

from logic.app_state import UIContext
from gui.themes import THEME_QSS, apply_theme


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

        # theme selector
        row_theme = QHBoxLayout()
        row_theme.addWidget(QLabel("Тема:"))
        self.theme_combo = QComboBox()
        self.theme_combo.addItem("Стандартная")
        self.theme_combo.addItems(list(THEME_QSS.keys()))
        self.theme_combo.setCurrentText(ctx.current_theme_name)
        self.theme_combo.currentTextChanged.connect(self._on_theme_changed)
        row_theme.addWidget(self.theme_combo)
        self.settings_layout.addLayout(row_theme)

        # animations
        row_anim_enable = QHBoxLayout()
        self.anim_checkbox = QCheckBox("Включить анимации")
        self.anim_checkbox.setChecked(ctx.animations_enabled)
        self.anim_checkbox.stateChanged.connect(lambda val: setattr(ctx, "animations_enabled", bool(val)))
        row_anim_enable.addWidget(self.anim_checkbox)
        self.settings_layout.addLayout(row_anim_enable)

        row_anim_effect = QHBoxLayout()
        row_anim_effect.addWidget(QLabel("Эффект:"))
        self.anim_effect_combo = QComboBox()
        self.anim_effect_combo.addItems(["Glow", "Scale", "Pulse"])
        self.anim_effect_combo.setCurrentText(ctx.animation_effect)
        self.anim_effect_combo.currentTextChanged.connect(lambda val: setattr(ctx, "animation_effect", val))
        row_anim_effect.addWidget(self.anim_effect_combo)
        self.settings_layout.addLayout(row_anim_effect)

        row_intensity = QHBoxLayout()
        row_intensity.addWidget(QLabel("Интенсивность:"))
        self.anim_slider = QSlider(Qt.Horizontal)
        self.anim_slider.setRange(0, 100)
        self.anim_slider.setValue(ctx.animation_intensity)
        self.anim_slider.valueChanged.connect(lambda val: setattr(ctx, "animation_intensity", val))
        row_intensity.addWidget(self.anim_slider)
        self.settings_layout.addLayout(row_intensity)

        ok_btn = QPushButton("OK")
        ok_btn.clicked.connect(self.accept)
        main_layout.addWidget(ok_btn)

    def _on_mode_changed(self, mode: str) -> None:
        self.ctx.ocr_mode = mode

    def _on_theme_changed(self, name: str) -> None:
        self.ctx.current_theme_name = name
        if self.ctx.app:
            apply_theme(self.ctx.app, name)

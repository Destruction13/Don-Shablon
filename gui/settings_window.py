import os
from PySide6.QtWidgets import (
    QDialog,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QComboBox,
    QPushButton,
    QWidget,
    QCheckBox,
    QSlider,
    QToolButton,
    QFileDialog,
    QMessageBox,
    QGroupBox,
    QFormLayout,
)
from PySide6.QtCore import Qt

from logic.app_state import UIContext
from gui.themes import THEME_QSS, apply_theme
from gui import ToggleSwitch


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
        self.anim_checkbox.stateChanged.connect(
            lambda val: setattr(ctx, "animations_enabled", bool(val))
        )
        row_anim_enable.addWidget(self.anim_checkbox)
        self.settings_layout.addLayout(row_anim_enable)

        row_anim_effect = QHBoxLayout()
        row_anim_effect.addWidget(QLabel("Эффект:"))
        self.anim_effect_combo = QComboBox()
        self.anim_effect_combo.addItems(
            [
                "Glow",
                "Scale",
                "Pulse",
                "Shimmer",
                "Shadow Slide",
                "ColorChange",
                "ColorInvert",
                "Opacity",
                "ShadowAppear",
                "SlideOffset",
                "ProgressFill",
            ]
        )
        self.anim_effect_combo.setCurrentText(ctx.animation_effect)
        self.anim_effect_combo.currentTextChanged.connect(self._on_effect_changed)
        row_anim_effect.addWidget(self.anim_effect_combo)
        self.settings_layout.addLayout(row_anim_effect)

        row_intensity = QHBoxLayout()
        self.intensity_label = QLabel("Интенсивность:")
        row_intensity.addWidget(self.intensity_label)
        self.anim_slider = QSlider(Qt.Horizontal)
        self.anim_slider.setRange(0, 100)
        self.anim_slider.setValue(ctx.animation_intensity)
        self.anim_slider.valueChanged.connect(
            lambda val: setattr(ctx, "animation_intensity", val)
        )
        row_intensity.addWidget(self.anim_slider)
        self.settings_layout.addLayout(row_intensity)
        self._on_effect_changed(ctx.animation_effect)

        row_music = QHBoxLayout()
        row_music.addWidget(QLabel("Музыка:"))
        self.music_label = QLabel(os.path.basename(ctx.music_dir))
        row_music.addWidget(self.music_label)
        self.music_btn = QToolButton()
        self.music_btn.setText("📂")
        self.music_btn.clicked.connect(self.choose_music_dir)
        row_music.addWidget(self.music_btn)
        self.settings_layout.addLayout(row_music)

        # Translator selector
        row_tr = QHBoxLayout()
        row_tr.addWidget(QLabel("Переводчик:"))
        self.translator_combo = QComboBox()
        self.translator_combo.addItems(["Google", "DeepL"])
        self.translator_combo.setCurrentText(ctx.translator)
        self.translator_combo.currentTextChanged.connect(
            lambda val: setattr(ctx, "translator", val)
        )
        row_tr.addWidget(self.translator_combo)
        self.settings_layout.addLayout(row_tr)

        row_help = QHBoxLayout()
        self.help_checkbox = QCheckBox("Показывать подсказки")
        self.help_checkbox.setChecked(ctx.show_help_icons)
        self.help_checkbox.stateChanged.connect(
            lambda val: setattr(ctx, "show_help_icons", bool(val))
        )
        row_help.addWidget(self.help_checkbox)
        self.settings_layout.addLayout(row_help)

        row_key = QHBoxLayout()
        self.key_btn = QPushButton("API DeepL")
        self.key_btn.clicked.connect(self.ask_deepl_key)
        row_key.addWidget(self.key_btn)
        self.key_label = QLabel("Сохранен" if ctx.deepl_api_key else "Не указан")
        row_key.addWidget(self.key_label)
        self.settings_layout.addLayout(row_key)

        save_box = QGroupBox("Сохранять")
        save_layout = QFormLayout(save_box)
        self.save_theme_sw = ToggleSwitch()
        self.save_theme_sw.setChecked(ctx.settings.save_theme)
        save_layout.addRow("Тему", self.save_theme_sw)
        self.save_ocr_sw = ToggleSwitch()
        self.save_ocr_sw.setChecked(ctx.settings.save_ocr_mode)
        save_layout.addRow("OCR (GPU/CPU)", self.save_ocr_sw)
        self.save_anim_sw = ToggleSwitch()
        self.save_anim_sw.setChecked(ctx.settings.save_animation_effect)
        save_layout.addRow("Эффект анимации", self.save_anim_sw)
        self.save_auto_copy_sw = ToggleSwitch()
        self.save_auto_copy_sw.setChecked(ctx.settings.save_auto_copy)
        save_layout.addRow("Автокопирование", self.save_auto_copy_sw)
        self.save_auto_generate_sw = ToggleSwitch()
        self.save_auto_generate_sw.setChecked(ctx.settings.save_auto_generate)
        save_layout.addRow("Автогенерацию", self.save_auto_generate_sw)
        self.save_auto_report_sw = ToggleSwitch()
        self.save_auto_report_sw.setChecked(ctx.settings.save_auto_report)
        save_layout.addRow("Авто-отчёт", self.save_auto_report_sw)
        self.settings_layout.addWidget(save_box)

        save_btn = QPushButton("Сохранить")
        save_btn.clicked.connect(self.save_and_close)
        main_layout.addWidget(save_btn)

    def _on_mode_changed(self, mode: str) -> None:
        self.ctx.ocr_mode = mode

    def _on_theme_changed(self, name: str) -> None:
        self.ctx.current_theme_name = name
        if self.ctx.app:
            apply_theme(self.ctx.app, name, self.ctx)

    def _on_effect_changed(self, name: str) -> None:
        self.ctx.animation_effect = name
        visible = name not in {
            "Scale",
            "ColorInvert",
            "ProgressFill",
        }
        self.anim_slider.setVisible(visible)
        self.intensity_label.setVisible(visible)

    def choose_music_dir(self) -> None:
        new_dir = QFileDialog.getExistingDirectory(
            self, "Выбрать папку с музыкой", self.ctx.music_dir
        )
        if new_dir:
            self.ctx.music_dir = new_dir
            self.music_label.setText(os.path.basename(new_dir) or new_dir)
            self.ctx.refresh_music_files()
            if self.ctx.music_files:
                QMessageBox.information(self, "Музыка", "Список обновлён")
            else:
                QMessageBox.information(self, "Музыка", "Треков не найдено")

    def ask_deepl_key(self) -> None:
        from PySide6.QtWidgets import QInputDialog

        key, ok = QInputDialog.getText(
            self, "DeepL API", "Введите ключ", text=self.ctx.deepl_api_key
        )
        if ok:
            self.ctx.deepl_api_key = key
            self.key_label.setText("Сохранен" if key else "Не указан")

    def save_and_close(self) -> None:
        """Persist selected settings and close the dialog."""
        self.ctx.settings.theme = self.ctx.current_theme_name
        self.ctx.settings.ocr_mode = self.ctx.ocr_mode
        self.ctx.settings.animation_effect = self.ctx.animation_effect
        self.ctx.settings.auto_copy = self.ctx.auto_copy_enabled
        self.ctx.settings.auto_generate = self.ctx.auto_generate_after_autofill
        self.ctx.settings.auto_report = self.ctx.auto_report_enabled
        self.ctx.settings.deepl_api_key = self.ctx.deepl_api_key
        self.ctx.settings.translator = self.ctx.translator
        self.ctx.settings.show_help_icons = self.ctx.show_help_icons

        self.ctx.settings.save_theme = self.save_theme_sw.isChecked()
        self.ctx.settings.save_ocr_mode = self.save_ocr_sw.isChecked()
        self.ctx.settings.save_animation_effect = self.save_anim_sw.isChecked()
        self.ctx.settings.save_auto_copy = self.save_auto_copy_sw.isChecked()
        self.ctx.settings.save_auto_generate = self.save_auto_generate_sw.isChecked()
        self.ctx.settings.save_auto_report = self.save_auto_report_sw.isChecked()
        self.ctx.settings.save()
        self.accept()

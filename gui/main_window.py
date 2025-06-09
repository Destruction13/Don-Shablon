from PySide6.QtWidgets import (
    QMainWindow, QWidget, QLabel, QVBoxLayout, QHBoxLayout, QPushButton,
    QTextEdit, QComboBox, QMessageBox, QToolButton, QFormLayout, QCheckBox,
    QScrollArea, QSpinBox, QGroupBox
)
from PySide6.QtGui import QPixmap
from PySide6.QtCore import Qt
import os
import pygame

from logic.app_state import UIContext
from logic.generator import update_fields, generate_message, on_link_change
from logic.utils import toggle_music, copy_generated_text, translate_to_english
from gui.themes import apply_theme
from gui.animations import setup_animation
from gui.music_dialog import MusicDialog


class MainWindow(QMainWindow):
    def __init__(self, ctx: UIContext):
        super().__init__()
        self.ctx = ctx
        ctx.window = self
        pygame.init()
        try:
            pygame.mixer.init()
            music_path = ctx.music_path
            if music_path and os.path.exists(music_path):
                pygame.mixer.music.load(music_path)
        except Exception as e:
            print(f"[ERROR] Failed to init mixer: {e}")
        self.setWindowTitle("Генератор шаблонов встреч")
        self.resize(800, 600)
        if ctx.app:
            apply_theme(ctx.app, ctx.current_theme_name)

        self.bg_label = QLabel(self)
        self.bg_label.setScaledContents(True)
        self.bg_label.lower()

        central = QWidget()
        self.setCentralWidget(central)
        self.main_layout = QVBoxLayout(central)

        header = QHBoxLayout()
        header.addStretch()
        self.settings_btn = QToolButton()
        self.settings_btn.setText("⚙")
        self.settings_btn.clicked.connect(self.show_settings_dialog)
        self.music_btn = QToolButton()
        self.music_btn.setText("🎵")
        self.music_btn.clicked.connect(self.show_music_dialog)
        setup_animation(self.settings_btn, ctx)
        setup_animation(self.music_btn, ctx)
        header.addWidget(self.music_btn)
        header.addWidget(self.settings_btn)
        self.main_layout.addLayout(header)

        # meeting type selector
        self.type_combo = QComboBox()
        self.type_combo.addItems(["Актуализация", "Обмен", "Организация встречи"])
        self.main_layout.addWidget(self.type_combo)
        ctx.type_combo = self.type_combo
        self.type_combo.currentTextChanged.connect(lambda _: update_fields(ctx))
        self.type_combo.currentTextChanged.connect(self.on_type_changed)
        setup_animation(self.type_combo, ctx)

        # checkbox + group for regular meeting configuration
        self.regular_cb = QCheckBox("Организация регулярной встречи")
        self.regular_cb.stateChanged.connect(self.toggle_regular_fields)
        setup_animation(self.regular_cb, ctx)
        self.main_layout.addWidget(self.regular_cb)

        self.regular_group = QGroupBox()
        self.regular_group.setTitle("")
        setup_animation(self.regular_group, ctx)

        self.regular_layout = QFormLayout(self.regular_group)
        self.reg_spin = QSpinBox()
        self.reg_spin.setRange(1, 10)
        self.reg_period_combo = QComboBox()
        self.reg_period_combo.addItems(["неделю", "месяц"])
        self.reg_day_combo = QComboBox()
        self.reg_day_combo.addItems([
            "понедельник",
            "вторник",
            "среду",
            "четверг",
            "пятницу",
            "субботу",
            "воскресенье",
        ])
        self.regular_layout.addRow(QLabel("Количество:"), self.reg_spin)
        self.regular_layout.addRow(QLabel("Период:"), self.reg_period_combo)
        self.regular_layout.addRow(QLabel("День недели:"), self.reg_day_combo)
        self.regular_group.setVisible(False)
        self.main_layout.addWidget(self.regular_group)
        ctx.regular_count = self.reg_spin
        ctx.regular_period = self.reg_period_combo
        ctx.regular_day = self.reg_day_combo

        # fields frame inside scroll area
        self.scroll_area = QScrollArea()
        self.scroll_area.setObjectName("fieldsArea")
        self.scroll_area.setWidgetResizable(True)
        self.fields_widget = QWidget()
        self.fields_widget.setObjectName("fieldsWidget")
        self.fields_layout = QFormLayout(self.fields_widget)
        self.scroll_area.setWidget(self.fields_widget)
        self.scroll_area.setStyleSheet(
            "QScrollArea, QScrollArea > QWidget > QWidget { background: transparent; border: none; }"
        )
        self.main_layout.addWidget(self.scroll_area)
        ctx.fields_layout = self.fields_layout

        # buttons
        action_row = QHBoxLayout()
        generate_btn = QPushButton("Сгенерировать")
        generate_btn.clicked.connect(lambda: generate_message(ctx))
        action_row.addWidget(generate_btn)
        self.main_layout.addLayout(action_row)
        setup_animation(generate_btn, ctx)

        clipboard_row = QHBoxLayout()
        cv_btn = QPushButton("📥 Из буфера")
        cv_btn.setObjectName("pasteButton")
        cv_btn.setFixedHeight(60)
        cv_btn.clicked.connect(self.handle_clipboard_ocr)
        clipboard_row.addWidget(cv_btn)
        clipboard_row.addStretch()
        self.main_layout.addLayout(clipboard_row)
        setup_animation(cv_btn, ctx)

        self.asya_btn = QPushButton("ЛС")
        self.asya_btn.setObjectName("lsButton")
        self.asya_btn.setCheckable(True)
        self.asya_btn.toggled.connect(self.toggle_ls)
        setup_animation(self.asya_btn, ctx)
        self.asya_mode_btn = QPushButton("Ася+")
        self.asya_mode_btn.setObjectName("asyaButton")
        self.asya_mode_btn.setCheckable(True)
        self.asya_mode_btn.toggled.connect(lambda val: setattr(ctx, 'asya_mode', val))
        setup_animation(self.asya_mode_btn, ctx)
        ctx.btn_ls = self.asya_btn
        ctx.btn_asya_plus = self.asya_mode_btn

        self.copy_btn = QToolButton()
        self.copy_btn.setText("📋")
        self.copy_btn.setToolTip("Скопировать текст")
        self.copy_btn.clicked.connect(lambda: copy_generated_text(ctx))
        self.trans_btn = QPushButton("🌐 EN")
        self.trans_btn.clicked.connect(lambda: translate_to_english(ctx))
        setup_animation(self.copy_btn, ctx)
        setup_animation(self.trans_btn, ctx)

        output_container = QVBoxLayout()
        self.auto_copy_cb = QCheckBox("📋 Авто-копирование")
        self.auto_copy_cb.stateChanged.connect(lambda val: setattr(ctx, "auto_copy_enabled", bool(val)))
        top_controls = QHBoxLayout()
        top_controls.addStretch()
        top_controls.addWidget(self.auto_copy_cb)
        top_controls.addWidget(self.copy_btn)
        top_controls.addWidget(self.trans_btn)
        output_container.addLayout(top_controls)
        self.output_text = QTextEdit()
        output_container.addWidget(self.output_text)
        self.main_layout.addLayout(output_container)
        ctx.output_text = self.output_text

        update_fields(ctx)
        self.on_type_changed()

    def on_theme_changed(self, name):
        self.ctx.current_theme_name = name
        self.update_background()

    def on_type_changed(self, *_):
        typ = self.type_combo.currentText()
        is_org = typ == "Организация встречи"
        self.regular_cb.setVisible(is_org)
        if not is_org:
            self.regular_group.setVisible(False)
            self.regular_cb.setChecked(False)
        lab = self.ctx.labels.get("client_name")
        if lab:
            if is_org:
                lab.setText("🧑\u200d💼 Имя и фамилия заказчика (в род. падеже):")
            else:
                lab.setText("🧑\u200d💼 Имя заказчика:")
        lab2 = self.ctx.labels.get("meeting_name")
        if lab2:
            lab2.setText("📝 Название встречи:")

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self.update_background()

    def update_background(self):
        if not self.ctx.bg_path:
            return
        pix = QPixmap(self.ctx.bg_path)
        if not pix.isNull():
            self.bg_label.setGeometry(self.rect())
            self.bg_label.setPixmap(pix.scaled(self.size(), Qt.KeepAspectRatioByExpanding, Qt.SmoothTransformation))
            self.bg_label.lower()

    def show_ls_dialog(self):
        from PySide6.QtWidgets import (
            QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QRadioButton, QPushButton
        )
        dlg = QDialog(self)
        dlg.setWindowTitle("Личный ассистент")
        v = QVBoxLayout(dlg)
        name_edit = QLineEdit()
        male = QRadioButton("Мужской")
        female = QRadioButton("Женский")
        male.setChecked(True)
        v.addWidget(QLabel("Имя ассистента:"))
        v.addWidget(name_edit)
        h = QHBoxLayout()
        h.addWidget(male)
        h.addWidget(female)
        v.addLayout(h)
        ok_btn = QPushButton("OK")
        v.addWidget(ok_btn)

        result = {"accepted": False}

        def accept():
            name = name_edit.text().strip()
            if not name:
                QMessageBox.warning(dlg, "Ошибка", "Введите имя")
                return
            self.ctx.user_name = name
            self.ctx.user_gender = "м" if male.isChecked() else "ж"
            self.ctx.ls_saved = True
            result["accepted"] = True
            dlg.accept()

        ok_btn.clicked.connect(accept)
        dlg.exec()
        return result["accepted"]

    def toggle_ls(self, checked):
        if checked and not self.ctx.ls_saved:
            if not self.show_ls_dialog():
                self.asya_btn.setChecked(False)
                return
        self.ctx.ls_active = checked

    def handle_clipboard_ocr(self):
        from ocr_unified import recognize_from_clipboard
        recognize_from_clipboard(self.ctx)

    def show_settings_dialog(self):
        from gui.settings_window import SettingsDialog
        dlg = SettingsDialog(self.ctx, self)
        dlg.exec()

    def show_music_dialog(self):
        dlg = MusicDialog(self.ctx, self)
        dlg.exec()

    def toggle_regular_fields(self, checked: bool):
        self.ctx.regular_meeting_enabled = bool(checked)
        self.regular_group.setVisible(bool(checked))



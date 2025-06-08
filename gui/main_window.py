from PySide6.QtWidgets import (
    QMainWindow,
    QWidget,
    QLabel,
    QVBoxLayout,
    QHBoxLayout,
    QPushButton,
    QTextEdit,
    QComboBox,
    QMessageBox,
    QToolButton,
)
from PySide6.QtGui import QPixmap
from PySide6.QtCore import Qt
import os
import pygame

from logic.app_state import UIContext
from logic.generator import update_fields, generate_message, on_link_change
from logic.utils import toggle_music, copy_generated_text, translate_to_english


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

        self.bg_label = QLabel(self)
        self.bg_label.setScaledContents(True)
        self.bg_label.lower()

        central = QWidget()
        self.setCentralWidget(central)
        self.main_layout = QVBoxLayout(central)

        header = QHBoxLayout()
        # theme selector (placeholder)
        self.theme_combo = QComboBox()
        self.theme_combo.addItems(["Светлая", "Тёмная"])
        self.theme_combo.currentTextChanged.connect(self.on_theme_changed)
        header.addWidget(self.theme_combo)
        header.addStretch()
        self.type_combo.currentTextChanged.connect(lambda _: update_fields(ctx))
        self.asya_btn = QPushButton("ЛС")
        self.asya_mode_btn = QPushButton("Ася +")
        self.asya_mode_btn.toggled.connect(lambda val: setattr(ctx, "asya_mode", val))
        copy_btn = QPushButton("Скопировать текст")
        music_btn = QPushButton("🎵")
        music_btn.clicked.connect(lambda: toggle_music(music_btn, ctx))
        trans_btn = QPushButton("EN")
        cv_btn = QPushButton("📋 Из буфера")
        for w in [
            generate_btn,
            self.asya_btn,
            self.asya_mode_btn,
            music_btn,
            trans_btn,
            cv_btn,
        ]:
        self.main_layout.addWidget(copy_btn)
    def on_theme_changed(self, name):
        self.ctx.current_theme_name = name
        self.update_background()

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self.update_background()

    def update_background(self):
        if not self.ctx.bg_path:
            return
        pix = QPixmap(self.ctx.bg_path)
        if not pix.isNull():
            self.bg_label.setGeometry(self.rect())
            self.bg_label.setPixmap(
                pix.scaled(
                    self.size(), Qt.KeepAspectRatioByExpanding, Qt.SmoothTransformation
                )
            )
            self.bg_label.lower()

            QLabel,
            QLineEdit,
            QRadioButton,
            QPushButton,

        ok_btn = QPushButton("OK")



        # fields frame
        self.fields_widget = QWidget()
        self.fields_layout = QVBoxLayout(self.fields_widget)
        self.main_layout.addWidget(self.fields_widget)

        trans_btn.clicked.connect(lambda: translate_to_english(ctx))
        ctx.register_button(trans_btn)
        cv_btn = HoverButton("📋 Из буфера")
        cv_btn.setToolTip("Распознать текст из буфера")
        cv_btn.clicked.connect(self.handle_clipboard_ocr)
        ctx.register_button(cv_btn)
        for w in [generate_btn, self.asya_btn, self.asya_mode_btn]:
            action_row.addWidget(w)
        self.main_layout.addLayout(action_row)
        self.main_layout.addWidget(cv_btn)

        text_controls = QHBoxLayout()
        text_controls.addStretch()
        text_controls.addWidget(trans_btn)
        text_controls.addWidget(copy_btn)
        self.main_layout.addLayout(text_controls)

        # output
        self.output_text = QTextEdit()
        self.main_layout.addWidget(self.output_text)
        ctx.output_text = self.output_text

        update_fields(ctx)
        ctx.apply_theme()

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
            QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QRadioButton
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
        ok_btn = HoverButton("OK")
        self.ctx.register_button(ok_btn)
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



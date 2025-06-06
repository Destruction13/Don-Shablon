from PySide6.QtWidgets import (
    QMainWindow, QWidget, QLabel, QVBoxLayout, QHBoxLayout, QPushButton,
    QTextEdit, QComboBox
)
from PySide6.QtGui import QPixmap
from PySide6.QtCore import Qt
import random
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

        # theme selector (placeholder)
        self.theme_combo = QComboBox()
        self.theme_combo.addItems(["Светлая", "Тёмная"])
        self.theme_combo.currentTextChanged.connect(self.on_theme_changed)
        self.main_layout.addWidget(self.theme_combo)

        # meeting type selector
        self.type_combo = QComboBox()
        self.type_combo.addItems(["Актуализация", "Обмен", "Разовая встреча"])
        self.main_layout.addWidget(self.type_combo)
        ctx.type_combo = self.type_combo
        self.type_combo.currentTextChanged.connect(lambda _: update_fields(ctx))

        # fields frame
        self.fields_widget = QWidget()
        self.fields_layout = QVBoxLayout(self.fields_widget)
        self.main_layout.addWidget(self.fields_widget)
        ctx.fields_layout = self.fields_layout

        # buttons
        action_row = QHBoxLayout()
        generate_btn = QPushButton("Сгенерировать")
        generate_btn.clicked.connect(lambda: generate_message(ctx))
        self.asya_btn = QPushButton("ЛС")
        self.asya_btn.clicked.connect(self.show_ls_dialog)
        self.asya_mode_btn = QPushButton("Ася +")
        self.asya_mode_btn.setCheckable(True)
        self.asya_mode_btn.toggled.connect(lambda val: setattr(ctx, 'asya_mode', val))
        copy_btn = QPushButton("Скопировать текст")
        copy_btn.clicked.connect(lambda: copy_generated_text(ctx))
        music_btn = QPushButton("🎵")
        music_btn.clicked.connect(lambda: toggle_music(music_btn, ctx))
        trans_btn = QPushButton("EN")
        trans_btn.clicked.connect(lambda: translate_to_english(ctx))
        cv_btn = QPushButton("📋 Из буфера")
        from logic.ocr_qt import import_from_clipboard_image
        cv_btn.clicked.connect(lambda: import_from_clipboard_image(ctx))
        for w in [generate_btn, self.asya_btn, self.asya_mode_btn, music_btn, trans_btn, cv_btn]:
            action_row.addWidget(w)
        self.main_layout.addLayout(action_row)
        self.main_layout.addWidget(copy_btn)

        # output
        self.output_text = QTextEdit()
        self.main_layout.addWidget(self.output_text)
        ctx.output_text = self.output_text

        update_fields(ctx)

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
            self.bg_label.setPixmap(pix.scaled(self.size(), Qt.KeepAspectRatioByExpanding, Qt.SmoothTransformation))
            self.bg_label.lower()

    def show_ls_dialog(self):
        from PySide6.QtWidgets import QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QRadioButton, QPushButton
        dlg = QDialog(self)
        dlg.setWindowTitle("Выбор имени")
        v = QVBoxLayout(dlg)
        name_edit = QLineEdit()
        male = QRadioButton("Мужской")
        female = QRadioButton("Женский")
        female.setChecked(True)
        v.addWidget(QLabel("Имя:"))
        v.addWidget(name_edit)
        h = QHBoxLayout()
        h.addWidget(male)
        h.addWidget(female)
        v.addLayout(h)
        ok_btn = QPushButton("OK")
        v.addWidget(ok_btn)

        def accept():
            name = name_edit.text().strip()
            males = ["Алексей", "Дмитрий", "Иван", "Сергей"]
            females = ["Анастасия", "Мария", "Елена", "Ольга"]
            if not name:
                name = random.choice(males if male.isChecked() else females)
            if "name" in self.ctx.fields:
                self.ctx.fields["name"].setText(name)
            dlg.accept()

        ok_btn.clicked.connect(accept)
        dlg.exec()


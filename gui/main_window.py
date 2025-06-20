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
    QFormLayout,
    QScrollArea,
    QSpinBox,
    QGroupBox,
    QSizePolicy,
    QSlider,
    QCheckBox,
)
from PySide6.QtGui import QPixmap
from PySide6.QtCore import Qt, QTimer

from gui.tasks_window import TasksDialog
import logging
import os
import pygame

from logic.app_state import UIContext
from logic.generator import (
    update_fields,
    generate_message,
    add_help_icon,
    label_with_icon,
    HELP_TEXTS,
)
from logic.utils import copy_generated_text, copy_report_text, translate_to_english
from gui.themes import apply_theme
from gui.animations import setup_animation
from gui import ToggleSwitch


class MainWindow(QMainWindow):
    """Главное окно генератора шаблонов."""
    def __init__(self, ctx: UIContext):
        """Создать главное окно и настроить элементы интерфейса."""
        super().__init__()
        self.ctx = ctx
        ctx.window = self
        pygame.init()
        try:
            pygame.mixer.init()
            music_path = ctx.music_path
            if music_path and os.path.exists(music_path):
                pygame.mixer.music.load(music_path)
                pygame.mixer.music.set_volume(ctx.music_volume / 100)
        except Exception as e:
            logging.error("Failed to init mixer: %s", e)
        self.bg_label = QLabel(self)
        self.bg_label.setScaledContents(True)
        self.bg_label.lower()

        self.setWindowTitle("Генератор шаблонов встреч")
        self.resize(1100, 1000)
        if ctx.app:
            apply_theme(ctx.app, ctx.current_theme_name, ctx)

        central = QWidget()
        self.setCentralWidget(central)
        self.main_layout = QVBoxLayout(central)

        header = QHBoxLayout()
        header.addStretch()
        self.settings_btn = QToolButton()
        self.settings_btn.setText("⚙")
        self.settings_btn.clicked.connect(self.show_settings_dialog)

        self.tasks_btn = QToolButton()
        self.tasks_btn.setText("📝")
        self.tasks_btn.clicked.connect(self.show_tasks_dialog)

        self.prev_btn = QToolButton()
        self.prev_btn.setText("⏮")
        self.prev_btn.clicked.connect(self.play_prev_track)

        self.play_btn = QToolButton()
        self.play_btn.setText("▶️")
        self.play_btn.clicked.connect(self.handle_play_button)

        self.next_btn = QToolButton()
        self.next_btn.setText("⏭")
        self.next_btn.clicked.connect(self.play_next_track)

        self.volume_btn = QToolButton()
        self.volume_btn.setText("🔊")
        self.volume_btn.clicked.connect(self.toggle_volume_slider)

        self.volume_slider = QSlider(Qt.Horizontal)
        self.volume_slider.setRange(0, 100)
        self.volume_slider.setFixedWidth(100)
        self.volume_slider.setValue(ctx.music_volume)
        self.volume_slider.valueChanged.connect(self.change_volume)
        self.volume_slider.setVisible(False)

        self.track_timer = QTimer(self)
        self.track_timer.setInterval(1000)
        self.track_timer.timeout.connect(self.check_music)

        for btn in (
            self.prev_btn,
            self.play_btn,
            self.next_btn,
            self.volume_btn,
            self.tasks_btn,
            self.settings_btn,
        ):
            setup_animation(btn, ctx)

        header.addWidget(self.prev_btn)
        header.addWidget(self.play_btn)
        header.addWidget(self.next_btn)
        header.addWidget(self.volume_btn)
        header.addWidget(self.volume_slider)
        header.addWidget(self.tasks_btn)
        header.addWidget(self.settings_btn)
        self.main_layout.addLayout(header)

        self.type_combo = QComboBox()
        self.type_combo.addItems(
            [
                "Актуализация",
                "Обмен",
                "Организация встречи",
                "Другое",
            ]
        )
        self.main_layout.addWidget(self.type_combo)
        ctx.type_combo = self.type_combo
        self.type_combo.currentTextChanged.connect(lambda _: update_fields(ctx))
        self.type_combo.currentTextChanged.connect(self.on_type_changed)
        setup_animation(self.type_combo, ctx)

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
        self.reg_day_combo.addItems(
            ["понедельник", "вторник", "среда", "четверг", "пятница"]
        )
        lab_count = label_with_icon("Количество:")
        lab_count_w = add_help_icon(lab_count, HELP_TEXTS["reg_count"], ctx)
        self.regular_layout.addRow(lab_count_w, self.reg_spin)

        lab_period = label_with_icon("Период:")
        lab_period_w = add_help_icon(lab_period, HELP_TEXTS["reg_period"], ctx)
        self.regular_layout.addRow(lab_period_w, self.reg_period_combo)

        lab_day = label_with_icon("День недели:")
        lab_day_w = add_help_icon(lab_day, HELP_TEXTS["reg_day"], ctx)
        self.regular_layout.addRow(lab_day_w, self.reg_day_combo)
        self.regular_group.setVisible(False)
        self.main_layout.addWidget(self.regular_group)
        ctx.regular_count = self.reg_spin
        ctx.regular_period = self.reg_period_combo
        ctx.regular_day = self.reg_day_combo

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

        clipboard_row = QHBoxLayout()
        from gui.rainbow_button import RainbowButton

        cv_btn = RainbowButton("Автозаполнение полей")
        cv_btn.setObjectName("pasteButton")
        cv_btn.clicked.connect(self.handle_clipboard_ocr)
        cv_btn.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        clipboard_row.addWidget(cv_btn)
        self.cv_btn = cv_btn
        clipboard_row.setContentsMargins(0, 0, 0, 10)
        self.main_layout.addLayout(clipboard_row)
        setup_animation(cv_btn, ctx)

        action_row = QHBoxLayout()
        generate_btn = QPushButton("Сгенерировать")
        generate_btn.clicked.connect(lambda: generate_message(ctx))
        generate_btn.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        action_row.addWidget(generate_btn)
        self.generate_btn = generate_btn
        self.main_layout.addLayout(action_row)
        setup_animation(generate_btn, ctx)

        cv_btn.setFixedHeight(int(generate_btn.sizeHint().height() * 1.5))

        self.ls_sw = ToggleSwitch(tooltip_off="Выкл", tooltip_on="Вкл")
        self.ls_sw.setObjectName("lsButton")
        self.ls_sw.setChecked(ctx.ls_active)
        self.ls_sw.toggled.connect(self.toggle_ls)
        setup_animation(self.ls_sw, ctx)

        self.asya_mode_sw = ToggleSwitch(tooltip_off="Выкл", tooltip_on="Вкл")
        self.asya_mode_sw.setObjectName("asyaButton")
        self.asya_mode_sw.setChecked(ctx.asya_mode)
        self.asya_mode_sw.toggled.connect(lambda val: setattr(ctx, "asya_mode", val))
        setup_animation(self.asya_mode_sw, ctx)

        ctx.btn_ls = self.ls_sw
        ctx.btn_asya_plus = self.asya_mode_sw

        self.copy_btn = QToolButton()
        self.copy_btn.setText("📋")
        self.copy_btn.setToolTip("Скопировать текст")
        self.copy_btn.clicked.connect(lambda: copy_generated_text(ctx))
        self.trans_btn = QPushButton("🌐 EN")
        self.trans_btn.clicked.connect(lambda: translate_to_english(ctx))
        setup_animation(self.copy_btn, ctx)
        setup_animation(self.trans_btn, ctx)

        output_container = QVBoxLayout()
        top_controls = QHBoxLayout()
        top_controls.addWidget(QLabel("ЛС"))
        top_controls.addWidget(self.ls_sw)
        top_controls.addSpacing(15)
        top_controls.addWidget(QLabel("Ася+"))
        top_controls.addWidget(self.asya_mode_sw)
        top_controls.addSpacing(15)

        self.auto_copy_sw = ToggleSwitch(tooltip_off="Выкл", tooltip_on="Вкл")
        self.auto_copy_sw.setChecked(ctx.auto_copy_enabled)
        self.auto_copy_sw.toggled.connect(
            lambda val: setattr(ctx, "auto_copy_enabled", bool(val))
        )
        self.auto_gen_sw = ToggleSwitch(tooltip_off="Выкл", tooltip_on="Вкл")
        self.auto_gen_sw.setChecked(ctx.auto_generate_after_autofill)
        self.auto_gen_sw.toggled.connect(
            lambda val: setattr(ctx, "auto_generate_after_autofill", bool(val))
        )
        self.auto_report_sw = ToggleSwitch(tooltip_off="Выкл", tooltip_on="Вкл")
        self.auto_report_sw.setChecked(ctx.auto_report_enabled)
        self.auto_report_sw.toggled.connect(self.toggle_auto_report)

        top_controls.addWidget(QLabel("Авто-копирование"))
        top_controls.addWidget(self.auto_copy_sw)
        top_controls.addSpacing(15)
        top_controls.addWidget(QLabel("Автогенерация после автозаполнения"))
        top_controls.addWidget(self.auto_gen_sw)
        top_controls.addSpacing(15)
        top_controls.addWidget(QLabel("Авто-отчёт"))
        top_controls.addWidget(self.auto_report_sw)
        top_controls.addStretch()
        top_controls.addWidget(self.copy_btn)
        top_controls.addWidget(self.trans_btn)
        output_container.addLayout(top_controls)
        self.output_text = QTextEdit()
        output_container.addWidget(self.output_text)

        report_box = QVBoxLayout()
        report_top = QHBoxLayout()
        report_top.addStretch()
        self.report_copy_btn = QToolButton()
        self.report_copy_btn.setText("📋")
        self.report_copy_btn.setToolTip("Скопировать авто-отчёт")
        self.report_copy_btn.clicked.connect(lambda: copy_report_text(ctx))
        setup_animation(self.report_copy_btn, ctx)
        report_top.addWidget(self.report_copy_btn)
        report_box.addLayout(report_top)
        self.report_text = QTextEdit()
        report_box.addWidget(self.report_text)
        self.report_block = QWidget()
        self.report_block.setLayout(report_box)
        self.report_block.setVisible(ctx.auto_report_enabled)
        output_container.addWidget(self.report_block)
        self.main_layout.addLayout(output_container)
        ctx.output_text = self.output_text
        ctx.report_text = self.report_text

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
        if hasattr(self, "cv_btn"):
            self.cv_btn.setVisible(typ != "Другое")
        if hasattr(self, "generate_btn"):
            self.generate_btn.setVisible(typ != "Другое")
        lab = self.ctx.labels.get("client_name")
        if lab:
            if is_org:
                lab.setText("🧑\u200d💼 Имя и фамилия заказчика (в род. падеже):")
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
            self.bg_label.setPixmap(
                pix.scaled(
                    self.size(), Qt.KeepAspectRatioByExpanding, Qt.SmoothTransformation
                )
            )
            self.bg_label.lower()

    def show_ls_dialog(self):
        """Показать диалог настройки личного ассистента."""
        from PySide6.QtWidgets import (
            QDialog,
            QVBoxLayout,
            QHBoxLayout,
            QLabel,
            QLineEdit,
            QRadioButton,
            QPushButton,
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
                self.ls_sw.setChecked(False)
                return
        self.ctx.ls_active = checked

    def handle_clipboard_ocr(self):
        from logic.ocr_paddle import recognize_from_clipboard

        recognize_from_clipboard(self.ctx)

    def show_settings_dialog(self):
        from gui.settings_window import SettingsDialog

        dlg = SettingsDialog(self.ctx, self)
        dlg.exec()

    def show_tasks_dialog(self):
        dlg = TasksDialog(self.ctx, self.ctx.task_manager, self)
        dlg.exec()

    def handle_play_button(self):
        ctx = self.ctx
        if not ctx.music_state["playing"]:
            if not ctx.music_files:
                QMessageBox.information(self, "Музыка", "Папка с музыкой пуста")
                return
            from PySide6.QtWidgets import QMenu

            menu = QMenu(self)
            for idx, path in enumerate(ctx.music_files):
                action = menu.addAction(os.path.basename(path))
                action.triggered.connect(lambda _=False, i=idx: self.start_track(i))
            menu.exec_(self.play_btn.mapToGlobal(self.play_btn.rect().bottomLeft()))
        elif not ctx.music_state["paused"]:
            pygame.mixer.music.pause()
            ctx.music_state["paused"] = True
            self.play_btn.setText("▶️")
        else:
            pygame.mixer.music.unpause()
            ctx.music_state["paused"] = False
            self.play_btn.setText("⏸")
            if not self.track_timer.isActive():
                self.track_timer.start()

    def start_track(self, index: int) -> None:
        ctx = self.ctx
        if index < 0 or index >= len(ctx.music_files):
            return
        path = ctx.music_files[index]
        if not pygame.mixer.get_init():
            pygame.mixer.init()
        try:
            pygame.mixer.music.load(path)
            pygame.mixer.music.set_volume(ctx.music_volume / 100)
            pygame.mixer.music.play()
            ctx.music_index = index
            ctx.music_path = path
            ctx.music_state["playing"] = True
            ctx.music_state["paused"] = False
            self.play_btn.setText("⏸")
            if not self.track_timer.isActive():
                self.track_timer.start()
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", str(e))

    def play_next_track(self):
        ctx = self.ctx
        if not ctx.music_files:
            return
        next_idx = (ctx.music_index + 1) % len(ctx.music_files)
        self.start_track(next_idx)

    def play_prev_track(self):
        ctx = self.ctx
        if not ctx.music_files:
            return
        prev_idx = (ctx.music_index - 1) % len(ctx.music_files)
        self.start_track(prev_idx)

    def toggle_volume_slider(self):
        self.volume_slider.setVisible(not self.volume_slider.isVisible())

    def change_volume(self, value: int) -> None:
        self.ctx.music_volume = value
        if pygame.mixer.get_init():
            pygame.mixer.music.set_volume(value / 100)

    def check_music(self) -> None:
        ctx = self.ctx
        if ctx.music_state["playing"] and not ctx.music_state["paused"]:
            if not pygame.mixer.music.get_busy():
                self.play_next_track()

    def toggle_regular_fields(self, checked: bool):
        self.ctx.regular_meeting_enabled = bool(checked)
        self.regular_group.setVisible(bool(checked))

    def toggle_auto_report(self, val: bool) -> None:
        self.ctx.auto_report_enabled = bool(val)
        if hasattr(self, "report_block"):
            self.report_block.setVisible(bool(val))

import os
from PySide6.QtWidgets import QApplication
from logic.template_history import TemplateHistory
from logic.user_settings import UserSettings


class UIContext:
    """Хранит состояние интерфейса и виджеты приложения."""

    def __init__(self):
        """Создать контекст и загрузить пользовательские настройки."""
        self.app: QApplication | None = None
        self.window = None
        self.fields: dict[str, object] = {}
        self.field_containers: dict[str, object] = {}
        self.input_fields: list[object] = []
        self.asya_mode = False
        self.custom_asya_saved = False
        self.custom_asya_on = False
        self.asya_name = ""
        self.asya_gender = ""
        # personal assistant settings for "ЛС" button
        self.user_name = ""
        self.user_gender = ""
        self.ls_saved = False
        self.ls_active = False
        self.music_dir = os.path.join(
            os.path.dirname(os.path.dirname(__file__)), "music"
        )
        if not os.path.isdir(self.music_dir):
            os.makedirs(self.music_dir, exist_ok=True)
        self.music_files: list[str] = []
        self.music_index: int = -1
        self.music_path = ""
        self.music_volume = 50
        self.refresh_music_files()
        self.music_state = {
            "playing": False,
            "paused": False,
        }
        # persistent settings
        settings_path = os.path.join(
            os.path.dirname(os.path.dirname(__file__)), "user_settings.json"
        )
        self.settings = UserSettings(settings_path)

        self.deepl_api_key = self.settings.deepl_api_key
        self.translator = self.settings.translator

        # "Винтаж" используется по умолчанию
        self.current_theme_name = (
            self.settings.theme if self.settings.save_theme else "Винтаж"
        )
        self.bg_pixmap = None
        self.bg_path = None
        self.btn_ls = None
        self.btn_asya_plus = None
        # OCR settings
        self.ocr_mode = (
            self.settings.ocr_mode if self.settings.save_ocr_mode else "CPU"
        )  # "CPU" or "GPU"

        # generation helpers
        self.auto_copy_enabled = (
            self.settings.auto_copy if self.settings.save_auto_copy else False
        )
        self.auto_generate_after_autofill = (
            self.settings.auto_generate if self.settings.save_auto_generate else False
        )
        self.auto_report_enabled = (
            self.settings.auto_report if self.settings.save_auto_report else False
        )
        self.show_help_icons = self.settings.show_help_icons
        self.report_text = None
        self.labels: dict[str, object] = {}
        self.regular_meeting_enabled = False
        self.regular_count = None
        self.regular_period = None
        self.regular_day = None

        # animation settings
        self.animations_enabled = True
        self.animation_effect = (
            self.settings.animation_effect
            if self.settings.save_animation_effect
            else "Glow"
        )
        self.animation_intensity = 50

        # history of generated templates
        hist_path = os.path.join(
            os.path.dirname(os.path.dirname(__file__)), "template_history.json"
        )
        self.history = TemplateHistory(hist_path)

        # user-defined templates
        tpl_path = os.path.join(
            os.path.dirname(os.path.dirname(__file__)), "user_templates.json"
        )
        from .user_templates import UserTemplates

        self.user_templates = UserTemplates(tpl_path)

    def refresh_music_files(self) -> None:
        """Обновить список доступных музыкальных файлов."""
        if not os.path.isdir(self.music_dir):
            os.makedirs(self.music_dir, exist_ok=True)
        self.music_files = [
            os.path.join(self.music_dir, f)
            for f in os.listdir(self.music_dir)
            if f.lower().endswith((".mp3", ".wav", ".ogg"))
        ]
        self.music_index = 0 if self.music_files else -1
        self.music_path = self.music_files[0] if self.music_files else ""

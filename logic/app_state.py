import os
from PySide6.QtWidgets import QApplication

class UIContext:
    """Centralized storage for UI state and widgets."""
    def __init__(self):
        self.app: QApplication | None = None
        self.window = None
        self.fields: dict[str, object] = {}
        self.field_containers: dict[str, object] = {}
        self.input_fields: list[object] = []
        self.asya_mode = False
        self.custom_asya_saved = False
        self.custom_asya_on = False
        self.asya_name = ''
        self.asya_gender = ''
        # personal assistant settings for "ЛС" button
        self.user_name = ''
        self.user_gender = ''
        self.ls_saved = False
        self.ls_active = False
        self.music_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "music")
        if not os.path.isdir(self.music_dir):
            os.makedirs(self.music_dir, exist_ok=True)
        self.music_files: list[str] = [
            os.path.join(self.music_dir, f)
            for f in os.listdir(self.music_dir)
            if f.lower().endswith((".mp3", ".wav", ".ogg"))
        ]
        self.music_index: int = 0 if self.music_files else -1
        self.music_path = self.music_files[0] if self.music_files else ""
        self.music_state = {
            "playing": False,
            "paused": False,
        }
        # "Винтаж" используется по умолчанию
        self.current_theme_name = "Винтаж"
        self.bg_pixmap = None
        self.bg_path = None
        self.btn_ls = None
        self.btn_asya_plus = None
        # OCR settings
        self.ocr_mode = "CPU"  # or "GPU"

        # generation helpers
        self.auto_copy_enabled = False
        self.labels: dict[str, object] = {}
        self.regular_meeting_enabled = False
        self.regular_count = None
        self.regular_period = None
        self.regular_day = None

        # animation settings
        self.animations_enabled = True
        self.animation_effect = "Glow"
        self.animation_intensity = 50


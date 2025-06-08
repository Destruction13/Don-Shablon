from PySide6.QtWidgets import QApplication

class UIContext:
    """Centralized storage for UI state and widgets."""
    def __init__(self):
        self.app: QApplication | None = None
        self.window = None
        self.fields: dict[str, object] = {}
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
        self.music_path = "James.mp3"
        self.music_state = {
            "playing": False,
            "paused": False,
        }
        self.current_theme_name = "Светлая"
        self.bg_pixmap = None
        self.bg_path = None
        # OCR settings
        self.ocr_mode = "CPU"  # or "GPU"


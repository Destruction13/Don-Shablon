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
        self.music_path = "James.mp3"
        self.music_state = {
            "playing": False,
            "paused": False,
        }
        self.current_theme_name = "Светлая"
        self.bg_pixmap = None
        self.bg_path = None


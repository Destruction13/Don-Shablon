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
        self.asya_name = ""
        self.asya_gender = ""
        # personal assistant settings for "ЛС" button
        self.user_name = ""
        self.user_gender = ""
        self.ls_saved = False
        self.ls_active = False
        self.music_path = "James.mp3"
        self.music_state = {
            "playing": False,
            "paused": False,
        }
        self.hover_buttons.append(btn)
        if self.theme:
            btn.setup_theme(self.theme.button_base_style(), self.theme.button_bg)
            btn.set_effect_mode(self.button_effect)

    def apply_button_effect(self, effect: str) -> None:
        """Set hover animation effect and update all buttons."""
        self.button_effect = effect
        for btn in self.hover_buttons:
            try:
                btn.set_effect_mode(effect)
            except Exception:
                pass


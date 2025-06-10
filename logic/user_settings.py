import json
from pathlib import Path


class UserSettings:
    """Persist user-adjustable settings between runs."""

    def __init__(self, path: str | Path = "user_settings.json") -> None:
        self.path = Path(path)
        self.theme = "Винтаж"
        self.ocr_mode = "CPU"
        self.animation_effect = "Glow"
        self.auto_copy = False

        self.save_theme = True
        self.save_ocr_mode = True
        self.save_animation_effect = True
        self.save_auto_copy = True
        self.load()

    def load(self) -> None:
        if self.path.exists():
            try:
                data = json.loads(self.path.read_text(encoding="utf-8"))
                self.save_theme = data.get("save_theme", True)
                self.save_ocr_mode = data.get("save_ocr_mode", True)
                self.save_animation_effect = data.get("save_animation_effect", True)
                self.save_auto_copy = data.get("save_auto_copy", True)

                if self.save_theme:
                    self.theme = data.get("theme", self.theme)
                if self.save_ocr_mode:
                    self.ocr_mode = data.get("ocr_mode", self.ocr_mode)
                if self.save_animation_effect:
                    self.animation_effect = data.get("animation_effect", self.animation_effect)
                if self.save_auto_copy:
                    self.auto_copy = data.get("auto_copy", self.auto_copy)
            except Exception:
                pass

    def save(self) -> None:
        data = {
            "theme": self.theme,
            "ocr_mode": self.ocr_mode,
            "animation_effect": self.animation_effect,
            "auto_copy": self.auto_copy,
            "save_theme": self.save_theme,
            "save_ocr_mode": self.save_ocr_mode,
            "save_animation_effect": self.save_animation_effect,
            "save_auto_copy": self.save_auto_copy,
        }
        try:
            self.path.write_text(
                json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8"
            )
        except Exception:
            pass

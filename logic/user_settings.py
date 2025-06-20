import json
from pathlib import Path


class UserSettings:
    """Сохраняет пользовательские настройки между запусками программы."""

    def __init__(self, path: str | Path = "user_settings.json") -> None:
        """Создать объект настроек и загрузить их из файла."""
        self.path = Path(path)
        self.theme = "Винтаж"
        self.ocr_mode = "CPU"
        self.animation_effect = "Glow"
        self.auto_copy = False
        self.auto_generate = False
        self.auto_report = False
        self.deepl_api_key = ""
        self.translator = "Google"
        self.show_help_icons = True

        self.save_theme = True
        self.save_ocr_mode = True
        self.save_animation_effect = True
        self.save_auto_copy = True
        self.save_auto_generate = True
        self.save_auto_report = True
        self.load()

    def load(self) -> None:
        """Загрузить настройки из файла."""
        if self.path.exists():
            try:
                data = json.loads(self.path.read_text(encoding="utf-8"))
                self.save_theme = data.get("save_theme", True)
                self.save_ocr_mode = data.get("save_ocr_mode", True)
                self.save_animation_effect = data.get("save_animation_effect", True)
                self.save_auto_copy = data.get("save_auto_copy", True)
                self.save_auto_generate = data.get("save_auto_generate", True)
                self.save_auto_report = data.get("save_auto_report", True)

                self.show_help_icons = data.get("show_help_icons", self.show_help_icons)

                self.deepl_api_key = data.get("deepl_api_key", self.deepl_api_key)
                self.translator = data.get("translator", self.translator)

                if self.save_theme:
                    self.theme = data.get("theme", self.theme)
                if self.save_ocr_mode:
                    self.ocr_mode = data.get("ocr_mode", self.ocr_mode)
                if self.save_animation_effect:
                    self.animation_effect = data.get(
                        "animation_effect", self.animation_effect
                    )
                if self.save_auto_copy:
                    self.auto_copy = data.get("auto_copy", self.auto_copy)
                if self.save_auto_generate:
                    self.auto_generate = data.get("auto_generate", self.auto_generate)
                if self.save_auto_report:
                    self.auto_report = data.get("auto_report", self.auto_report)
            except Exception:
                pass

    def save(self) -> None:
        """Сохранить текущие настройки в файл."""
        data = {
            "theme": self.theme,
            "ocr_mode": self.ocr_mode,
            "animation_effect": self.animation_effect,
            "auto_copy": self.auto_copy,
            "auto_generate": self.auto_generate,
            "auto_report": self.auto_report,
            "deepl_api_key": self.deepl_api_key,
            "translator": self.translator,
            "show_help_icons": self.show_help_icons,
            "save_theme": self.save_theme,
            "save_ocr_mode": self.save_ocr_mode,
            "save_animation_effect": self.save_animation_effect,
            "save_auto_copy": self.save_auto_copy,
            "save_auto_generate": self.save_auto_generate,
            "save_auto_report": self.save_auto_report,
        }
        try:
            self.path.write_text(
                json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8"
            )
        except Exception:
            pass

import json
from pathlib import Path


class UserSettings:
    """Persist user-adjustable settings between runs."""

    def __init__(self, path: str | Path = "user_settings.json") -> None:
        self.path = Path(path)
        self.theme = "Винтаж"
        self.ocr_mode = "CPU"
        self.load()

    def load(self) -> None:
        if self.path.exists():
            try:
                data = json.loads(self.path.read_text(encoding="utf-8"))
                self.theme = data.get("theme", self.theme)
                self.ocr_mode = data.get("ocr_mode", self.ocr_mode)
            except Exception:
                pass

    def save(self) -> None:
        data = {"theme": self.theme, "ocr_mode": self.ocr_mode}
        try:
            self.path.write_text(
                json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8"
            )
        except Exception:
            pass

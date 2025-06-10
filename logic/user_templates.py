import json
from pathlib import Path
from typing import List, Dict

from .room_filter import fix_layout


class UserTemplates:
    """Persist user-created templates."""

    def __init__(self, path: str | Path = "user_templates.json") -> None:
        self.path = Path(path)
        self.templates: List[Dict[str, str]] = []
        self.load()

    def load(self) -> None:
        if self.path.exists():
            try:
                self.templates = json.loads(self.path.read_text(encoding="utf-8"))
            except Exception:
                self.templates = []

    def save(self) -> None:
        try:
            self.path.write_text(
                json.dumps(self.templates, ensure_ascii=False, indent=2),
                encoding="utf-8",
            )
        except Exception:
            pass

    def add_template(self, tag: str, text: str) -> None:
        self.templates.append({"tag": tag, "text": text})
        self.save()

    def remove_template(self, index: int) -> None:
        if 0 <= index < len(self.templates):
            del self.templates[index]
            self.save()

    def filter_by_tag(self, query: str) -> List[Dict[str, str]]:
        if not query:
            return list(self.templates)
        q = query.lower()
        fixed = fix_layout(query).lower()
        result: List[Dict[str, str]] = []
        for t in self.templates:
            tag = t.get("tag", "").lower()
            if q in tag or fixed in tag:
                result.append(t)
        return result

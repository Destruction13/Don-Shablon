import json
from collections import deque
from pathlib import Path
from typing import List, Dict


class TemplateHistory:
    """Хранит историю сгенерированных шаблонов."""

    def __init__(self, path: str | Path = "template_history.json") -> None:
        """Создать историю по указанному пути."""
        self.path = Path(path)
        self.records: deque[Dict] = deque(maxlen=5)
        self.load()

    def load(self) -> None:
        """Загрузить записи из файла."""
        if self.path.exists():
            try:
                data = json.loads(self.path.read_text(encoding="utf-8"))
                self.records = deque(data, maxlen=5)
            except Exception:
                self.records = deque(maxlen=5)

    def save(self) -> None:
        """Сохранить историю в файл."""
        try:
            self.path.write_text(
                json.dumps(list(self.records), ensure_ascii=False, indent=2),
                encoding="utf-8",
            )
        except Exception:
            pass

    def add_record(self, record: Dict) -> None:
        """Добавить запись и сохранить историю."""
        self.records.append(record)
        self.save()

    def get_recent_by_type(self, typ: str) -> List[Dict]:
        """Вернуть до пяти последних записей выбранного типа."""
        typ = typ.lower()
        return [
            r
            for r in reversed(self.records)
            if r.get("type", "").lower() == typ
        ][:5]



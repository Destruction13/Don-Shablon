# Filtering utilities and combo box widget for meeting rooms
from PySide6.QtWidgets import QComboBox


# Mapping from English keyboard layout to Russian
_EN_TO_RU = {
    'q': 'й', 'w': 'ц', 'e': 'у', 'r': 'к', 't': 'е', 'y': 'н', 'u': 'г',
    'i': 'ш', 'o': 'щ', 'p': 'з', '[': 'х', ']': 'ъ',
    'a': 'ф', 's': 'ы', 'd': 'в', 'f': 'а', 'g': 'п', 'h': 'р', 'j': 'о',
    'k': 'л', 'l': 'д', ';': 'ж', "'": 'э',
    'z': 'я', 'x': 'ч', 'c': 'с', 'v': 'м', 'b': 'и', 'n': 'т', 'm': 'ь',
    ',': 'б', '.': 'ю', '`': 'ё', '/': '.',
    '<': 'Б', '>': 'Ю',
}
# add uppercase mapping
_EN_TO_RU.update({k.upper(): v.upper() for k, v in list(_EN_TO_RU.items())})


def fix_layout(text: str) -> str:
    """Convert text typed in English layout to Russian layout."""
    return ''.join(_EN_TO_RU.get(ch, ch) for ch in text)


def filter_rooms(all_rooms: list[str], query: str) -> list[str]:
    """Return rooms filtered according to prefix, substring and layout correction."""
    if not query:
        return list(all_rooms)
    q = query.lower()
    fixed = fix_layout(query).lower()

    prefix = [r for r in all_rooms if r.lower().startswith(q)]
    substring = [r for r in all_rooms if q in r.lower() and r not in prefix]

    remaining = [r for r in all_rooms if r not in prefix + substring]
    if fixed != q:
        prefix_fixed = [r for r in remaining if r.lower().startswith(fixed)]
        substring_fixed = [r for r in remaining if fixed in r.lower() and r not in prefix_fixed]
    else:
        prefix_fixed = []
        substring_fixed = []

    return prefix + substring + prefix_fixed + substring_fixed


class FilteringComboBox(QComboBox):
    """QComboBox with custom filtering logic for meeting rooms."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setEditable(True)
        self._all_items: list[str] = []
        self.lineEdit().textEdited.connect(self._on_text_edited)

    def set_items(self, items: list[str]):
        self._all_items = list(items)
        self._apply_filter(self.lineEdit().text())

    def _on_text_edited(self, text: str):
        self._apply_filter(text)

    def _apply_filter(self, text: str):
        filtered = filter_rooms(self._all_items, text)
        self.blockSignals(True)
        self.clear()
        self.addItems(filtered)
        self.setEditText(text)
        self.blockSignals(False)


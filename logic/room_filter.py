# Filtering utilities and combo box widget for meeting rooms
from PySide6.QtWidgets import QComboBox, QCompleter
from PySide6.QtCore import QStringListModel, Qt, QEvent


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
    """QComboBox with non-blocking autocompletion based on custom filtering."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setEditable(True)
        # Keep focus in the line edit so Tab doesn't jump to the next widget
        line_edit = self.lineEdit()
        if hasattr(line_edit, "setTabChangesFocus"):
            line_edit.setTabChangesFocus(False)
        self._all_items: list[str] = []
        self._model = QStringListModel()
        self._completer = QCompleter(self._model, self)
        self._completer.setCaseSensitivity(Qt.CaseInsensitive)
        self._completer.setFilterMode(Qt.MatchContains)
        self._completer.setCompletionMode(QCompleter.PopupCompletion)
        self.setCompleter(self._completer)
        self.lineEdit().textEdited.connect(self._on_text_edited)
        self.lineEdit().installEventFilter(self)

    def set_items(self, items: list[str]):
        """Populate the combo box with a new list of rooms."""
        self._all_items = list(items)
        self.clear()
        self.addItems(self._all_items)
        self._model.setStringList(self._all_items)
        if self._all_items:
            self.setCurrentIndex(0)

    def _on_text_edited(self, text: str):
        filtered = filter_rooms(self._all_items, text)
        self._model.setStringList(filtered)
        if text and filtered:
            self._completer.complete()

    def accept_first(self):
        """Fill the edit with the first filtered item if available."""
        filtered = self._model.stringList()
        if not filtered:
            return
        text = filtered[0]
        self.setEditText(text)
        idx = self.findText(text)
        if idx >= 0:
            self.setCurrentIndex(idx)

    def eventFilter(self, obj, event):
        if obj is self.lineEdit() and event.type() == QEvent.KeyPress:
            if event.key() in (Qt.Key_Return, Qt.Key_Enter, Qt.Key_Tab):
                self.accept_first()
                return True
        return super().eventFilter(obj, event)


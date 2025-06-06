from PySide6.QtWidgets import QApplication, QWidget

class QtUIContext:
    """Storage for PySide6 UI widgets."""

    def __init__(self):
        self.app = QApplication.instance() or QApplication([])
        self.window = QWidget()
        self.fields: dict[str, QWidget] = {}
        self.input_fields: list[QWidget] = []
        self.type_box = None

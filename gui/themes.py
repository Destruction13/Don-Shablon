THEME_QSS = {
    "Футуризм": """
        * { font-family: 'Orbitron', 'Rajdhani', 'DejaVu Sans'; font-size: 14px; color: #c8fcff; }
        QMainWindow { background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #050d14, stop:1 #0e1c24); }
        QLabel, QGroupBox::title, QCheckBox, QRadioButton, QToolTip { color: #c8fcff; }
        QPushButton, QToolButton {
            background: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 #092d3f, stop:1 #095b8d);
            border: 1px solid #00ffff;
            border-radius: 8px;
            padding: 4px;
        }
        QPushButton:hover, QToolButton:hover {
            background: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 #0b364f, stop:1 #098fc8);
        }
        QPushButton:pressed, QToolButton:pressed, QPushButton:checked, QToolButton:checked {
            background: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 #00ffff, stop:1 #008fb3);
            color: #000000;
        }
        QLineEdit, QComboBox, QTextEdit {
            background: #111820;
            color: #c8fcff;
            border: 1px solid #00ffff;
            border-radius: 6px;
        }
        QLineEdit:focus, QComboBox:focus, QTextEdit:focus { border: 1px solid #88ffff; }
    """,
    "Готика": """
        * { font-family: 'Cinzel', 'IM Fell', 'DejaVu Serif'; font-size: 14px; color: #e8d4f2; }
        QMainWindow { background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #1b0f16, stop:1 #000000); }
        QLabel, QGroupBox::title, QCheckBox, QRadioButton, QToolTip { color: #e8d4f2; }
        QPushButton, QToolButton {
            background: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 #2c1627, stop:1 #4a2346);
            border: 1px dotted #aa66cc;
            border-radius: 6px;
            padding: 4px;
        }
        QPushButton:hover, QToolButton:hover {
            background: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 #44203c, stop:1 #5e2c53);
        }
        QPushButton:pressed, QToolButton:pressed, QPushButton:checked, QToolButton:checked {
            background: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 #5e2c53, stop:1 #762e6d);
        }
        QLineEdit, QComboBox, QTextEdit {
            background: #271822;
            color: #e8d4f2;
            border: 1px dotted #aa66cc;
            border-radius: 5px;
        }
        QLineEdit:focus, QComboBox:focus, QTextEdit:focus { border: 1px solid #dd9cff; }
    """,
    "Киберпанк": """
        * { font-family: 'Share Tech Mono', 'DejaVu Sans Mono'; font-size: 13px; color: #ff9af5; }
        QMainWindow { background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #090018, stop:1 #2a0048); }
        QLabel, QGroupBox::title, QCheckBox, QRadioButton, QToolTip { color: #ff9af5; }
        QPushButton, QToolButton {
            background: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 #32005c, stop:1 #7a007a);
            border: 1px dashed #ff00ff;
            border-radius: 4px;
            padding: 4px;
        }
        QPushButton:hover, QToolButton:hover {
            background: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 #4a007d, stop:1 #a000d8);
        }
        QPushButton:pressed, QToolButton:pressed, QPushButton:checked, QToolButton:checked {
            background: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 #ff00a0, stop:1 #ff0080);
            color: #000000;
        }
        QLineEdit, QComboBox, QTextEdit {
            background: #12003b;
            color: #ff9af5;
            border: 1px dashed #ff00ff;
            border-radius: 4px;
        }
        QLineEdit:focus, QComboBox:focus, QTextEdit:focus { border: 1px solid #00ffff; }
    """,
    "Минимал": """
        * { font-family: 'Segoe UI', 'DejaVu Sans'; font-size: 12px; color: #202020; }
        QMainWindow { background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #f5f5f5, stop:1 #eaeaea); }
        QLabel, QGroupBox::title, QCheckBox, QRadioButton, QToolTip { color: #202020; }
        QPushButton, QToolButton {
            background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #ffffff, stop:1 #dcdcdc);
            border: 1px solid #bfbfbf;
            border-radius: 2px;
            padding: 4px;
        }
        QPushButton:hover, QToolButton:hover {
            background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #eeeeee, stop:1 #cccccc);
        }
        QPushButton:pressed, QToolButton:pressed, QPushButton:checked, QToolButton:checked {
            background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #d0d0d0, stop:1 #b0b0b0);
        }
        QLineEdit, QComboBox, QTextEdit {
            background: #ffffff;
            color: #202020;
            border: 1px solid #bfbfbf;
            border-radius: 2px;
        }
        QLineEdit:focus, QComboBox:focus, QTextEdit:focus { border: 1px solid #337ab7; }
    """,
    "Аниме": """
        * { font-family: 'Segoe UI', 'DejaVu Sans'; font-size: 13px; color: #ff3399; }
        QMainWindow { background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #ffe4f2, stop:1 #fff5f9); }
        QLabel, QGroupBox::title, QCheckBox, QRadioButton, QToolTip { color: #ff3399; }
        QPushButton, QToolButton {
            background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #ffd1ec, stop:1 #ffa8da);
            border: 1px solid #ff66b2;
            border-radius: 6px;
            padding: 4px;
        }
        QPushButton:hover, QToolButton:hover {
            background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #ffe7f5, stop:1 #ffcfe5);
        }
        QPushButton:pressed, QToolButton:pressed, QPushButton:checked, QToolButton:checked {
            background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #ff88cc, stop:1 #ff66b2);
        }
        QLineEdit, QComboBox, QTextEdit {
            background: #ffffff;
            color: #ff3399;
            border: 1px solid #ff66b2;
            border-radius: 6px;
        }
        QLineEdit:focus, QComboBox:focus, QTextEdit:focus { border: 1px solid #ff66b2; }
    """,
    "Гёрли": """
        * { font-family: 'Segoe UI', 'DejaVu Sans'; font-size: 13px; color: #d63384; }
        QMainWindow { background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #fff0f8, stop:1 #ffe2ed); }
        QLabel, QGroupBox::title, QCheckBox, QRadioButton, QToolTip { color: #d63384; }
        QPushButton, QToolButton {
            background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #ffd6e8, stop:1 #ffafcc);
            border: 1px solid #d63384;
            border-radius: 5px;
            padding: 4px;
        }
        QPushButton:hover, QToolButton:hover {
            background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #ffb9d6, stop:1 #ff9acb);
        }
        QPushButton:pressed, QToolButton:pressed, QPushButton:checked, QToolButton:checked {
            background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #ff9acb, stop:1 #ff7ab2);
        }
        QLineEdit, QComboBox, QTextEdit {
            background: #ffffff;
            color: #d63384;
            border: 1px solid #d63384;
            border-radius: 5px;
        }
        QLineEdit:focus, QComboBox:focus, QTextEdit:focus { border: 1px solid #e0529c; }
    """,
    "Неон": """
        * { font-family: 'Monoton', 'DejaVu Sans'; font-size: 13px; color: #eaeaea; }
        QMainWindow { background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #000000, stop:1 #001a1a); }
        QLabel, QGroupBox::title, QCheckBox, QRadioButton, QToolTip { color: #eaeaea; }
        QPushButton, QToolButton {
            background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #141414, stop:1 #2d2d2d);
            border: 1px dashed #39ff14;
            border-radius: 8px;
            padding: 4px;
        }
        QPushButton:hover, QToolButton:hover {
            background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #1f1f1f, stop:1 #444444);
        }
        QPushButton:pressed, QToolButton:pressed, QPushButton:checked, QToolButton:checked {
            background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #39ff14, stop:1 #29a329);
            color: #000000;
        }
        QLineEdit, QComboBox, QTextEdit {
            background: #1a1a1a;
            color: #eaeaea;
            border: 1px dashed #39ff14;
            border-radius: 8px;
        }
        QLineEdit:focus, QComboBox:focus, QTextEdit:focus { border: 1px solid #39ff14; }
    """,
    "Тёмная": """
        * { font-family: 'Roboto Mono', 'DejaVu Sans Mono'; font-size: 13px; color: #eaeaea; }
        QMainWindow { background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #121212, stop:1 #262626); }
        QLabel, QGroupBox::title, QCheckBox, QRadioButton, QToolTip { color: #eaeaea; }
        QPushButton, QToolButton {
            background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #1a1a1a, stop:1 #333333);
            border: 1px solid #555555;
            border-radius: 3px;
            padding: 4px;
        }
        QPushButton:hover, QToolButton:hover {
            background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #222222, stop:1 #444444);
        }
        QPushButton:pressed, QToolButton:pressed, QPushButton:checked, QToolButton:checked {
            background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #333333, stop:1 #555555);
        }
        QLineEdit, QComboBox, QTextEdit {
            background: #000000;
            color: #eaeaea;
            border: 1px solid #555555;
            border-radius: 3px;
        }
        QLineEdit:focus, QComboBox:focus, QTextEdit:focus { border: 1px solid #888888; }
    """,
    "Сканди": """
        * { font-family: 'Segoe UI', 'DejaVu Sans'; font-size: 13px; color: #2d2d2d; }
        QMainWindow { background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #f0f0f0, stop:1 #dce4e6); }
        QLabel, QGroupBox::title, QCheckBox, QRadioButton, QToolTip { color: #2d2d2d; }
        QPushButton, QToolButton {
            background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #e6e7e6, stop:1 #d4d7d5);
            border: 1px solid #9ba0a0;
            border-radius: 4px;
            padding: 4px;
        }
        QPushButton:hover, QToolButton:hover {
            background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #d4d7d5, stop:1 #c2c6c4);
        }
        QPushButton:pressed, QToolButton:pressed, QPushButton:checked, QToolButton:checked {
            background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #bcc0bf, stop:1 #aeb3b1);
        }
        QLineEdit, QComboBox, QTextEdit {
            background: #ffffff;
            color: #2d2d2d;
            border: 1px solid #9ba0a0;
            border-radius: 4px;
        }
        QLineEdit:focus, QComboBox:focus, QTextEdit:focus { border: 1px solid #668b8b; }
    """,
    "Моно": """
        * { font-family: 'JetBrains Mono', 'DejaVu Sans Mono'; font-size: 13px; color: #d0d0d0; }
        QMainWindow { background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #2a2a2a, stop:1 #1e1e1e); }
        QLabel, QGroupBox::title, QCheckBox, QRadioButton, QToolTip { color: #d0d0d0; }
        QPushButton, QToolButton {
            background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #333333, stop:1 #4d4d4d);
            border: 1px solid #707070;
            border-radius: 2px;
            padding: 4px;
        }
        QPushButton:hover, QToolButton:hover {
            background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #444444, stop:1 #666666);
        }
        QPushButton:pressed, QToolButton:pressed, QPushButton:checked, QToolButton:checked {
            background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #666666, stop:1 #888888);
        }
        QLineEdit, QComboBox, QTextEdit {
            background: #1a1a1a;
            color: #d0d0d0;
            border: 1px solid #707070;
            border-radius: 2px;
        }
        QLineEdit:focus, QComboBox:focus, QTextEdit:focus { border: 1px solid #999999; }
    """,
    "Винтаж": """
        * { font-family: 'Georgia', 'Garamond', 'DejaVu Serif'; font-size: 14px; color: #5e412f; }
        QMainWindow { background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #f5e6c8, stop:1 #e9d0a4); }
        QLabel, QGroupBox::title, QCheckBox, QRadioButton, QToolTip { color: #5e412f; }
        QPushButton, QToolButton {
            background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #ecd5b1, stop:1 #d9b385);
            border: 1px solid #8b6f47;
            border-radius: 4px;
            padding: 4px;
        }
        QPushButton:hover, QToolButton:hover {
            background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #f0e0c5, stop:1 #deb98f);
        }
        QPushButton:pressed, QToolButton:pressed, QPushButton:checked, QToolButton:checked {
            background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #d1a679, stop:1 #c2965d);
        }
        QLineEdit, QComboBox, QTextEdit {
            background: #ffffff;
            color: #5e412f;
            border: 1px solid #8b6f47;
            border-radius: 4px;
        }
        QLineEdit:focus, QComboBox:focus, QTextEdit:focus { border: 1px solid #a87f52; }
    """,
}

DEFAULT_QSS = """
    * { font-family: 'Segoe UI'; font-size: 12px; }
    QMainWindow { background-color: #f0f0f0; color: #202020; }
    QLineEdit, QComboBox, QTextEdit { background-color: #ffffff; color: #202020; border-radius: 4px; }
    QPushButton { background-color: #e0e0e0; color: #202020; border-radius: 4px; padding: 4px; }
    QPushButton:hover { background-color: #d0d0d0; }
    QPushButton:checked { background-color: #bdbdbd; }
    QPushButton#lsButton:checked { border: 2px solid #FFD700; }
    QPushButton#asyaButton:checked { border: 2px solid #00AAFF; }
"""


def apply_theme(app, name: str) -> None:
    """Apply theme stylesheet to the QApplication."""
    if not name or name == "Стандартная":
        app.setStyleSheet(DEFAULT_QSS)
    else:
        app.setStyleSheet(THEME_QSS.get(name, DEFAULT_QSS))

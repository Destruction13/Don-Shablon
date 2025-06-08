from __future__ import annotations

"""Collection of application themes and helper for building QSS."""

from dataclasses import dataclass
from typing import Dict


@dataclass
class Theme:
    name: str
    background: str
    accent: str
    accent_hover: str
    text: str
    field_bg: str
    button_bg: str
    button_text: str
    font_family: str

    def build_global_qss(self) -> str:
        """Return QSS for applying the theme to QApplication."""
        return f"""
        QWidget {{
            background: {self.background};
            color: {self.text};
            font-family: '{self.font_family}';
        }}
        QLineEdit, QTextEdit, QComboBox {{
            background-color: {self.field_bg};
            border: 1px solid {self.accent};
            border-radius: 4px;
            padding: 3px;
        }}
        QPushButton {{
            color: {self.button_text};
            border: 1px solid {self.accent};
            border-radius: 6px;
            padding: 5px;
        }}
        QPushButton:pressed {{
            border-color: {self.accent_hover};
        }}
        """

    def button_base_style(self) -> str:
        """Base style for buttons without background-color."""
        return (
            f"color: {self.button_text};"
            f"border: 1px solid {self.accent};"
            f"border-radius: 6px;"
            f"padding: 5px;"
        )


# Define all available themes
THEMES: Dict[str, Theme] = {
    "Туманный рассвет": Theme(
        name="Туманный рассвет",
        background="qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #dfe9f3, stop:1 #ffffff)",
        accent="#6d8fa3",
        accent_hover="#3a5161",
        text="#333333",
        field_bg="rgba(255,255,255,0.7)",
        button_bg="rgba(255,255,255,0.8)",
        button_text="#333333",
        font_family="Segoe UI",
    ),
    "Графитовый лёд": Theme(
        name="Графитовый лёд",
        background="qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #222222, stop:1 #555555)",
        accent="#9ac1d6",
        accent_hover="#c9e6f5",
        text="#eeeeee",
        field_bg="rgba(255,255,255,0.1)",
        button_bg="rgba(60,60,60,0.7)",
        button_text="#eeeeee",
        font_family="Roboto",
    ),
    "Ретро неон": Theme(
        name="Ретро неон",
        background="#0b0b0b",
        accent="#00ffff",
        accent_hover="#ff0080",
        text="#e0e0e0",
        field_bg="rgba(50,50,50,0.8)",
        button_bg="#222222",
        button_text="#e0e0e0",
        font_family="Courier New",
    ),
    "Песчаный минимализм": Theme(
        name="Песчаный минимализм",
        background="qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #f5f5dc, stop:1 #ffffff)",
        accent="#d2b48c",
        accent_hover="#b89b6d",
        text="#5b4636",
        field_bg="rgba(255,255,255,0.6)",
        button_bg="rgba(255,255,255,0.7)",
        button_text="#5b4636",
        font_family="Georgia",
    ),
    "Киберпанк": Theme(
        name="Киберпанк",
        background="qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 #0f0c29, stop:1 #302b63)",
        accent="#ff0090",
        accent_hover="#ffa5d8",
        text="#d6f3ff",
        field_bg="rgba(50,50,80,0.6)",
        button_bg="rgba(50,20,70,0.8)",
        button_text="#d6f3ff",
        font_family="Consolas",
    ),
    "Голубой закат": Theme(
        name="Голубой закат",
        background="qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #1e3c72, stop:1 #2a5298)",
        accent="#ffcc00",
        accent_hover="#ffee55",
        text="#ffffff",
        field_bg="rgba(255,255,255,0.2)",
        button_bg="rgba(30,60,120,0.8)",
        button_text="#ffffff",
        font_family="Tahoma",
    ),
    "Ночная роскошь": Theme(
        name="Ночная роскошь",
        background="qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #232526, stop:1 #414345)",
        accent="#d4af37",
        accent_hover="#f1d97a",
        text="#f0e6d6",
        field_bg="rgba(70,70,70,0.5)",
        button_bg="rgba(50,50,50,0.7)",
        button_text="#f0e6d6",
        font_family="Garamond",
    ),
    "Осенний бриз": Theme(
        name="Осенний бриз",
        background="qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #FCEABB, stop:1 #F8B500)",
        accent="#AC5D00",
        accent_hover="#d47a00",
        text="#5b3600",
        field_bg="rgba(255,255,255,0.6)",
        button_bg="rgba(255,255,255,0.8)",
        button_text="#5b3600",
        font_family="Verdana",
    ),
    "Лунный свет": Theme(
        name="Лунный свет",
        background="qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #757F9A, stop:1 #D7DDE8)",
        accent="#4a90e2",
        accent_hover="#82b1f0",
        text="#2c3e50",
        field_bg="rgba(255,255,255,0.8)",
        button_bg="rgba(230,230,250,0.8)",
        button_text="#2c3e50",
        font_family="Calibri",
    ),
    "Солнечная поляна": Theme(
        name="Солнечная поляна",
        background="qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #a8e063, stop:1 #56ab2f)",
        accent="#f5f5f5",
        accent_hover="#ffffff",
        text="#1b3b05",
        field_bg="rgba(255,255,255,0.7)",
        button_bg="rgba(255,255,255,0.9)",
        button_text="#1b3b05",
        font_family="Arial",
    ),
}


def build_styles(theme_name: str) -> tuple[str, Theme]:
    theme = THEMES[theme_name]
    return theme.build_global_qss(), theme

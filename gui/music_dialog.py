from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QComboBox,
    QCheckBox, QPushButton, QMessageBox
)
import os
import pygame

from logic.app_state import UIContext


class MusicDialog(QDialog):
    """Simple dialog for music playback settings."""

    TRACKS = [
        "James.mp3",
        "Track1.mp3",
        "Track2.mp3",
    ]

    def __init__(self, ctx: UIContext, parent=None):
        super().__init__(parent)
        self.ctx = ctx
        self.setWindowTitle("Музыка")

        layout = QVBoxLayout(self)

        self.enable_check = QCheckBox("Включить музыку")
        self.enable_check.setChecked(ctx.music_state.get("playing", False))
        layout.addWidget(self.enable_check)

        row = QHBoxLayout()
        row.addWidget(QLabel("Трек:"))
        self.track_combo = QComboBox()
        self.track_combo.addItems(self.TRACKS)
        self.track_combo.setCurrentText(ctx.music_path)
        row.addWidget(self.track_combo)
        layout.addLayout(row)

        self.listen_btn = QPushButton("🎧 Прослушать")
        layout.addWidget(self.listen_btn)

        self.enable_check.toggled.connect(self.toggle_music)
        self.listen_btn.clicked.connect(self.preview)
        self.track_combo.currentTextChanged.connect(self.change_track)

    def change_track(self, name: str) -> None:
        self.ctx.music_path = name

    def toggle_music(self, checked: bool) -> None:
        path = self.ctx.music_path
        if checked:
            self._play(path, loop=True)
            self.ctx.music_state["playing"] = True
            self.ctx.music_state["paused"] = False
        else:
            if pygame.mixer.get_init():
                pygame.mixer.music.stop()
            self.ctx.music_state["playing"] = False
            self.ctx.music_state["paused"] = False

    def preview(self) -> None:
        path = self.track_combo.currentText()
        self._play(path, loop=False)

    def _play(self, path: str, loop: bool = False) -> None:
        if not path or not os.path.exists(path):
            QMessageBox.warning(self, "Ошибка", "Файл недоступен")
            return
        if not pygame.mixer.get_init():
            pygame.mixer.init()
        try:
            pygame.mixer.music.load(path)
            pygame.mixer.music.play(-1 if loop else 0)
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", str(e))

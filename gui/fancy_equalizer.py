import os
from PySide6.QtWidgets import QWidget, QVBoxLayout
from PySide6.QtCore import Qt, QTimer
import numpy as np
import pyqtgraph as pg

from logic.app_state import UIContext


class FancyEqualizer(QWidget):
    """Animated equalizer using pyqtgraph for smoother visuals."""

    def __init__(self, ctx: UIContext, parent=None) -> None:
        super().__init__(parent)
        self.ctx = ctx
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        self.plot = pg.PlotWidget()
        self.plot.setBackground(None)
        self.plot.setMenuEnabled(False)
        self.plot.hideAxis('bottom')
        self.plot.hideAxis('left')
        self.plot.setYRange(0, 1)
        layout.addWidget(self.plot)
        self.setStyleSheet("border: 1px solid #33CCFF;")
        x = np.arange(10)
        self.bars = pg.BarGraphItem(x=x, height=np.zeros_like(x), width=0.8,
                                    brush=pg.mkBrush('#33CCFF'))
        self.plot.addItem(self.bars)
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_bars)
        self.timer.start(120)

    def update_bars(self) -> None:
        playing = self.ctx.music_state.get('playing') and not self.ctx.music_state.get('paused')
        if os.getenv('EQ_DEBUG'):
            print(f"[EQ] update playing={playing}")
        if playing:
            heights = np.random.uniform(0.1, 1.0, size=10)
        else:
            heights = np.full(10, 0.1)
        self.bars.setOpts(height=heights)

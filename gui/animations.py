from PySide6.QtCore import (
    QObject,
    QEvent,
    QPropertyAnimation,
    QEasingCurve,
    QRect,
    QPoint,
)
from PySide6.QtGui import QColor
from PySide6.QtWidgets import (
    QGraphicsDropShadowEffect,
    QGraphicsOpacityEffect,
    QGraphicsColorizeEffect,
)


class HoverAnimationFilter(QObject):
    def __init__(self, ctx):
        super().__init__()
        self.ctx = ctx
        self._orig_geom = {}
        self._animations = {}

    def eventFilter(self, obj, event):
        if event.type() == QEvent.Enter:
            if not getattr(self.ctx, "animations_enabled", False):
                return False
            effect = getattr(self.ctx, "animation_effect", "Glow")
            intensity = getattr(self.ctx, "animation_intensity", 50)
            if effect == "Glow":
                glow = QGraphicsDropShadowEffect(obj)
                glow.setOffset(0)
                glow.setBlurRadius(max(5, intensity))
                glow.setColor(QColor("#3daee9"))
                obj.setGraphicsEffect(glow)
            elif effect == "Scale":
                rect = obj.geometry()
                self._orig_geom[obj] = QRect(rect)
                scale = 1.13
                new_rect = QRect(rect)
                dw = int(rect.width() * (scale - 1) / 2)
                dh = int(rect.height() * (scale - 1) / 2)
                new_rect.adjust(-dw, -dh, dw, dh)
                anim = QPropertyAnimation(obj, b"geometry", obj)
                anim.setDuration(150)
                anim.setEasingCurve(QEasingCurve.OutQuad)
                anim.setStartValue(rect)
                anim.setEndValue(new_rect)
                anim.start()
                self._animations[obj] = anim
            elif effect == "Pulse":
                op = QGraphicsOpacityEffect(obj)
                obj.setGraphicsEffect(op)
                anim = QPropertyAnimation(op, b"opacity", obj)
                anim.setDuration(max(200, 1000 - intensity * 8))
                anim.setStartValue(1.0)
                anim.setEndValue(max(0.3, 1 - intensity / 100))
                anim.setLoopCount(-1)
                anim.setEasingCurve(QEasingCurve.InOutQuad)
                anim.start()
                self._animations[obj] = anim
            elif effect == "Shimmer":
                colorize = QGraphicsColorizeEffect(obj)
                colorize.setColor(QColor("#ffffff"))
                obj.setGraphicsEffect(colorize)
                anim = QPropertyAnimation(colorize, b"strength", obj)
                anim.setDuration(800)
                anim.setStartValue(0)
                anim.setEndValue(min(1.0, intensity / 100))
                anim.setLoopCount(-1)
                anim.setEasingCurve(QEasingCurve.InOutQuad)
                anim.start()
                self._animations[obj] = anim
            elif effect == "Shadow Slide":
                shadow = QGraphicsDropShadowEffect(obj)
                shadow.setBlurRadius(10)
                shadow.setColor(QColor("#3daee9"))
                obj.setGraphicsEffect(shadow)
                anim = QPropertyAnimation(shadow, b"offset", obj)
                anim.setDuration(300)
                anim.setStartValue(QPoint(0, 0))
                anim.setEndValue(QPoint(intensity / 5, intensity / 5))
                anim.setEasingCurve(QEasingCurve.OutQuad)
                anim.setLoopCount(2)
                anim.start()
                self._animations[obj] = anim
        elif event.type() == QEvent.Leave:
            anim = self._animations.pop(obj, None)
            if anim:
                anim.stop()
            if self.ctx.animation_effect == "Scale" and obj in self._orig_geom:
                rect = obj.geometry()
                orig = self._orig_geom.pop(obj)
                revert = QPropertyAnimation(obj, b"geometry", obj)
                revert.setDuration(150)
                revert.setEasingCurve(QEasingCurve.OutQuad)
                revert.setStartValue(rect)
                revert.setEndValue(orig)
                revert.start()
            if obj.graphicsEffect():
                obj.graphicsEffect().deleteLater()
                obj.setGraphicsEffect(None)
        return False

def setup_animation(widget, ctx):
    if not hasattr(ctx, "anim_filter"):
        ctx.anim_filter = HoverAnimationFilter(ctx)
    widget.installEventFilter(ctx.anim_filter)

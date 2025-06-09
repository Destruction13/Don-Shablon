from PySide6.QtCore import (
    QObject,
    QEvent,
    QPropertyAnimation,
    QEasingCurve,
    QRect,
    QPoint,
    QTimer,
    Qt,
)
from PySide6.QtGui import QColor, QCursor, QPalette
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
        self._effects = {}
        self._timers = {}
        self._orig_styles = {}
        self._progress_overlays = {}
        self._active_effect = {}

    def _store_anim(self, obj, anim):
        """Track running animations and clean up on finish."""
        self._animations[obj] = anim
        try:
            anim.finished.connect(lambda o=obj: self._animations.pop(o, None))
        except Exception:
            pass

    def eventFilter(self, obj, event):
        if event.type() == QEvent.Enter:
            if not getattr(self.ctx, "animations_enabled", False):
                return False
            effect = getattr(self.ctx, "animation_effect", "Glow")
            intensity = getattr(self.ctx, "animation_intensity", 50)
            self._active_effect[obj] = effect
            self._apply_effect(obj, effect, intensity)
        elif event.type() == QEvent.Leave:
            effect = self._active_effect.pop(obj, None)
            self._clear_effect(obj, effect)
        return False

    def _apply_effect(self, obj, effect: str, intensity: int) -> None:
        if obj in self._animations:
            return
        if effect == "Glow":
            glow = self._effects.get(obj)
            if not isinstance(glow, QGraphicsDropShadowEffect):
                glow = QGraphicsDropShadowEffect(obj)
                self._effects[obj] = glow
            glow.setOffset(0)
            glow.setBlurRadius(max(5, intensity))
            glow.setColor(QColor("#3daee9"))
            obj.setGraphicsEffect(glow)
        elif effect == "Scale":
            rect = obj.geometry()
            self._orig_geom[obj] = QRect(rect)
            scale = 1.03
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
            self._store_anim(obj, anim)
        elif effect == "Pulse":
            op = self._effects.get(obj)
            if not isinstance(op, QGraphicsOpacityEffect):
                op = QGraphicsOpacityEffect(obj)
                self._effects[obj] = op
            obj.setGraphicsEffect(op)
            anim = QPropertyAnimation(op, b"opacity", obj)
            anim.setDuration(max(200, 1000 - intensity * 8))
            anim.setStartValue(1.0)
            anim.setEndValue(max(0.3, 1 - intensity / 100))
            anim.setLoopCount(-1)
            anim.setEasingCurve(QEasingCurve.InOutQuad)
            anim.start()
            self._store_anim(obj, anim)
        elif effect == "Shimmer":
            glow = self._effects.get(obj)
            if not isinstance(glow, QGraphicsDropShadowEffect):
                glow = QGraphicsDropShadowEffect(obj)
                color = QColor("#3daee9")
                color.setAlpha(180)
                glow.setColor(color)
                self._effects[obj] = glow
                obj.setGraphicsEffect(glow)
            glow.setBlurRadius(max(15, intensity))
            glow.setOffset(0)
            factor = max(1, intensity) / 30
            timer = self._timers.get(obj)
            if timer is None:
                timer = QTimer(obj)
                timer.timeout.connect(lambda o=obj, e=glow, f=factor: self._update_cursor_offset(o, e, f))
                timer.start(30)
                self._timers[obj] = timer
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
            anim.setLoopCount(1)
            anim.start()
            self._store_anim(obj, anim)
        elif effect == "ColorChange":
            color_effect = QGraphicsColorizeEffect(obj)
            color_effect.setColor(QColor("#3daee9"))
            color_effect.setStrength(0.0)
            obj.setGraphicsEffect(color_effect)
            anim = QPropertyAnimation(color_effect, b"strength", obj)
            anim.setDuration(200)
            anim.setStartValue(0.0)
            anim.setEndValue(min(1.0, intensity / 100))
            anim.start()
            self._store_anim(obj, anim)
            self._effects[obj] = color_effect
        elif effect == "ColorInvert":
            if obj not in self._orig_styles:
                self._orig_styles[obj] = obj.styleSheet()
            pal = obj.palette()
            bg = pal.color(obj.backgroundRole())
            txt = pal.color(QPalette.WindowText)
            inv_bg = QColor(255 - bg.red(), 255 - bg.green(), 255 - bg.blue())
            inv_txt = QColor(255 - txt.red(), 255 - txt.green(), 255 - txt.blue())
            obj.setStyleSheet(
                f"background-color: {inv_bg.name()}; color: {inv_txt.name()};"
            )
        elif effect == "Opacity":
            op = QGraphicsOpacityEffect(obj)
            obj.setGraphicsEffect(op)
            anim = QPropertyAnimation(op, b"opacity", obj)
            anim.setDuration(150)
            anim.setStartValue(1.0)
            anim.setEndValue(max(0.0, 1 - intensity / 100))
            anim.start()
            self._store_anim(obj, anim)
            self._effects[obj] = op
        elif effect == "ShadowAppear":
            shadow = QGraphicsDropShadowEffect(obj)
            shadow.setColor(QColor(0, 0, 0, 150))
            shadow.setOffset(0)
            obj.setGraphicsEffect(shadow)
            anim = QPropertyAnimation(shadow, b"blurRadius", obj)
            anim.setDuration(200)
            anim.setStartValue(0)
            anim.setEndValue(max(5, intensity))
            anim.start()
            self._store_anim(obj, anim)
            self._effects[obj] = shadow
        elif effect == "SlideOffset":
            rect = obj.geometry()
            self._orig_geom[obj] = QRect(rect)
            offset = max(1, intensity // 20)
            new_rect = QRect(rect)
            new_rect.translate(offset, offset)
            anim = QPropertyAnimation(obj, b"geometry", obj)
            anim.setDuration(150)
            anim.setEasingCurve(QEasingCurve.OutQuad)
            anim.setStartValue(rect)
            anim.setEndValue(new_rect)
            anim.start()
            self._store_anim(obj, anim)
        elif effect == "ProgressFill":
            from PySide6.QtWidgets import QPushButton, QWidget

            if isinstance(obj, QPushButton):
                overlay = self._progress_overlays.get(obj)
                if overlay is None:
                    overlay = QWidget(obj)
                    overlay.setStyleSheet(
                        "background-color: rgba(61,174,233,120); border: none;"
                    )
                    overlay.setAttribute(Qt.WA_TransparentForMouseEvents)
                    self._progress_overlays[obj] = overlay
                start_rect = QRect(0, 0, 0, obj.height())
                end_rect = QRect(0, 0, int(obj.width() * 0.7), obj.height())
                overlay.setGeometry(start_rect)
                overlay.show()
                anim = QPropertyAnimation(overlay, b"geometry", obj)
                anim.setDuration(300)
                anim.setStartValue(start_rect)
                anim.setEndValue(end_rect)
                anim.start()
                self._store_anim(obj, anim)

    def _clear_effect(self, obj, effect_name=None):
        anim = self._animations.pop(obj, None)
        if anim:
            anim.stop()
        timer = self._timers.pop(obj, None)
        if timer:
            timer.stop()
            timer.deleteLater()

        if effect_name == "ColorInvert":
            style = self._orig_styles.pop(obj, None)
            if style is not None:
                obj.setStyleSheet(style)
            return

        if effect_name == "ProgressFill":
            overlay = self._progress_overlays.get(obj)
            if overlay is not None:
                start_rect = overlay.geometry()
                end_rect = QRect(0, 0, 0, overlay.height())
                anim = QPropertyAnimation(overlay, b"geometry", obj)
                anim.setDuration(200)
                anim.setStartValue(start_rect)
                anim.setEndValue(end_rect)
                anim.finished.connect(lambda o=overlay: (o.hide(), o.setGeometry(0, 0, 0, o.height())))
                anim.start()
                self._store_anim(obj, anim)

        effect = self._effects.pop(obj, None)
        if effect:
            if isinstance(effect, QGraphicsDropShadowEffect):
                use_offset = timer is not None or effect.offset() != QPoint(0, 0)
                end_prop = b"offset" if use_offset else b"blurRadius"
                prop_anim = QPropertyAnimation(effect, end_prop, obj)
                prop_anim.setDuration(150)
                if end_prop == b"blurRadius":
                    prop_anim.setStartValue(effect.blurRadius())
                    prop_anim.setEndValue(0)
                else:
                    prop_anim.setStartValue(effect.offset())
                    prop_anim.setEndValue(QPoint(0, 0))
                prop_anim.finished.connect(lambda eff=effect, o=obj: self._remove_effect(o, eff))
                prop_anim.start()
                self._store_anim(obj, prop_anim)
            elif isinstance(effect, QGraphicsOpacityEffect):
                fade = QPropertyAnimation(effect, b"opacity", obj)
                fade.setDuration(150)
                fade.setStartValue(effect.opacity())
                fade.setEndValue(1.0)
                fade.finished.connect(lambda eff=effect, o=obj: self._remove_effect(o, eff))
                fade.start()
                self._store_anim(obj, fade)
            elif isinstance(effect, QGraphicsColorizeEffect):
                fade = QPropertyAnimation(effect, b"strength", obj)
                fade.setDuration(150)
                fade.setStartValue(effect.strength())
                fade.setEndValue(0.0)
                fade.finished.connect(lambda eff=effect, o=obj: self._remove_effect(o, eff))
                fade.start()
                self._store_anim(obj, fade)
        else:
            obj.setGraphicsEffect(None)

        if obj in self._orig_geom:
            rect = obj.geometry()
            orig = self._orig_geom.pop(obj)
            revert = QPropertyAnimation(obj, b"geometry", obj)
            revert.setDuration(150)
            revert.setEasingCurve(QEasingCurve.OutQuad)
            revert.setStartValue(rect)
            revert.setEndValue(orig)
            revert.start()

    def _remove_effect(self, obj, effect):
        try:
            if obj and obj.graphicsEffect() is effect:
                obj.setGraphicsEffect(None)
        except RuntimeError:
            pass
        try:
            if effect and effect.parent() is not None:
                effect.deleteLater()
        except RuntimeError:
            pass
        self._animations.pop(obj, None)

    def _update_cursor_offset(self, obj, effect, factor):
        if not obj.underMouse():
            return
        pos = obj.mapFromGlobal(QCursor.pos())
        center = obj.rect().center()
        dx = pos.x() - center.x()
        dy = pos.y() - center.y()
        effect.setOffset(dx * factor, dy * factor)

def setup_animation(widget, ctx):
    if not hasattr(ctx, "anim_filter"):
        ctx.anim_filter = HoverAnimationFilter(ctx)
    widget.installEventFilter(ctx.anim_filter)

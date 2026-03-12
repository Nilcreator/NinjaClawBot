"""Procedural animated facial expressions for NinjaClawBot."""

from __future__ import annotations

import logging
import math
import threading
import time
from typing import Any, Callable

from PIL import Image, ImageDraw, ImageFont

from ninjaclawbot.expressions.catalog import normalize_face_expression

log = logging.getLogger(__name__)


class AnimatedFaceEngine:
    """Port of the legacy NinjaRobotV5 facial expression engine."""

    def __init__(self, display: Any | None) -> None:
        self._display = display
        self.width = int(getattr(display, "width", 240))
        self.height = int(getattr(display, "height", 240))

        self.bg_color = "black"
        self.face_color = "white"
        self.blush_color = "#FF69B4"
        self.tear_color = "#00BFFF"
        self.accent_color = "#FFF176"
        self.warning_color = "#FFD54F"
        self.error_color = "#EF5350"

        self._animation_thread: threading.Thread | None = None
        self._stop_event = threading.Event()
        self._thread_lock = threading.Lock()
        self._active_expression: str | None = None

        self.center_x = self.width // 2
        self.center_y = self.height // 2
        self.eye_y = self.center_y - 35
        self.mouth_y = self.center_y + 50
        self.eye_offset = 60
        self.eye_radius = 45
        self.pupil_radius = 20
        self.line_width = 12

        try:
            self.font = ImageFont.truetype("Pillow/Tests/fonts/FreeMono.ttf", 50)
        except OSError:
            self.font = ImageFont.load_default()

        self.animations: dict[str, Callable[[ImageDraw.ImageDraw, float], None]] = {
            "idle": self._logic_idle,
            "happy": self._logic_happy,
            "laughing": self._logic_laughing,
            "sad": self._logic_sad,
            "cry": self._logic_cry,
            "angry": self._logic_angry,
            "surprising": self._logic_surprising,
            "sleepy": self._logic_sleepy,
            "speaking": self._logic_speaking,
            "shy": self._logic_shy,
            "scary": self._logic_scary,
            "exciting": self._logic_exciting,
            "confusing": self._logic_confusing,
            "greeting": self._logic_greeting,
            "listening": self._logic_listening,
            "thinking": self._logic_thinking,
            "curious": self._logic_curious,
            "success": self._logic_success,
            "warning": self._logic_warning,
            "error": self._logic_error,
        }

    @property
    def active_expression(self) -> str | None:
        return self._active_expression

    def render_frame(self, expression: str, t: float) -> Image.Image:
        """Render one frame for a given expression and time offset."""

        normalized = normalize_face_expression(expression)
        image = Image.new("RGB", (self.width, self.height), self.bg_color)
        draw = ImageDraw.Draw(image)
        self.animations[normalized](draw, t)
        return image

    def play(self, expression: str, duration_s: float = 3.0) -> None:
        """Start an animated expression thread."""

        normalized = normalize_face_expression(expression)
        with self._thread_lock:
            self.stop()
            self._stop_event.clear()
            self._active_expression = normalized
            self._animation_thread = threading.Thread(
                target=self._animation_loop,
                args=(normalized, duration_s),
                daemon=True,
            )
            self._animation_thread.start()

    def set_idle(self) -> None:
        self.play("idle", float("inf"))

    def wait(self, timeout: float | None = None) -> None:
        thread = self._animation_thread
        if thread is not None and thread.is_alive():
            thread.join(timeout=timeout)

    def stop(self) -> None:
        thread = self._animation_thread
        if thread is None:
            return
        if thread.is_alive():
            self._stop_event.set()
            thread.join(timeout=1.0)
        self._animation_thread = None
        self._active_expression = None

    def close(self) -> None:
        self.stop()

    def _animation_loop(self, expression: str, duration_s: float) -> None:
        start_time = time.time()
        while not self._stop_event.is_set():
            elapsed = time.time() - start_time
            if math.isfinite(duration_s) and elapsed >= duration_s:
                break
            image = self.render_frame(expression, elapsed)
            try:
                if self._display is not None:
                    self._display.show_image(image)
            except Exception as exc:  # pragma: no cover - defensive guard for hardware I/O
                log.error("Expression display failed: %s", exc, exc_info=True)
                break
            time.sleep(1 / 60)
        self._active_expression = None

    def _draw_base_eyes(
        self,
        draw: ImageDraw.ImageDraw,
        left_pupil_shift: tuple[float, float] = (0, 0),
        right_pupil_shift: tuple[float, float] = (0, 0),
    ) -> None:
        lx, ly = self.center_x - self.eye_offset, self.eye_y
        draw.ellipse(
            [
                lx - self.eye_radius,
                ly - self.eye_radius,
                lx + self.eye_radius,
                ly + self.eye_radius,
            ],
            fill=self.face_color,
        )
        lpx, lpy = lx + left_pupil_shift[0], ly + left_pupil_shift[1]
        draw.ellipse(
            [
                lpx - self.pupil_radius,
                lpy - self.pupil_radius,
                lpx + self.pupil_radius,
                lpy + self.pupil_radius,
            ],
            fill=self.bg_color,
        )

        rx, ry = self.center_x + self.eye_offset, self.eye_y
        draw.ellipse(
            [
                rx - self.eye_radius,
                ry - self.eye_radius,
                rx + self.eye_radius,
                ry + self.eye_radius,
            ],
            fill=self.face_color,
        )
        rpx, rpy = rx + right_pupil_shift[0], ry + right_pupil_shift[1]
        draw.ellipse(
            [
                rpx - self.pupil_radius,
                rpy - self.pupil_radius,
                rpx + self.pupil_radius,
                rpy + self.pupil_radius,
            ],
            fill=self.bg_color,
        )

    def _draw_happy_base(self, draw: ImageDraw.ImageDraw) -> None:
        self._draw_base_eyes(draw)
        eyebrow_y = self.eye_y - self.eye_radius - (self.line_width / 2) - 5
        draw.arc(
            [
                self.center_x - self.eye_offset - 40,
                eyebrow_y - 40,
                self.center_x - self.eye_offset + 40,
                eyebrow_y,
            ],
            0,
            180,
            fill=self.face_color,
            width=self.line_width,
        )
        draw.arc(
            [
                self.center_x + self.eye_offset - 40,
                eyebrow_y - 40,
                self.center_x + self.eye_offset + 40,
                eyebrow_y,
            ],
            0,
            180,
            fill=self.face_color,
            width=self.line_width,
        )
        draw.arc(
            [
                self.center_x - 70,
                self.mouth_y - 50,
                self.center_x + 70,
                self.mouth_y + 50,
            ],
            0,
            180,
            fill=self.face_color,
        )

    def _draw_sad_base(self, draw: ImageDraw.ImageDraw) -> None:
        pupil_shift = (0, 15)
        self._draw_base_eyes(draw, pupil_shift, pupil_shift)
        draw.line(
            [
                self.center_x - self.eye_offset - 30,
                self.eye_y - 50,
                self.center_x - self.eye_offset + 10,
                self.eye_y - 70,
            ],
            fill=self.face_color,
            width=self.line_width,
        )
        draw.line(
            [
                self.center_x + self.eye_offset + 30,
                self.eye_y - 50,
                self.center_x + self.eye_offset - 10,
                self.eye_y - 70,
            ],
            fill=self.face_color,
            width=self.line_width,
        )
        draw.arc(
            [
                self.center_x - 60,
                self.mouth_y + 20,
                self.center_x + 60,
                self.mouth_y + 80,
            ],
            180,
            360,
            fill=self.face_color,
        )

    def _draw_caption(
        self,
        draw: ImageDraw.ImageDraw,
        text: str,
        *,
        x_offset: int = 0,
        y_offset: int = 0,
        fill: str | tuple[int, int, int] | None = None,
    ) -> None:
        fill = fill or self.face_color
        bbox = draw.textbbox((0, 0), text, font=self.font)
        width = bbox[2] - bbox[0]
        height = bbox[3] - bbox[1]
        x_pos = self.center_x - width // 2 + x_offset
        y_pos = self.center_y - height // 2 + y_offset
        draw.text((x_pos, y_pos), text, font=self.font, fill=fill)

    def _logic_idle(self, draw: ImageDraw.ImageDraw, t: float) -> None:
        blink_cycle = (t * 2) % 3
        mouth_offset = math.sin(t * 2.4) * 2
        if blink_cycle < 0.15:
            for eye_center_x in [self.center_x - self.eye_offset, self.center_x + self.eye_offset]:
                draw.line(
                    [eye_center_x - 30, self.eye_y, eye_center_x + 30, self.eye_y],
                    fill=self.face_color,
                    width=self.line_width,
                )
        else:
            self._draw_base_eyes(draw)
        draw.arc(
            [
                self.center_x - 50,
                self.mouth_y - 10 + mouth_offset,
                self.center_x + 50,
                self.mouth_y + 10 + mouth_offset,
            ],
            0,
            180,
            fill=self.face_color,
        )

    def _logic_happy(self, draw: ImageDraw.ImageDraw, t: float) -> None:
        self._draw_happy_base(draw)
        bounce = math.sin(t * 6) * 2
        draw.arc(
            [
                self.center_x - 70,
                self.mouth_y - 50 + bounce,
                self.center_x + 70,
                self.mouth_y + 50 + bounce,
            ],
            0,
            180,
            fill=self.face_color,
        )

    def _logic_greeting(self, draw: ImageDraw.ImageDraw, t: float) -> None:
        self._draw_happy_base(draw)
        self._draw_caption(draw, "!", x_offset=75, y_offset=-95, fill=self.accent_color)
        arc_offset = math.sin(t * 8) * 4
        draw.arc(
            [
                self.center_x - 70,
                self.mouth_y - 50 + arc_offset,
                self.center_x + 70,
                self.mouth_y + 50 + arc_offset,
            ],
            0,
            180,
            fill=self.face_color,
        )

    def _logic_laughing(self, draw: ImageDraw.ImageDraw, t: float) -> None:
        self._draw_happy_base(draw)
        mouth_height = abs(math.sin(t * 15)) * 60
        draw.rectangle(
            [
                self.center_x - 70,
                self.mouth_y,
                self.center_x + 70,
                self.mouth_y + mouth_height,
            ],
            fill=self.bg_color,
        )

    def _logic_sad(self, draw: ImageDraw.ImageDraw, t: float) -> None:
        self._draw_sad_base(draw)

    def _logic_cry(self, draw: ImageDraw.ImageDraw, t: float) -> None:
        self._draw_sad_base(draw)
        tear_y_base = self.eye_y + self.eye_radius
        tear_length = self.height - tear_y_base
        for i in range(3):
            tear_y = tear_y_base + (t * 200 + i * 40) % tear_length
            draw.line(
                [
                    self.center_x - self.eye_offset,
                    tear_y,
                    self.center_x - self.eye_offset,
                    tear_y + 30,
                ],
                fill=self.tear_color,
                width=self.line_width,
            )

    def _logic_angry(self, draw: ImageDraw.ImageDraw, t: float) -> None:
        shake = math.sin(t * 20) * 3
        self._draw_base_eyes(draw)
        draw.line(
            [
                self.center_x - self.eye_offset - 40,
                self.eye_y - 30 + shake,
                self.center_x - self.eye_offset + 40,
                self.eye_y - 70 + shake,
            ],
            fill=self.face_color,
            width=self.line_width,
        )
        draw.line(
            [
                self.center_x + self.eye_offset + 40,
                self.eye_y - 30 + shake,
                self.center_x + self.eye_offset - 40,
                self.eye_y - 70 + shake,
            ],
            fill=self.face_color,
            width=self.line_width,
        )
        draw.arc(
            [
                self.center_x - 70,
                self.mouth_y - 20,
                self.center_x + 70,
                self.mouth_y + 80,
            ],
            180,
            360,
            fill=self.face_color,
        )

    def _logic_surprising(self, draw: ImageDraw.ImageDraw, t: float) -> None:
        open_factor = min(1.0, t * 4)
        pupil_radius = self.pupil_radius * (1 - open_factor * 0.5)
        for eye_center_x in [self.center_x - self.eye_offset, self.center_x + self.eye_offset]:
            draw.ellipse(
                [
                    eye_center_x - self.eye_radius,
                    self.eye_y - self.eye_radius,
                    eye_center_x + self.eye_radius,
                    self.eye_y + self.eye_radius,
                ],
                fill=self.face_color,
            )
            draw.ellipse(
                [
                    eye_center_x - pupil_radius,
                    self.eye_y - pupil_radius,
                    eye_center_x + pupil_radius,
                    self.eye_y + pupil_radius,
                ],
                fill=self.bg_color,
            )
        mouth_radius = min(50, t * 120)
        draw.ellipse(
            [
                self.center_x - mouth_radius,
                self.mouth_y - mouth_radius,
                self.center_x + mouth_radius,
                self.mouth_y + mouth_radius,
            ],
            fill=self.face_color,
        )

    def _logic_warning(self, draw: ImageDraw.ImageDraw, t: float) -> None:
        self._logic_surprising(draw, t)
        self._draw_caption(draw, "!", x_offset=78, y_offset=-95, fill=self.warning_color)

    def _logic_sleepy(self, draw: ImageDraw.ImageDraw, t: float) -> None:
        open_factor = (math.cos(t * 1.5) + 1) / 2 * 0.9 + 0.05
        for eye_center_x in [self.center_x - self.eye_offset, self.center_x + self.eye_offset]:
            draw.arc(
                [
                    eye_center_x - self.eye_radius,
                    self.eye_y - self.eye_radius,
                    eye_center_x + self.eye_radius,
                    self.eye_y + self.eye_radius,
                ],
                180,
                360,
                fill=self.face_color,
            )
            draw.arc(
                [
                    eye_center_x - self.eye_radius,
                    self.eye_y - self.eye_radius,
                    eye_center_x + self.eye_radius,
                    self.eye_y + self.eye_radius,
                ],
                0,
                180,
                fill=self.face_color,
                width=self.line_width,
            )
        draw.rectangle(
            [
                0,
                self.eye_y - self.eye_radius,
                self.width,
                self.eye_y - self.eye_radius + (self.eye_radius * 2) * (1 - open_factor),
            ],
            fill=self.bg_color,
        )
        draw.arc(
            [self.center_x - 20, self.mouth_y - 10, self.center_x + 20, self.mouth_y + 10],
            0,
            360,
            fill=self.face_color,
        )

    def _logic_speaking(self, draw: ImageDraw.ImageDraw, t: float) -> None:
        self._draw_base_eyes(draw)
        mouth_height = (math.sin(t * 15) + 1) / 2 * 40 + 10
        draw.ellipse(
            [
                self.center_x - 50,
                self.mouth_y,
                self.center_x + 50,
                self.mouth_y + mouth_height,
            ],
            fill=self.face_color,
        )

    def _logic_listening(self, draw: ImageDraw.ImageDraw, t: float) -> None:
        pupil_shift = (0, -8)
        self._draw_base_eyes(draw, pupil_shift, pupil_shift)
        eyebrow_y = self.eye_y - self.eye_radius - 10
        draw.arc(
            [
                self.center_x - self.eye_offset - 35,
                eyebrow_y - 10,
                self.center_x - self.eye_offset + 35,
                eyebrow_y + 20,
            ],
            200,
            340,
            fill=self.face_color,
            width=self.line_width - 4,
        )
        draw.arc(
            [
                self.center_x + self.eye_offset - 35,
                eyebrow_y - 10,
                self.center_x + self.eye_offset + 35,
                eyebrow_y + 20,
            ],
            200,
            340,
            fill=self.face_color,
            width=self.line_width - 4,
        )
        draw.arc(
            [self.center_x - 40, self.mouth_y - 10, self.center_x + 40, self.mouth_y + 20],
            0,
            180,
            fill=self.face_color,
        )

    def _logic_shy(self, draw: ImageDraw.ImageDraw, t: float) -> None:
        pupil_shift = (-20, 15)
        self._draw_base_eyes(draw, pupil_shift, pupil_shift)
        blush_y = self.eye_y + self.eye_radius / 2
        draw.ellipse(
            [
                self.center_x - self.eye_offset - 15,
                blush_y,
                self.center_x - self.eye_offset + 35,
                blush_y + 25,
            ],
            fill=self.blush_color,
        )
        draw.ellipse(
            [
                self.center_x + self.eye_offset - 35,
                blush_y,
                self.center_x + self.eye_offset + 15,
                blush_y + 25,
            ],
            fill=self.blush_color,
        )
        points = [
            self.center_x - 40,
            self.mouth_y + 10,
            self.center_x - 20,
            self.mouth_y,
            self.center_x,
            self.mouth_y + 10,
            self.center_x + 20,
            self.mouth_y,
            self.center_x + 40,
            self.mouth_y + 10,
        ]
        draw.line(points, fill=self.face_color, width=self.line_width - 2, joint="curve")

    def _logic_scary(self, draw: ImageDraw.ImageDraw, t: float) -> None:
        current_pupil_radius = 10
        shake = math.sin(t * 50) * 4
        for eye_center_x in [self.center_x - self.eye_offset, self.center_x + self.eye_offset]:
            draw.ellipse(
                [
                    eye_center_x - self.eye_radius,
                    self.eye_y - self.eye_radius,
                    eye_center_x + self.eye_radius,
                    self.eye_y + self.eye_radius,
                ],
                fill=self.face_color,
            )
            draw.ellipse(
                [
                    eye_center_x - current_pupil_radius,
                    self.eye_y + shake - current_pupil_radius,
                    eye_center_x + current_pupil_radius,
                    self.eye_y + shake + current_pupil_radius,
                ],
                fill=self.bg_color,
            )
        draw.arc(
            [
                self.center_x - 70,
                self.mouth_y - 20,
                self.center_x + 70,
                self.mouth_y + 80,
            ],
            180,
            360,
            fill=self.face_color,
        )

    def _logic_exciting(self, draw: ImageDraw.ImageDraw, t: float) -> None:
        star_points = 10
        for eye_center_x in [self.center_x - self.eye_offset, self.center_x + self.eye_offset]:
            angle = math.pi * 2 / star_points
            points = []
            for i in range(star_points):
                radius = self.eye_radius if i % 2 == 0 else self.eye_radius / 2
                points.append(
                    (
                        eye_center_x + radius * math.cos(angle * i + t * 10),
                        self.eye_y + radius * math.sin(angle * i + t * 10),
                    )
                )
            draw.polygon(points, fill=self.face_color)
        draw.arc(
            [
                self.center_x - 70,
                self.mouth_y - 50,
                self.center_x + 70,
                self.mouth_y + 50,
            ],
            0,
            180,
            fill=self.face_color,
        )

    def _logic_confusing(self, draw: ImageDraw.ImageDraw, t: float) -> None:
        self._draw_base_eyes(draw, (-15, 0), (15, 0))
        draw.arc(
            [
                self.center_x - self.eye_offset - 40,
                self.eye_y - 90,
                self.center_x - self.eye_offset + 40,
                self.eye_y - 10,
            ],
            0,
            180,
            fill=self.face_color,
            width=self.line_width,
        )
        points = [
            self.center_x - 50,
            self.mouth_y + 10,
            self.center_x - 25,
            self.mouth_y - 10,
            self.center_x,
            self.mouth_y + 10,
            self.center_x + 25,
            self.mouth_y - 10,
            self.center_x + 50,
            self.mouth_y + 10,
        ]
        draw.line(points, fill=self.face_color, width=self.line_width - 2, joint="curve")
        if t > 0.5:
            self._draw_caption(draw, "?", x_offset=80, y_offset=-100)

    def _logic_thinking(self, draw: ImageDraw.ImageDraw, t: float) -> None:
        horizontal_shift = math.sin(t * 2.5) * 10
        self._draw_base_eyes(draw, (horizontal_shift - 10, 8), (horizontal_shift + 10, -4))
        draw.line(
            [
                self.center_x - self.eye_offset - 35,
                self.eye_y - 55,
                self.center_x - self.eye_offset + 25,
                self.eye_y - 70,
            ],
            fill=self.face_color,
            width=self.line_width - 2,
        )
        draw.arc(
            [self.center_x - 40, self.mouth_y, self.center_x + 40, self.mouth_y + 28],
            180,
            360,
            fill=self.face_color,
        )
        if int(t * 2) % 3 == 0:
            self._draw_caption(draw, "...", x_offset=78, y_offset=-94)

    def _logic_curious(self, draw: ImageDraw.ImageDraw, t: float) -> None:
        self._draw_base_eyes(draw, (12, -10), (12, -10))
        draw.arc(
            [
                self.center_x - self.eye_offset - 35,
                self.eye_y - 80,
                self.center_x - self.eye_offset + 35,
                self.eye_y - 25,
            ],
            200,
            360,
            fill=self.face_color,
            width=self.line_width - 3,
        )
        draw.line(
            [
                self.center_x + self.eye_offset - 35,
                self.eye_y - 58,
                self.center_x + self.eye_offset + 25,
                self.eye_y - 65,
            ],
            fill=self.face_color,
            width=self.line_width - 3,
        )
        draw.ellipse(
            [self.center_x - 20, self.mouth_y - 5, self.center_x + 20, self.mouth_y + 28],
            outline=self.face_color,
            width=self.line_width - 4,
        )
        if t > 0.35:
            self._draw_caption(draw, "?", x_offset=84, y_offset=-92, fill=self.accent_color)

    def _logic_success(self, draw: ImageDraw.ImageDraw, t: float) -> None:
        self._draw_happy_base(draw)
        sparkle = int(6 + abs(math.sin(t * 8)) * 8)
        draw.line(
            [
                self.center_x + 70,
                self.eye_y + 5,
                self.center_x + 85,
                self.eye_y + 20,
                self.center_x + 110,
                self.eye_y - sparkle,
            ],
            fill=self.accent_color,
            width=self.line_width - 4,
            joint="curve",
        )

    def _logic_error(self, draw: ImageDraw.ImageDraw, t: float) -> None:
        self._draw_sad_base(draw)
        offset = math.sin(t * 8) * 3
        draw.line(
            [
                self.center_x - 26,
                self.mouth_y - 8 + offset,
                self.center_x + 26,
                self.mouth_y + 24 - offset,
            ],
            fill=self.error_color,
            width=self.line_width - 3,
        )
        draw.line(
            [
                self.center_x + 26,
                self.mouth_y - 8 + offset,
                self.center_x - 26,
                self.mouth_y + 24 - offset,
            ],
            fill=self.error_color,
            width=self.line_width - 3,
        )

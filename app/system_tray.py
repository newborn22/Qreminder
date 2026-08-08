"""System tray icon for background running."""

import pystray
from PIL import Image, ImageDraw

from . import startup as startup_mod


def _make_icon_image(size: int = 64) -> Image.Image:
    """Generate a clock-style tray icon programmatically."""
    img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)

    margin = 3
    cx = cy = size // 2
    r = (size // 2) - margin

    # Circle background
    draw.ellipse(
        [margin, margin, size - margin, size - margin],
        fill="#89b4fa",
    )

    # Clock hands
    draw.line([cx, cy, cx - r // 3, cy - r // 3], fill="#1e1e2e", width=4)
    draw.line([cx, cy, cx + r // 2, cy - r // 4], fill="#1e1e2e", width=3)
    # Center dot
    draw.ellipse([cx - 3, cy - 3, cx + 3, cy + 3], fill="#f38ba8")

    return img


def create_tray_icon(on_show, on_exit, on_toggle_startup=None) -> pystray.Icon:
    """Build the pystray Icon with menu."""

    def _startup_text(_item=None):
        enabled = startup_mod.is_enabled()
        check = "✓ " if enabled else ""
        return f"{check}开机自启"

    def _toggle_startup(_icon=None, _item=None):
        if startup_mod.is_enabled():
            startup_mod.disable()
        else:
            startup_mod.enable()
        # pystray will re-call the text callback to update the menu label
        if on_toggle_startup:
            on_toggle_startup(startup_mod.is_enabled())

    menu = pystray.Menu(
        pystray.MenuItem("打开主窗口", on_show, default=True),
        pystray.Menu.SEPARATOR,
        pystray.MenuItem(_startup_text, _toggle_startup),
        pystray.Menu.SEPARATOR,
        pystray.MenuItem("退出", on_exit),
    )
    return pystray.Icon(
        "Qreminder",
        _make_icon_image(),
        "每日提醒",
        menu,
    )

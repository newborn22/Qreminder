"""Entry point — starts scheduler + API server + system tray + tk main loop.

Usage:
    python main.py              # default port 19520
    python main.py --port 8080  # custom port
    python main.py --no-api     # disable API server
"""

import os
import sys
import threading
import tkinter as tk

# Ensure the app package is importable
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.task_storage import TaskStorage
from app.scheduler import Scheduler
from app.main_window import MainWindow
from app.system_tray import create_tray_icon
from app import startup as startup_mod


def _parse_args():
    """Minimal CLI arg parsing — avoids pulling in argparse for .exe size."""
    args = {"port": 19520, "no_api": False}
    argv = sys.argv[1:]
    i = 0
    while i < len(argv):
        if argv[i] == "--port" and i + 1 < len(argv):
            try:
                args["port"] = int(argv[i + 1])
            except ValueError:
                pass
            i += 2
        elif argv[i] == "--no-api":
            args["no_api"] = True
            i += 1
        else:
            i += 1
    return args


def main():
    cli = _parse_args()

    # ── hidden tk root ───────────────────────────────────────────
    root = tk.Tk()
    root.withdraw()
    root.title("每日提醒")

    # ── data ─────────────────────────────────────────────────────
    storage_path = os.path.join(os.path.dirname(__file__), "tasks.json")
    storage = TaskStorage(storage_path)

    # ── scheduler ────────────────────────────────────────────────
    scheduler = Scheduler(storage)
    scheduler.set_root(root)

    # ── main window ──────────────────────────────────────────────
    main_win = MainWindow(root, storage, scheduler)
    scheduler.set_on_trigger(main_win.show_notification)

    # ── API server (optional) ────────────────────────────────────
    api_server = None
    if not cli["no_api"]:
        from app.api_server import ApiServer
        api_server = ApiServer(storage, root, main_win.show_notification, port=cli["port"])
        api_server.start()

    # ── system tray ──────────────────────────────────────────────
    def _on_show(_icon=None, _item=None):
        main_win.show()

    def _on_exit(_icon=None, _item=None):
        scheduler.stop()
        if api_server:
            api_server.stop()
        tray_icon.stop()
        root.quit()

    def _on_toggle_startup(enabled):
        main_win.update_startup_status(enabled)

    tray_icon = create_tray_icon(_on_show, _on_exit, _on_toggle_startup)

    # ── start ────────────────────────────────────────────────────
    scheduler.start()

    # pystray runs its own event loop in a daemon thread
    tray_thread = threading.Thread(target=tray_icon.run, daemon=True, name="tray")
    tray_thread.start()

    # tkinter main loop (main thread)
    try:
        root.mainloop()
    except KeyboardInterrupt:
        pass
    finally:
        scheduler.stop()
        if api_server:
            api_server.stop()
        tray_icon.stop()


if __name__ == "__main__":
    main()

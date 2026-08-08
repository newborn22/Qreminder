"""Background scheduler — checks for due tasks every 30 seconds."""

import threading
import time
from datetime import datetime


class Scheduler:
    """Checks every 30s for enabled tasks whose time + recurrence match now."""

    def __init__(self, storage):
        self.storage = storage
        self.running = False
        self.thread: threading.Thread | None = None
        self.root = None
        self.on_trigger = None
        self._triggered_today: set[str] = set()
        self._last_date = ""

    def set_root(self, root):
        self.root = root

    def set_on_trigger(self, callback):
        """callback(task) — will be called on tk main thread."""
        self.on_trigger = callback

    # ── lifecycle ────────────────────────────────────────────────

    def start(self):
        self.running = True
        self.thread = threading.Thread(target=self._run, daemon=True, name="scheduler")
        self.thread.start()

    def stop(self):
        self.running = False

    # ── check loop ───────────────────────────────────────────────

    def _run(self):
        while self.running:
            try:
                self._check()
            except Exception:
                pass
            time.sleep(30)

    def _check(self):
        now = datetime.now()
        current_time = now.strftime("%H:%M")
        today = now.strftime("%Y-%m-%d")

        # Reset triggered set at midnight
        if today != self._last_date:
            self._triggered_today.clear()
            self._last_date = today

        for task in self.storage.get_enabled():
            if task.time != current_time:
                continue

            if not self._matches_repeat(task, now):
                continue

            trigger_key = f"{today}:{task.id}"
            if trigger_key in self._triggered_today:
                continue

            self._triggered_today.add(trigger_key)
            if self.root and self.on_trigger:
                self.root.after(0, self.on_trigger, task)

    def _matches_repeat(self, task, now: datetime) -> bool:
        """Check whether the task should fire on this date."""
        rt = getattr(task, "repeat_type", "daily")  # back-compat with old data
        if rt in ("daily", "once"):
            return True
        if rt == "weekly":
            # 0=Monday in Python weekday()
            wd = now.weekday()
            days = getattr(task, "repeat_days", [0, 1, 2, 3, 4])
            return wd in days
        if rt == "monthly":
            rd = getattr(task, "repeat_day", 1)
            return now.day == rd
        return True  # unknown type → fire anyway

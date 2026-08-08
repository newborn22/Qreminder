"""Task data model."""

import uuid
from dataclasses import dataclass, field


WEEKDAY_NAMES = ["一", "二", "三", "四", "五", "六", "日"]


@dataclass
class Task:
    """A scheduled task/reminder with recurrence support."""

    id: str = None
    time: str = "09:00"          # HH:MM format
    content: str = ""            # reminder text
    mode: str = "simple"         # "simple" | "rest" | "shutdown"
    lock_minutes: int = 5        # lock duration for rest mode (1-60)
    enabled: bool = True

    # Recurrence
    repeat_type: str = "daily"           # "once" | "daily" | "weekly" | "monthly"
    repeat_days: list = field(default_factory=lambda: [0, 1, 2, 3, 4])  # weekly: [0..6] 0=Mon
    repeat_day: int = 1                  # monthly: 1-31

    # TTS (text-to-speech)
    tts_enabled: bool = True             # read content aloud when notification fires
    tts_engine: str = "edge"             # "edge" | "pyttsx3" | ""
    tts_voice: str = "zh-CN-XiaoxiaoNeural"  # voice ID

    def __post_init__(self):
        if self.id is None:
            self.id = str(uuid.uuid4())
        if self.repeat_days is None:
            self.repeat_days = [0, 1, 2, 3, 4]

    # ── serialization ────────────────────────────────────────────

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "time": self.time,
            "content": self.content,
            "mode": self.mode,
            "lock_minutes": self.lock_minutes,
            "enabled": self.enabled,
            "repeat_type": self.repeat_type,
            "repeat_days": self.repeat_days,
            "repeat_day": self.repeat_day,
            "tts_enabled": self.tts_enabled,
            "tts_engine": self.tts_engine,
            "tts_voice": self.tts_voice,
        }

    @classmethod
    def from_dict(cls, d: dict) -> "Task":
        return cls(
            id=d.get("id"),
            time=d.get("time", "09:00"),
            content=d.get("content", ""),
            mode=d.get("mode", "simple"),
            lock_minutes=d.get("lock_minutes", 5),
            enabled=d.get("enabled", True),
            repeat_type=d.get("repeat_type", "daily"),
            repeat_days=d.get("repeat_days", [0, 1, 2, 3, 4]),
            repeat_day=d.get("repeat_day", 1),
            tts_enabled=d.get("tts_enabled", True),
            tts_engine=d.get("tts_engine", "edge"),
            tts_voice=d.get("tts_voice", "zh-CN-XiaoxiaoNeural"),
        )

    # ── display helpers ──────────────────────────────────────────

    @property
    def mode_label(self) -> str:
        labels = {"simple": "📋 简单提醒", "rest": "☕ 休息模式", "shutdown": "🔌 关机"}
        return labels.get(self.mode, self.mode)

    @property
    def repeat_label(self) -> str:
        """Short human-readable recurrence label for the task list."""
        if self.repeat_type == "once":
            return "单次"
        if self.repeat_type == "daily":
            return "每天"
        if self.repeat_type == "weekly":
            names = [WEEKDAY_NAMES[d] for d in sorted(self.repeat_days) if 0 <= d <= 6]
            return "周" + "".join(names) if names else "每周"
        if self.repeat_type == "monthly":
            return f"每月{self.repeat_day}号"
        return "每天"

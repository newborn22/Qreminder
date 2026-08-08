"""JSON file persistence for tasks."""

import json
import os
import threading
from typing import List

from .task_model import Task


class TaskStorage:
    """Thread-safe JSON file storage for tasks."""

    def __init__(self, filepath: str):
        self.filepath = filepath
        self.lock = threading.Lock()
        self.tasks: List[Task] = []
        self.load()

    # ── persistence ──────────────────────────────────────────────

    def load(self):
        """Load tasks from JSON file."""
        if os.path.exists(self.filepath):
            try:
                with open(self.filepath, "r", encoding="utf-8") as f:
                    data = json.load(f)
                self.tasks = [Task.from_dict(d) for d in data]
            except (json.JSONDecodeError, Exception):
                self.tasks = []
        else:
            self.tasks = []

    def save(self):
        """Save tasks to JSON file."""
        with self.lock:
            os.makedirs(os.path.dirname(self.filepath), exist_ok=True)
            with open(self.filepath, "w", encoding="utf-8") as f:
                json.dump(
                    [t.to_dict() for t in self.tasks],
                    f,
                    ensure_ascii=False,
                    indent=2,
                )

    # ── CRUD ─────────────────────────────────────────────────────

    def add(self, task: Task):
        """Add a new task and persist."""
        self.tasks.append(task)
        self.save()

    def update(self, task_id: str, **kwargs) -> bool:
        """Update task fields by id. Returns True if found."""
        for t in self.tasks:
            if t.id == task_id:
                for k, v in kwargs.items():
                    if hasattr(t, k):
                        setattr(t, k, v)
                self.save()
                return True
        return False

    def delete(self, task_id: str):
        """Delete a task by id."""
        self.tasks = [t for t in self.tasks if t.id != task_id]
        self.save()

    def get(self, task_id: str) -> Task | None:
        """Get a single task by id."""
        for t in self.tasks:
            if t.id == task_id:
                return t
        return None

    def get_all(self) -> List[Task]:
        """Return all tasks (sorted by time)."""
        return sorted(self.tasks, key=lambda t: t.time)

    def get_enabled(self) -> List[Task]:
        """Return only enabled tasks."""
        return [t for t in self.tasks if t.enabled]

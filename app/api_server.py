"""Local HTTP API server — allows external programs / agents to interact.

Listens on 127.0.0.1 only (no network exposure).  Zero extra dependencies.
"""

import json
import threading
from http.server import HTTPServer, BaseHTTPRequestHandler


class ApiServer:
    """REST API served on localhost in a daemon thread."""

    def __init__(self, storage, root, on_notify, port: int = 19520):
        self.storage = storage
        self.root = root      # tk root for thread-safe UI calls
        self.on_notify = on_notify
        self.port = port
        self._httpd: HTTPServer | None = None

    # ── lifecycle ────────────────────────────────────────────────

    def start(self):
        """Launch the HTTP server in a daemon background thread."""
        self._httpd = HTTPServer(("127.0.0.1", self.port), _make_handler(
            self.storage, self.root, self.on_notify,
        ))
        t = threading.Thread(target=self._httpd.serve_forever, daemon=True,
                             name="api-server")
        t.start()

    def stop(self):
        if self._httpd:
            self._httpd.shutdown()
            self._httpd = None


# ── request handler factory ─────────────────────────────────────

def _make_handler(storage, root, on_notify):
    """Closure to inject dependencies into the handler class."""

    class _Handler(BaseHTTPRequestHandler):
        # Silence per-request log spam
        def log_message(self, fmt, *args):
            pass

        # ── routing ────────────────────────────────────────────

        def do_GET(self):
            path = self.path.rstrip("/")
            # /api/health
            if path == "/api/health":
                return self._json({"status": "ok", "tasks_count": len(storage.get_all())})
            # /api/tasks
            if path == "/api/tasks":
                return self._json([t.to_dict() for t in storage.get_all()])
            # /api/tasks/<id>
            if path.startswith("/api/tasks/"):
                task_id = path.split("/")[-1]
                task = storage.get(task_id)
                if task:
                    return self._json(task.to_dict())
                return self._json({"error": "not found"}, status=404)
            return self._json({"error": "not found"}, status=404)

        def do_POST(self):
            path = self.path.rstrip("/")
            body = self._read_body()

            # /api/tasks — create
            if path == "/api/tasks":
                return self._create_task(body)
            # /api/notify — instant notification
            if path == "/api/notify":
                return self._trigger_notify(body)
            return self._json({"error": "not found"}, status=404)

        def do_PUT(self):
            path = self.path.rstrip("/")
            if path.startswith("/api/tasks/"):
                task_id = path.split("/")[-1]
                body = self._read_body()
                return self._update_task(task_id, body)
            return self._json({"error": "not found"}, status=404)

        def do_DELETE(self):
            path = self.path.rstrip("/")
            if path.startswith("/api/tasks/"):
                task_id = path.split("/")[-1]
                task = storage.get(task_id)
                if not task:
                    return self._json({"error": "not found"}, status=404)
                storage.delete(task_id)
                return self._json({"deleted": True})
            return self._json({"error": "not found"}, status=404)

        def do_OPTIONS(self):
            """CORS preflight."""
            self.send_response(204)
            self._cors_headers()
            self.end_headers()

        # ── helpers ────────────────────────────────────────────

        def _read_body(self) -> dict:
            length = int(self.headers.get("Content-Length", 0))
            if length == 0:
                return {}
            raw = self.rfile.read(length)
            try:
                return json.loads(raw)
            except json.JSONDecodeError:
                return {}

        def _json(self, data, status=200):
            body = json.dumps(data, ensure_ascii=False).encode("utf-8")
            self.send_response(status)
            self._cors_headers()
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Content-Length", len(body))
            self.end_headers()
            self.wfile.write(body)

        def _cors_headers(self):
            self.send_header("Access-Control-Allow-Origin", "*")
            self.send_header("Access-Control-Allow-Methods", "GET, POST, PUT, DELETE, OPTIONS")
            self.send_header("Access-Control-Allow-Headers", "Content-Type")

        # ── actions ────────────────────────────────────────────

        def _create_task(self, body: dict):
            from .task_model import Task
            try:
                task = Task(
                    time=body.get("time", "09:00"),
                    content=body.get("content", ""),
                    mode=body.get("mode", "simple"),
                    lock_minutes=body.get("lock_minutes", 5),
                    enabled=body.get("enabled", True),
                    repeat_type=body.get("repeat_type", "daily"),
                    repeat_days=body.get("repeat_days", [0, 1, 2, 3, 4]),
                    repeat_day=body.get("repeat_day", 1),
                    tts_enabled=body.get("tts_enabled", True),
                    tts_engine=body.get("tts_engine", "edge"),
                    tts_voice=body.get("tts_voice", "zh-CN-XiaoxiaoNeural"),
                )
                storage.add(task)
                self._json(task.to_dict(), status=201)
            except Exception as e:
                self._json({"error": str(e)}, status=400)

        def _update_task(self, task_id: str, body: dict):
            task = storage.get(task_id)
            if not task:
                return self._json({"error": "not found"}, status=404)
            updatable = {"time", "content", "mode", "lock_minutes", "enabled",
                         "repeat_type", "repeat_days", "repeat_day",
                         "tts_enabled", "tts_engine", "tts_voice"}
            kwargs = {k: v for k, v in body.items() if k in updatable}
            storage.update(task_id, **kwargs)
            task = storage.get(task_id)  # re-read
            self._json(task.to_dict())

        def _trigger_notify(self, body: dict):
            from .task_model import Task
            task = Task(
                time="now",
                content=body.get("content", ""),
                mode=body.get("mode", "simple"),
                lock_minutes=body.get("lock_minutes", 5),
                enabled=True,
                repeat_type=body.get("repeat_type", "once"),
                tts_enabled=body.get("tts_enabled", True),
                tts_engine=body.get("tts_engine", "edge"),
                tts_voice=body.get("tts_voice", "zh-CN-XiaoxiaoNeural"),
            )
            # Schedule on tk main thread
            root.after(0, on_notify, task)
            self._json({"triggered": True})

    return _Handler

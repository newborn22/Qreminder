"""Main window — task list with create / edit / delete."""

import tkinter as tk
from tkinter import messagebox, ttk

from .notification import NotificationWindow
from .task_dialog import TaskDialog
from . import startup as startup_mod


class MainWindow:
    """Manages the main task-list window."""

    def __init__(self, root: tk.Tk, storage, scheduler):
        self.root = root
        self.storage = storage
        self.scheduler = scheduler
        self.window: tk.Toplevel | None = None
        self.tree: ttk.Treeview | None = None
        self._startup_status_label: tk.Label | None = None

    # ── show / hide ──────────────────────────────────────────────

    def show(self):
        if self.window and self.window.winfo_exists():
            self.window.deiconify()
            self.window.lift()
            self.window.focus_force()
            return
        self._create_window()

    def _create_window(self):
        self.window = tk.Toplevel(self.root)
        self.window.title("⏰ 每日提醒 — 任务管理")
        self.window.geometry("820x520")
        self.window.minsize(640, 360)
        self.window.configure(bg="#1e1e2e")
        self.window.protocol("WM_DELETE_WINDOW", self._on_close)

        self._build_ui()
        self._refresh_list()

        # Center
        self.window.update_idletasks()
        w, h = self.window.winfo_width(), self.window.winfo_height()
        x = (self.window.winfo_screenwidth() // 2) - (w // 2)
        y = (self.window.winfo_screenheight() // 2) - (h // 2)
        self.window.geometry(f"+{x}+{y}")

    def _on_close(self):
        self.window.withdraw()

    # ── UI ───────────────────────────────────────────────────────

    def _build_ui(self):
        bg = "#1e1e2e"
        fg = "#cdd6f4"

        # ── header ────────────────────────────────────────────────
        header = tk.Frame(self.window, bg=bg)
        header.pack(fill=tk.X, padx=16, pady=(14, 8))

        tk.Label(
            header, text="⏰ 每日提醒", font=("Microsoft YaHei", 16, "bold"),
            bg=bg, fg=fg,
        ).pack(side=tk.LEFT)

        tk.Label(
            header, text="到时间自动弹出提醒", font=("Microsoft YaHei", 9),
            bg=bg, fg="#6c7086",
        ).pack(side=tk.LEFT, padx=10)

        # ── toolbar ───────────────────────────────────────────────
        toolbar = tk.Frame(self.window, bg=bg)
        toolbar.pack(fill=tk.X, padx=16, pady=(0, 8))

        btn_data = [
            ("＋ 新建", self._new_task, "#a6e3a1", "#1e1e2e"),
            ("✎ 编辑", self._edit_task, "#89b4fa", "#1e1e2e"),
            ("✕ 删除", self._delete_task, "#f38ba8", "#1e1e2e"),
            ("▶ 测试", self._test_task, "#f9e2af", "#1e1e2e"),
        ]
        for text, cmd, bg_btn, fg_btn in btn_data:
            tk.Button(
                toolbar, text=text, command=cmd,
                font=("Microsoft YaHei", 10), bg=bg_btn, fg=fg_btn,
                activebackground="#6c7086", borderwidth=0,
                padx=14, pady=5, cursor="hand2",
            ).pack(side=tk.LEFT, padx=(0, 8))

        # Refresh button on the right
        tk.Button(
            toolbar, text="⟳ 刷新", command=self._refresh_list,
            font=("Microsoft YaHei", 10), bg="#45475a", fg=fg,
            activebackground="#585b70", borderwidth=0,
            padx=12, pady=5, cursor="hand2",
        ).pack(side=tk.RIGHT)

        # Autostart toggle
        self._startup_status_label = tk.Label(
            toolbar, text="", font=("Microsoft YaHei", 9),
            bg=bg, fg="#a6adc8", cursor="hand2",
        )
        self._startup_status_label.pack(side=tk.RIGHT, padx=(0, 12))
        self._startup_status_label.bind("<Button-1>", lambda _e: self._toggle_startup())
        self._refresh_startup_status()

        # ── treeview ──────────────────────────────────────────────
        tree_frame = tk.Frame(self.window, bg=bg)
        tree_frame.pack(fill=tk.BOTH, expand=True, padx=16, pady=(0, 12))

        columns = ("time", "content", "repeat", "mode", "tts", "enabled")
        self.tree = ttk.Treeview(
            tree_frame, columns=columns, show="headings",
            selectmode="browse", height=14,
        )

        self.tree.heading("time", text="时间")
        self.tree.heading("content", text="提醒内容")
        self.tree.heading("repeat", text="重复")
        self.tree.heading("mode", text="执行方式")
        self.tree.heading("tts", text="语音")
        self.tree.heading("enabled", text="状态")

        self.tree.column("time", width=70, anchor="center")
        self.tree.column("content", width=240)
        self.tree.column("repeat", width=100, anchor="center")
        self.tree.column("mode", width=120, anchor="center")
        self.tree.column("tts", width=60, anchor="center")
        self.tree.column("enabled", width=60, anchor="center")

        # Dark theme
        style = ttk.Style()
        style.theme_use("clam")
        style.configure(
            "Treeview",
            background="#313244", foreground="#cdd6f4",
            fieldbackground="#313244", borderwidth=0,
            font=("Microsoft YaHei", 10), rowheight=28,
        )
        style.configure(
            "Treeview.Heading",
            background="#45475a", foreground="#cdd6f4",
            font=("Microsoft YaHei", 10, "bold"),
            borderwidth=0, padding=6,
        )
        style.map("Treeview", background=[("selected", "#89b4fa")],
                  foreground=[("selected", "#1e1e2e")])

        scrollbar = ttk.Scrollbar(tree_frame, orient=tk.VERTICAL, command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)

        self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        self.tree.bind("<Double-1>", lambda _e: self._edit_task())

    # ── list management ──────────────────────────────────────────

    def _refresh_list(self):
        if self.tree is None:
            return
        for item in self.tree.get_children():
            self.tree.delete(item)
        for task in self.storage.get_all():
            tts_enabled = getattr(task, "tts_enabled", True)
            tts_engine = getattr(task, "tts_engine", "edge") or ""
            tts_icon = f"🔊 {tts_engine}" if tts_enabled else "🔇"
            self.tree.insert(
                "", tk.END, iid=task.id, values=(
                    task.time,
                    task.content,
                    task.repeat_label,
                    task.mode_label,
                    tts_icon,
                    "✅ 启用" if task.enabled else "❌ 停用",
                ),
            )

    # ── actions ──────────────────────────────────────────────────

    def _new_task(self):
        dialog = TaskDialog(self.window, "新建任务")
        if dialog.result:
            self.storage.add(dialog.result)
            self._refresh_list()

    def _edit_task(self):
        sel = self.tree.selection() if self.tree else []
        if not sel:
            messagebox.showwarning("提示", "请先选择一项任务")
            return
        task = self.storage.get(sel[0])
        if not task:
            return
        dialog = TaskDialog(self.window, "编辑任务", task)
        if dialog.result:
            self.storage.update(task.id, **{
                "time": dialog.result.time,
                "content": dialog.result.content,
                "mode": dialog.result.mode,
                "lock_minutes": dialog.result.lock_minutes,
                "enabled": dialog.result.enabled,
                "repeat_type": dialog.result.repeat_type,
                "repeat_days": dialog.result.repeat_days,
                "repeat_day": dialog.result.repeat_day,
                "tts_enabled": dialog.result.tts_enabled,
                "tts_engine": dialog.result.tts_engine,
                "tts_voice": dialog.result.tts_voice,
            })
            self._refresh_list()

    def _test_task(self):
        """Immediately trigger the selected task's notification (for testing)."""
        sel = self.tree.selection() if self.tree else []
        if not sel:
            return
        task = self.storage.get(sel[0])
        if task:
            self.show_notification(task)

    def _delete_task(self):
        sel = self.tree.selection() if self.tree else []
        if not sel:
            messagebox.showwarning("提示", "请先选择一项任务")
            return
        task = self.storage.get(sel[0])
        if not task:
            return
        if messagebox.askyesno("确认删除", f"确定要删除任务「{task.content}」吗？"):
            self.storage.delete(task.id)
            self._refresh_list()

    # ── autostart ─────────────────────────────────────────────────

    def _toggle_startup(self):
        if startup_mod.is_enabled():
            startup_mod.disable()
        else:
            startup_mod.enable()
        self._refresh_startup_status()

    def _refresh_startup_status(self):
        if self._startup_status_label is None:
            return
        if startup_mod.is_enabled():
            self._startup_status_label.config(text="🔔 开机自启: 开", fg="#a6e3a1")
        else:
            self._startup_status_label.config(text="🔕 开机自启: 关", fg="#6c7086")

    def update_startup_status(self, enabled: bool):
        """Called from tray after toggling autostart externally."""
        self._refresh_startup_status()

    # ── notification trigger (called from scheduler) ─────────────

    def show_notification(self, task):
        """Called by the scheduler (via tk after) to show a notification."""
        parent = self.window if (self.window and self.window.winfo_exists()) else self.root

        def _on_close():
            """After notification dismissed, delete once tasks."""
            if getattr(task, "repeat_type", None) == "once":
                self.storage.delete(task.id)
                self._refresh_list()

        NotificationWindow(parent, task, on_close=_on_close)

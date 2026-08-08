"""Create / Edit task dialog."""

import tkinter as tk
from tkinter import ttk

from .task_model import WEEKDAY_NAMES


class TaskDialog:
    """Modal dialog for creating or editing a task."""

    def __init__(self, parent: tk.Toplevel, title: str, task=None):
        self.result = None
        self.task = task

        self.dialog = tk.Toplevel(parent)
        self.dialog.title(title)
        self.dialog.resizable(False, False)
        self.dialog.transient(parent)
        self.dialog.grab_set()
        self.dialog.configure(bg="#1e1e2e")

        # Day-of-week toggle vars (for weekly)
        self._day_vars: list[tk.BooleanVar] = []
        self._day_buttons: list[tk.Button] = []

        self._build_ui()

        if task:
            self._load_task(task)
        else:
            self._on_mode_change()
            self._on_repeat_change()

        # Center on parent
        self.dialog.update_idletasks()
        w, h = self.dialog.winfo_width(), self.dialog.winfo_height()
        px = parent.winfo_rootx() + (parent.winfo_width() // 2) - (w // 2)
        py = parent.winfo_rooty() + (parent.winfo_height() // 2) - (h // 2)
        self.dialog.geometry(f"+{px}+{py}")

        self.dialog.wait_window()

    # ── UI ───────────────────────────────────────────────────────

    def _build_ui(self):
        bg = "#1e1e2e"
        fg = "#cdd6f4"
        accent = "#89b4fa"
        pad = {"padx": 20, "pady": (12, 0)}

        # ── time field ─────────────────────────────────────────
        tk.Label(self.dialog, text="提醒时间", font=("Microsoft YaHei", 10),
                 bg=bg, fg=fg).pack(anchor=tk.W, **pad)

        time_frame = tk.Frame(self.dialog, bg=bg)
        time_frame.pack(anchor=tk.W, padx=20, pady=(4, 0))

        hours = [f"{h:02d}" for h in range(24)]
        minutes = [f"{m:02d}" for m in range(60)]

        self.hour_var = tk.StringVar(value="09")
        h_cb = ttk.Combobox(time_frame, textvariable=self.hour_var, values=hours,
                            width=4, font=("Microsoft YaHei", 13), state="readonly")
        h_cb.pack(side=tk.LEFT)

        tk.Label(time_frame, text=" : ", font=("Microsoft YaHei", 14, "bold"),
                 bg=bg, fg=fg).pack(side=tk.LEFT)

        self.minute_var = tk.StringVar(value="00")
        m_cb = ttk.Combobox(time_frame, textvariable=self.minute_var, values=minutes,
                            width=4, font=("Microsoft YaHei", 13), state="readonly")
        m_cb.pack(side=tk.LEFT)

        # ── content field ──────────────────────────────────────
        tk.Label(self.dialog, text="提醒内容", font=("Microsoft YaHei", 10),
                 bg=bg, fg=fg).pack(anchor=tk.W, padx=20, pady=(14, 0))
        self.content_var = tk.StringVar()
        tk.Entry(
            self.dialog, textvariable=self.content_var, font=("Microsoft YaHei", 12),
            width=38, bg="#313244", fg=fg,
            insertbackground=fg, relief="flat", borderwidth=2,
        ).pack(anchor=tk.W, padx=20, pady=(4, 0))

        # ── mode radio group ───────────────────────────────────
        tk.Label(self.dialog, text="执行方式", font=("Microsoft YaHei", 10),
                 bg=bg, fg=fg).pack(anchor=tk.W, padx=20, pady=(14, 0))

        self.mode_var = tk.StringVar(value="simple")
        mode_frame = tk.Frame(self.dialog, bg=bg)
        mode_frame.pack(anchor=tk.W, padx=20, pady=(4, 0))

        modes = [
            ("📋  简单提醒", "simple"),
            ("☕  休息模式", "rest"),
            ("🔌  关机", "shutdown"),
        ]
        for text, value in modes:
            tk.Radiobutton(
                mode_frame, text=text, variable=self.mode_var, value=value,
                font=("Microsoft YaHei", 10), bg=bg, fg=fg,
                selectcolor="#313244", activebackground=bg,
                activeforeground=accent, command=self._on_mode_change,
            ).pack(side=tk.LEFT, padx=(0, 16))

        # Lock minutes spinbox (rest mode only)
        self.rest_frame = tk.Frame(self.dialog, bg=bg)
        tk.Label(self.rest_frame, text="锁定分钟数：", font=("Microsoft YaHei", 10),
                 bg=bg, fg=fg).pack(side=tk.LEFT)
        self.lock_var = tk.StringVar(value="5")
        tk.Spinbox(
            self.rest_frame, from_=1, to=60, textvariable=self.lock_var,
            width=5, font=("Microsoft YaHei", 11), bg="#313244", fg=fg,
            buttonbackground="#45475a", relief="flat", borderwidth=2,
        ).pack(side=tk.LEFT, padx=6)
        tk.Label(self.rest_frame, text="分钟", font=("Microsoft YaHei", 10),
                 bg=bg, fg=fg).pack(side=tk.LEFT)

        # ── repeat section ─────────────────────────────────────
        tk.Label(self.dialog, text="重复方式", font=("Microsoft YaHei", 10),
                 bg=bg, fg=fg).pack(anchor=tk.W, padx=20, pady=(14, 0))

        self.repeat_var = tk.StringVar(value="daily")
        repeat_frame = tk.Frame(self.dialog, bg=bg)
        repeat_frame.pack(anchor=tk.W, padx=20, pady=(4, 0))

        repeats = [
            ("🔂 单次", "once"),
            ("📅 每日", "daily"),
            ("📆 每周", "weekly"),
            ("📌 每月", "monthly"),
        ]
        for text, value in repeats:
            tk.Radiobutton(
                repeat_frame, text=text, variable=self.repeat_var, value=value,
                font=("Microsoft YaHei", 10), bg=bg, fg=fg,
                selectcolor="#313244", activebackground=bg,
                activeforeground=accent, command=self._on_repeat_change,
            ).pack(side=tk.LEFT, padx=(0, 12))

        # Weekly: day-of-week toggle buttons
        self.weekly_frame = tk.Frame(self.dialog, bg=bg)
        tk.Label(self.weekly_frame, text="选择星期：", font=("Microsoft YaHei", 10),
                 bg=bg, fg=fg).pack(side=tk.LEFT, padx=(0, 8))

        for i, name in enumerate(WEEKDAY_NAMES):
            var = tk.BooleanVar(value=(i < 5))  # Mon-Fri default on
            self._day_vars.append(var)
            btn = tk.Button(
                self.weekly_frame, text=name, font=("Microsoft YaHei", 9),
                width=3, relief="flat", borderwidth=1,
                command=lambda idx=i: self._toggle_day(idx),
            )
            btn.pack(side=tk.LEFT, padx=2)
            self._day_buttons.append(btn)

        # Monthly: day-of-month combobox
        self.monthly_frame = tk.Frame(self.dialog, bg=bg)
        tk.Label(self.monthly_frame, text="每月", font=("Microsoft YaHei", 10),
                 bg=bg, fg=fg).pack(side=tk.LEFT)
        self.month_day_var = tk.StringVar(value="1")
        month_days = [str(d) for d in range(1, 32)]
        ttk.Combobox(
            self.monthly_frame, textvariable=self.month_day_var, values=month_days,
            width=4, font=("Microsoft YaHei", 11), state="readonly",
        ).pack(side=tk.LEFT, padx=4)
        tk.Label(self.monthly_frame, text="号", font=("Microsoft YaHei", 10),
                 bg=bg, fg=fg).pack(side=tk.LEFT)

        # ── enabled checkbox ───────────────────────────────────
        self.enabled_var = tk.BooleanVar(value=True)
        tk.Checkbutton(
            self.dialog, text="启用此任务", variable=self.enabled_var,
            font=("Microsoft YaHei", 10), bg=bg, fg=fg,
            selectcolor="#313244", activebackground=bg,
            activeforeground=accent,
        ).pack(anchor=tk.W, padx=20, pady=(14, 0))

        # ── buttons ────────────────────────────────────────────
        btn_frame = tk.Frame(self.dialog, bg=bg)
        btn_frame.pack(pady=18)
        tk.Button(
            btn_frame, text="确定", command=self._on_confirm,
            font=("Microsoft YaHei", 11), bg=accent, fg="#1e1e2e",
            activebackground="#74c7ec", borderwidth=0,
            padx=28, pady=6, cursor="hand2",
        ).pack(side=tk.LEFT, padx=8)
        tk.Button(
            btn_frame, text="取消", command=self.dialog.destroy,
            font=("Microsoft YaHei", 11), bg="#585b70", fg=fg,
            activebackground="#6c7086", borderwidth=0,
            padx=28, pady=6, cursor="hand2",
        ).pack(side=tk.LEFT, padx=8)

        # Style
        style = ttk.Style()
        style.theme_use("clam")
        style.configure("TCombobox", background="#313244", foreground=fg,
                        fieldbackground="#313244", borderwidth=1, arrowcolor=fg)
        style.map("TCombobox", fieldbackground=[("readonly", "#313244")],
                  foreground=[("readonly", fg)])

    # ── toggle handlers ──────────────────────────────────────────

    def _toggle_day(self, idx: int):
        """Toggle a weekday button on/off."""
        var = self._day_vars[idx]
        var.set(not var.get())
        self._refresh_day_buttons()

    def _refresh_day_buttons(self):
        for i, var in enumerate(self._day_vars):
            if var.get():
                self._day_buttons[i].config(bg="#89b4fa", fg="#1e1e2e")
            else:
                self._day_buttons[i].config(bg="#45475a", fg="#6c7086")

    def _on_mode_change(self):
        if self.mode_var.get() == "rest":
            self.rest_frame.pack(anchor=tk.W, padx=20, pady=(8, 0))
        else:
            self.rest_frame.pack_forget()

    def _on_repeat_change(self):
        rt = self.repeat_var.get()
        self.weekly_frame.pack_forget()
        self.monthly_frame.pack_forget()

        if rt == "weekly":
            self.weekly_frame.pack(anchor=tk.W, padx=20, pady=(6, 0))
            self._refresh_day_buttons()
        elif rt == "monthly":
            self.monthly_frame.pack(anchor=tk.W, padx=20, pady=(6, 0))

    # ── load / save ──────────────────────────────────────────────

    def _load_task(self, task):
        h, m = task.time.split(":")
        self.hour_var.set(h)
        self.minute_var.set(m)
        self.content_var.set(task.content)
        self.mode_var.set(task.mode)
        self.lock_var.set(str(task.lock_minutes))
        self.enabled_var.set(task.enabled)

        # Recurrence
        self.repeat_var.set(getattr(task, "repeat_type", "daily"))
        for i, var in enumerate(self._day_vars):
            days = getattr(task, "repeat_days", [0, 1, 2, 3, 4])
            var.set(i in days)
        self.month_day_var.set(str(getattr(task, "repeat_day", 1)))

        self._on_mode_change()
        self._on_repeat_change()

    def _on_confirm(self):
        from tkinter import messagebox
        from .task_model import Task

        t = f"{self.hour_var.get()}:{self.minute_var.get()}"

        content = self.content_var.get().strip()
        if not content:
            messagebox.showwarning("内容为空", "请输入提醒内容")
            return

        lock_minutes = 5
        if self.mode_var.get() == "rest":
            try:
                lock_minutes = int(self.lock_var.get())
                if lock_minutes < 1 or lock_minutes > 60:
                    raise ValueError
            except ValueError:
                messagebox.showwarning("格式错误", "锁定分钟数应为 1-60 的整数")
                return

        # Gather repeat settings
        repeat_type = self.repeat_var.get()
        repeat_days = [i for i, var in enumerate(self._day_vars) if var.get()]
        if not repeat_days:  # at least one day must be selected
            repeat_days = [0, 1, 2, 3, 4]

        try:
            repeat_day = int(self.month_day_var.get())
        except ValueError:
            repeat_day = 1

        self.result = Task(
            id=self.task.id if self.task else None,
            time=t,
            content=content,
            mode=self.mode_var.get(),
            lock_minutes=lock_minutes,
            enabled=self.enabled_var.get(),
            repeat_type=repeat_type,
            repeat_days=repeat_days,
            repeat_day=repeat_day,
        )
        self.dialog.destroy()

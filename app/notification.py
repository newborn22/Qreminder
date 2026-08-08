"""Notification popup window — three execution modes."""

import subprocess
import tkinter as tk


# Confirmation phrase required to dismiss rest mode early
REST_DISMISS_PHRASE = "quit"


class NotificationWindow(tk.Toplevel):
    """Always-on-top notification overlay for task triggers."""

    def __init__(self, parent: tk.Tk, task, on_close=None):
        super().__init__(parent)
        self.task = task
        self.on_close = on_close
        self.countdown_seconds = 0
        self.cancelled = False
        self._closing = False  # set before legit destroy to suppress Unmap re-show

        # ── window setup ──────────────────────────────────────────
        self.title("⏰ 提醒")
        self.resizable(False, False)
        self.attributes("-topmost", True)
        self.configure(bg="#1e1e2e")

        # Rest mode: remove minimize/maximize buttons, block Win+D hide
        if task.mode == "rest":
            self.attributes("-toolwindow", True)
            self.bind("<Unmap>", self._on_unmap)

        # Larger window size
        win_w, win_h = 520, 400
        self.geometry(f"{win_w}x{win_h}")
        self.update_idletasks()
        x = (self.winfo_screenwidth() // 2) - (win_w // 2)
        y = (self.winfo_screenheight() // 2) - (win_h // 2)
        self.geometry(f"+{x}+{y}")

        self.protocol("WM_DELETE_WINDOW", self._on_close_attempt)
        self.build_ui()

        # TTS: read content aloud
        if getattr(task, "tts_enabled", True):
            engine = getattr(task, "tts_engine", "edge") or "edge"
            voice = getattr(task, "tts_voice", "") or ""
            from .tts import speak
            speak(task.content, engine=engine, voice=voice)

        # Mode-specific startup
        if task.mode == "shutdown":
            self.after(200, self.start_shutdown)
        elif task.mode == "rest":
            self.after(200, self.start_rest)

        self.focus_force()

    # ── UI ───────────────────────────────────────────────────────

    def build_ui(self):
        mode_icons = {"simple": "📋", "rest": "☕", "shutdown": "🔌"}
        mode_titles = {"simple": "简单提醒", "rest": "休息时间", "shutdown": "即将关机"}

        icon = mode_icons.get(self.task.mode, "📋")
        title = mode_titles.get(self.task.mode, "提醒")

        # Top icon + title
        tk.Label(
            self, text=f"{icon}  {title}", font=("Microsoft YaHei", 20, "bold"),
            bg="#1e1e2e", fg="#cdd6f4",
        ).pack(pady=(30, 12))

        # Divider
        tk.Frame(self, height=2, bg="#45475a").pack(fill=tk.X, padx=50)

        # Content message
        tk.Label(
            self, text=self.task.content, font=("Microsoft YaHei", 15),
            bg="#1e1e2e", fg="#a6adc8", wraplength=460, justify="center",
        ).pack(pady=(20, 8))

        # Bottom action area
        self.action_frame = tk.Frame(self, bg="#1e1e2e")
        self.action_frame.pack(pady=20, fill=tk.X, padx=40)

        if self.task.mode == "simple":
            self._build_simple_ui()
        elif self.task.mode == "rest":
            self._build_rest_ui()
        elif self.task.mode == "shutdown":
            self._build_shutdown_ui()

    def _build_simple_ui(self):
        tk.Button(
            self.action_frame, text="  知道了  ", command=self.on_dismiss,
            font=("Microsoft YaHei", 12), bg="#89b4fa", fg="#1e1e2e",
            activebackground="#74c7ec", borderwidth=0,
            padx=36, pady=10, cursor="hand2",
        ).pack()

    def _build_rest_ui(self):
        """Rest mode: always-on-top overlay, requires typing confirmation to exit early."""
        # Countdown display
        self.rest_label = tk.Label(
            self.action_frame,
            text=f"剩余 {self.task.lock_minutes}:00",
            font=("Microsoft YaHei", 13),
            bg="#1e1e2e", fg="#f9e2af",
        )
        self.rest_label.pack(pady=(0, 14))

        # Hint text
        tk.Label(
            self.action_frame,
            text=f"This window stays on top until the timer ends.\nTo dismiss early, type \"{REST_DISMISS_PHRASE}\" and press Enter:",
            font=("Microsoft YaHei", 10),
            bg="#1e1e2e", fg="#6c7086", justify="center",
        ).pack(pady=(0, 8))

        # Entry + button row
        row = tk.Frame(self.action_frame, bg="#1e1e2e")
        row.pack()

        self.rest_entry_var = tk.StringVar()
        self.rest_entry_var.trace_add("write", self._on_rest_entry_changed)

        self.rest_entry = tk.Entry(
            row, textvariable=self.rest_entry_var, font=("Consolas", 12),
            width=16, bg="#313244", fg="#cdd6f4", insertbackground="#cdd6f4",
            relief="flat", borderwidth=2, justify="center",
        )
        self.rest_entry.bind("<Return>", self._on_rest_enter)
        self.rest_entry.pack(side=tk.LEFT, padx=(0, 10))

        self.rest_dismiss_btn = tk.Button(
            row, text="End Break", command=self._on_rest_dismiss,
            font=("Microsoft YaHei", 11), bg="#585b70", fg="#6c7086",
            activebackground="#585b70", borderwidth=0,
            padx=16, pady=6, cursor="hand2", state=tk.DISABLED,
        )
        self.rest_dismiss_btn.pack(side=tk.LEFT)

    def _on_rest_entry_changed(self, *_args):
        """Enable the dismiss button only when the correct phrase is typed."""
        if self.rest_entry_var.get().strip().lower() == REST_DISMISS_PHRASE:
            self.rest_dismiss_btn.config(
                state=tk.NORMAL, bg="#f38ba8", fg="#1e1e2e",
                activebackground="#eba0ac", text="End Break ✓",
            )
        else:
            self.rest_dismiss_btn.config(
                state=tk.DISABLED, bg="#585b70", fg="#6c7086",
                activebackground="#585b70", text="End Break",
            )

    def _on_rest_enter(self, _event=None):
        """Enter key in the entry — dismiss if phrase matches."""
        if self.rest_entry_var.get().strip().lower() == REST_DISMISS_PHRASE:
            self.on_dismiss()

    def _on_rest_dismiss(self):
        """Button click — verify phrase match before dismissing."""
        if self.rest_entry_var.get().strip().lower() == REST_DISMISS_PHRASE:
            self.on_dismiss()

    def _build_shutdown_ui(self):
        self.shutdown_label = tk.Label(
            self.action_frame, text="⚠ 5 秒后关机",
            font=("Microsoft YaHei", 14, "bold"),
            bg="#1e1e2e", fg="#f38ba8",
        )
        self.shutdown_label.pack(side=tk.LEFT, padx=(0, 24))

        tk.Button(
            self.action_frame, text="  取消关机  ", command=self.cancel_shutdown,
            font=("Microsoft YaHei", 12), bg="#a6e3a1", fg="#1e1e2e",
            activebackground="#94e2d5", borderwidth=0,
            padx=24, pady=10, cursor="hand2",
        ).pack(side=tk.LEFT)

    # ── shutdown mode ────────────────────────────────────────────

    def start_shutdown(self):
        self.countdown_seconds = 5
        self._shutdown_tick()

    def _shutdown_tick(self):
        if self.cancelled:
            return
        if self.countdown_seconds <= 0:
            self._do_shutdown()
            return
        self.shutdown_label.config(text=f"⚠ {self.countdown_seconds} 秒后关机")
        self.countdown_seconds -= 1
        self.after(1000, self._shutdown_tick)

    def cancel_shutdown(self):
        self.cancelled = True
        subprocess.run(["shutdown", "/a"], capture_output=True)
        self.on_dismiss()

    def _do_shutdown(self):
        subprocess.run(["shutdown", "/s", "/t", "0"])

    # ── rest mode ────────────────────────────────────────────────

    def start_rest(self):
        """Start countdown — window stays on top, no screen lock."""
        self.countdown_seconds = self.task.lock_minutes * 60
        self._rest_tick()

    def _rest_tick(self):
        if self.cancelled:
            return
        if self.countdown_seconds <= 0:
            self.on_dismiss()
            return
        m, s = divmod(self.countdown_seconds, 60)
        self.rest_label.config(text=f"剩余 {m}:{s:02d}")
        self.countdown_seconds -= 1
        self.after(1000, self._rest_tick)

    # ── close guard ──────────────────────────────────────────────

    def _on_unmap(self, _event=None):
        """Re-show the rest-mode window if hidden externally (Win+D, etc.)."""
        if not self._closing and self.task.mode == "rest":
            self.after(50, self._re_raise)

    def _re_raise(self):
        """Bring the window back on top after being hidden."""
        if self._closing or not self.winfo_exists():
            return
        try:
            self.deiconify()
            self.lift()
            self.focus_force()
        except tk.TclError:
            pass

    def _on_close_attempt(self):
        """Prevent closing via window X button in rest mode."""
        if self.task.mode == "rest":
            return  # ignore close attempts — must type phrase or wait
        self.on_dismiss()

    def on_dismiss(self):
        self.cancelled = True
        self._closing = True
        if self.on_close:
            self.on_close()
        self.destroy()

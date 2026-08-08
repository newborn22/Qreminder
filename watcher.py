"""Hot-reload watcher — monitors app/ for changes, auto-restarts main.py.

Usage:  python watcher.py [--port 19520]
        Ctrl+C to stop.
"""

import os
import sys
import time
import subprocess
from pathlib import Path


PROJECT_DIR = Path(__file__).parent.absolute()
WATCH_DIR = PROJECT_DIR / "app"
MAIN_SCRIPT = PROJECT_DIR / "main.py"
POLL_INTERVAL = 0.5   # seconds between mtime checks


def _collect_mtimes(root: Path) -> dict[str, float]:
    """Return {relpath: mtime} for all .py files under root."""
    mtimes = {}
    for f in root.rglob("*.py"):
        try:
            mtimes[str(f.relative_to(PROJECT_DIR))] = f.stat().st_mtime
        except OSError:
            pass
    return mtimes


def _restart_child(proc, args: list[str]) -> subprocess.Popen:
    """Kill old child (if alive) and spawn a new one."""
    if proc and proc.poll() is None:
        proc.terminate()
        try:
            proc.wait(timeout=3)
        except subprocess.TimeoutExpired:
            proc.kill()
            proc.wait()
    print(f"[watcher] starting: python main.py {' '.join(args[1:])}".strip())
    # Pass through CLI args (--port, --no-api, etc.)
    cmd = [sys.executable, str(MAIN_SCRIPT)] + sys.argv[1:]
    return subprocess.Popen(cmd, cwd=str(PROJECT_DIR))


def main():
    print(f"[watcher] watching {WATCH_DIR} for .py changes")
    print(f"[watcher] press Ctrl+C to stop\n")

    proc = None
    try:
        # First launch
        proc = _restart_child(None, sys.argv[1:])

        # Snapshot current mtimes
        old_mtimes = _collect_mtimes(WATCH_DIR)

        while True:
            time.sleep(POLL_INTERVAL)

            # ── check if child exited on its own ────────────────
            if proc.poll() is not None:
                print("[watcher] app exited normally — watcher stopping")
                break

            # ── check for file changes ──────────────────────────
            new_mtimes = _collect_mtimes(WATCH_DIR)

            if new_mtimes != old_mtimes:
                changed = set(new_mtimes.keys()) - set(old_mtimes.keys())
                changed |= {k for k in new_mtimes if new_mtimes.get(k) != old_mtimes.get(k)}
                changed |= set(old_mtimes.keys()) - set(new_mtimes.keys())

                names = ", ".join(sorted(changed)[:3])
                rest = f" (+{len(changed) - 3} more)" if len(changed) > 3 else ""
                print(f"\n[watcher] changed: {names}{rest}  →  restarting...")

                proc = _restart_child(proc, sys.argv[1:])
                old_mtimes = _collect_mtimes(WATCH_DIR)  # re-snapshot after restart
                print("[watcher] ready\n")

    except KeyboardInterrupt:
        print("\n[watcher] stopping...")
    finally:
        if proc and proc.poll() is None:
            proc.terminate()
            try:
                proc.wait(timeout=3)
            except subprocess.TimeoutExpired:
                proc.kill()
                proc.wait()
        print("[watcher] stopped")


if __name__ == "__main__":
    main()

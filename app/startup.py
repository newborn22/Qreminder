"""Windows startup registration — add/remove shortcut in Startup folder.

Supports both source (pythonw main.py) and frozen (PyInstaller .exe) modes."""

import os
import subprocess
import sys


SHORTCUT_NAME = "Qreminder.lnk"


def _is_frozen() -> bool:
    """True when running as a PyInstaller-bundled .exe."""
    return getattr(sys, "frozen", False)


def _startup_folder() -> str:
    return os.path.join(
        os.environ["APPDATA"],
        r"Microsoft\Windows\Start Menu\Programs\Startup",
    )


def _shortcut_path() -> str:
    return os.path.join(_startup_folder(), SHORTCUT_NAME)


def _source_dir() -> str:
    """Directory containing the source code (or .exe)."""
    if _is_frozen():
        return os.path.dirname(sys.executable)
    return os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def is_enabled() -> bool:
    """Check whether the autostart shortcut exists in the Startup folder."""
    return os.path.exists(_shortcut_path())


def enable() -> bool:
    """Create a Startup folder shortcut so the app launches on login."""
    shortcut_path = _shortcut_path()
    work_dir = _source_dir()

    if _is_frozen():
        # ── frozen .exe ── shortcut points directly to the .exe
        ps_script = (
            f"$ws = New-Object -ComObject WScript.Shell; "
            f"$sc = $ws.CreateShortcut('{shortcut_path}'); "
            f"$sc.TargetPath = '{sys.executable}'; "
            f"$sc.WorkingDirectory = '{work_dir}'; "
            f"$sc.WindowStyle = 7; "
            f"$sc.Save()"
        )
    else:
        # ── source mode ── shortcut to a .bat that runs pythonw
        project_dir = work_dir
        bat_path = os.path.join(project_dir, "startup.bat")

        pythonw = sys.executable.replace("python.exe", "pythonw.exe")
        if not os.path.exists(pythonw):
            pythonw = os.path.join(os.path.dirname(sys.executable), "pythonw.exe")

        with open(bat_path, "w") as f:
            f.write(
                f"@echo off\n"
                f'cd /d "{project_dir}"\n'
                f'start "" "{pythonw}" "{os.path.join(project_dir, "main.py")}"\n'
            )

        ps_script = (
            f"$ws = New-Object -ComObject WScript.Shell; "
            f"$sc = $ws.CreateShortcut('{shortcut_path}'); "
            f"$sc.TargetPath = '{bat_path}'; "
            f"$sc.WorkingDirectory = '{project_dir}'; "
            f"$sc.WindowStyle = 7; "
            f"$sc.Save()"
        )

    result = subprocess.run(
        ["powershell", "-NoProfile", "-Command", ps_script],
        capture_output=True, text=True,
    )
    return result.returncode == 0


def disable() -> bool:
    """Remove the Startup folder shortcut."""
    sp = _shortcut_path()
    if os.path.exists(sp):
        try:
            os.remove(sp)
        except OSError:
            return False
    return True

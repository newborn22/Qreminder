"""Build script — packages the app into a single Windows .exe with PyInstaller."""

import os
import sys
import subprocess
from pathlib import Path


PROJECT_DIR = Path(__file__).parent.absolute()
MAIN_SCRIPT = PROJECT_DIR / "main.py"
OUTPUT_NAME = "每日提醒"
OUTPUT_DIR = PROJECT_DIR / "dist"


def build():
    print("=" * 50)
    print("  Building 每日提醒.exe")
    print("=" * 50)

    # Build command
    cmd = [
        sys.executable, "-m", "PyInstaller",
        "--onefile",                          # single .exe
        "--noconsole",                        # no terminal window (GUI app)
        "--name", OUTPUT_NAME,
        "--distpath", str(OUTPUT_DIR),
        "--workpath", str(PROJECT_DIR / "build" / "pyinstaller"),
        "--specpath", str(PROJECT_DIR / "build"),
        # hidden imports for pystray + PIL
        "--hidden-import", "pystray",
        "--hidden-import", "PIL",
        "--hidden-import", "PIL.Image",
        "--hidden-import", "PIL.ImageDraw",
        "--hidden-import", "tkinter",
        "--hidden-import", "ctypes",
        # collect pystray's bundled resources (icons, etc.)
        "--collect-all", "pystray",
        # main entry point
        str(MAIN_SCRIPT),
    ]

    print(f"\nRunning: {' '.join(cmd)}\n")
    result = subprocess.run(cmd, cwd=str(PROJECT_DIR))

    if result.returncode == 0:
        exe = OUTPUT_DIR / f"{OUTPUT_NAME}.exe"
        size_mb = exe.stat().st_size / (1024 * 1024) if exe.exists() else 0
        print(f"\n{'=' * 50}")
        print(f"  [OK] Build successful!")
        print(f"  Output: {exe}")
        print(f"  Size:   {size_mb:.1f} MB")
        print(f"{'=' * 50}")
    else:
        print("\n  ✗ Build failed!", file=sys.stderr)
        sys.exit(result.returncode)


if __name__ == "__main__":
    build()

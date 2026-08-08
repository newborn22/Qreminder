# CLAUDE.md — Qreminder Project Instructions

## Always follow this workflow after implementing changes

1. **Verify** — run the code to confirm the change works (import check, API test, etc.)
2. **Update docs** — if the change affects usage, update `README.md` and/or `.claude/skills/remind.md`
3. **Commit** — stage and commit with a descriptive message in English, ending with:
   ```
   Co-Authored-By: Claude <noreply@anthropic.com>
   ```
4. **Push** — `git push` to `origin main` (remote: `https://github.com/newborn22/Qreminder.git`)

## Testing conventions

- Use `python -c "..."` for quick import/logic checks
- Use `curl -s http://127.0.0.1:19520/api/...` for API endpoint checks (app must be running)
- Never leave a background `python main.py` process running after testing

## Project identity

- Name: **Qreminder**
- All references in code, docs, and logs use `Qreminder` (never `qwh_notice` or `QWH Notice`)
- Exe output name: `每日提醒.exe`

## Code style

- Python, tkinter GUI, no extra deps for core (pystray + Pillow for tray only)
- Chinese UI strings in tkinter widgets, English in code comments and git messages
- Thread safety: storage operations via `storage.lock`, UI operations via `root.after(0, ...)`

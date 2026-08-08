---
name: remind
description: Send notifications or schedule reminders for the user via the local Qreminder app. Use when the user asks to be reminded, wants a timed notification, needs a break reminder, or asks to schedule recurring tasks. Works by calling the local HTTP API at 127.0.0.1:19520.
---

# Remind Skill

You can send instant notifications and create scheduled reminders for the user through the **Qreminder** desktop app. The app exposes a local HTTP API at `http://127.0.0.1:19520`.

## Prerequisites

The Qreminder app must be running. If the API is unreachable (connection refused), tell the user to start it:

```bash
cd d:/dev/Qreminder && python main.py
# or double-click: dist/每日提醒.exe
```

Verify it's running: `curl -s http://127.0.0.1:19520/api/health`

## Available Actions

### 1. Instant Notification — `POST /api/notify`

Pops up a notification window immediately. Does NOT create a persistent task.

**When to use:** User says "remind me", "notify me", "tell me when done", "ping me", etc. — one-off, right now.

```bash
curl -s -X POST http://127.0.0.1:19520/api/notify \
  -H "Content-Type: application/json" \
  -d '{"content":"<message>","mode":"<mode>","lock_minutes":<minutes>}'
```

Parameters:
- `content` (string, required) — the notification message
- `mode` (string, optional, default `"simple"`):
  - `"simple"` — popup with dismiss button
  - `"rest"` — popup that stays on top, requires typing `quit` to dismiss early
  - `"shutdown"` — popup + 5-second shutdown countdown (can be cancelled)
- `lock_minutes` (int, optional, default `5`, 1-60) — rest mode duration

Examples:

```bash
# Simple heads-up
curl -s -X POST http://127.0.0.1:19520/api/notify \
  -H "Content-Type: application/json" \
  -d '{"content":"代码审查已完成，请查看结果","mode":"simple"}'

# Force a 5-minute break (window stays on top)
curl -s -X POST http://127.0.0.1:19520/api/notify \
  -H "Content-Type: application/json" \
  -d '{"content":"该休息了，起来走走！","mode":"rest","lock_minutes":5}'
```

### 2. Create Scheduled Task — `POST /api/tasks`

Creates a persistent task that fires at the specified time. Survives app restarts.

**When to use:** User says "schedule", "every day at", "remind me every", "set a daily reminder", "weekly at", etc.

```bash
curl -s -X POST http://127.0.0.1:19520/api/tasks \
  -H "Content-Type: application/json" \
  -d '{
    "time":"<HH:MM>",
    "content":"<message>",
    "mode":"<mode>",
    "repeat_type":"<repeat>",
    "repeat_days":[<day indices>],
    "repeat_day":<day of month>,
    "lock_minutes":<minutes>,
    "enabled":true
  }'
```

Parameters:
- `time` (string, required) — `HH:MM` 24-hour format, e.g. `"09:00"`, `"14:30"`
- `content` (string, required) — reminder message
- `mode` (string, optional, default `"simple"`) — same as notify
- `repeat_type` (string, optional, default `"daily"`):
  - `"once"` — fires once, then auto-deletes
  - `"daily"` — every day
  - `"weekly"` — on specific weekdays (use `repeat_days`)
  - `"monthly"` — on a specific day of month (use `repeat_day`)
- `repeat_days` (array of int, default `[0,1,2,3,4]`) — for weekly: `0`=Monday … `6`=Sunday
- `repeat_day` (int, default `1`, 1-31) — for monthly
- `lock_minutes` (int, default `5`, 1-60)
- `enabled` (bool, default `true`)

Examples:

```bash
# Daily reminder
curl -s -X POST http://127.0.0.1:19520/api/tasks \
  -H "Content-Type: application/json" \
  -d '{"time":"09:30","content":"每日站会","mode":"simple","repeat_type":"daily"}'

# Every Monday, Wednesday, Friday
curl -s -X POST http://127.0.0.1:19520/api/tasks \
  -H "Content-Type: application/json" \
  -d '{"time":"10:00","content":"团队同步","mode":"simple","repeat_type":"weekly","repeat_days":[0,2,4]}'

# Monthly on the 1st
curl -s -X POST http://127.0.0.1:19520/api/tasks \
  -H "Content-Type: application/json" \
  -d '{"time":"09:00","content":"月度报告","mode":"simple","repeat_type":"monthly","repeat_day":1}'

# One-time reminder (auto-deletes after firing)
curl -s -X POST http://127.0.0.1:19520/api/tasks \
  -H "Content-Type: application/json" \
  -d '{"time":"17:00","content":"今天下班前提交代码","mode":"simple","repeat_type":"once"}'

# Daily forced break
curl -s -X POST http://127.0.0.1:19520/api/tasks \
  -H "Content-Type: application/json" \
  -d '{"time":"15:00","content":"下午茶休息时间","mode":"rest","lock_minutes":10,"repeat_type":"daily"}'
```

### 3. List Tasks — `GET /api/tasks`

```bash
curl -s http://127.0.0.1:19520/api/tasks
```

### 4. Delete Task — `DELETE /api/tasks/<id>`

```bash
curl -s -X DELETE http://127.0.0.1:19520/api/tasks/<task_id>
```

## Decision Guide

| User says | Use |
|-----------|-----|
| "提醒我…" / "通知我…" (立刻) | `POST /api/notify` |
| "每天 X 点提醒我…" | `POST /api/tasks` with `repeat_type: "daily"` |
| "每周 X 提醒我…" | `POST /api/tasks` with `repeat_type: "weekly"` |
| "每月 X 号提醒我…" | `POST /api/tasks` with `repeat_type: "monthly"` |
| "就这一次，X 点提醒我…" | `POST /api/tasks` with `repeat_type: "once"` |
| "强制我休息…" | mode: `"rest"` with `lock_minutes` |
| "到时间关机" | mode: `"shutdown"` |

## Notes

- All API calls are to `http://127.0.0.1:19520` — local only, no network dependency.
- The `POST /api/notify` endpoint triggers immediately; `POST /api/tasks` schedules for later.
- After creating a task, confirm to the user what was set and when.
- If a task with `repeat_type: "once"` fires while the user is away, it will be auto-deleted — make the user aware of this.
- For `mode: "shutdown"`, warn the user clearly before creating the task.

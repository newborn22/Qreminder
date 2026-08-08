# ⏰ Qreminder

Windows 桌面定时提醒应用 — 到时间自动弹窗，支持简单提醒、强制休息、定时关机。

## 快速开始

```bash
# 源码运行
pip install -r requirements.txt
python main.py

# 打包的 EXE
双击 dist/每日提醒.exe
```

启动后应用出现在**系统托盘**（右下角），右键可打开主窗口或退出。

## 开发模式（Hot Reload）

修改代码后无需手动重启 — 保存文件即自动生效：

```bash
python watcher.py              # 启动热重载模式
python watcher.py --port 8080  # 自定义端口
```

原理：`watcher.py` 监听 `app/` 目录下所有 `.py` 文件的 mtime，检测到变更后自动杀掉旧进程并重启 `main.py`（1~2 秒完成）。从托盘正常退出应用时，watcher 也会跟着退出。

| 模式 | 命令 | 场景 |
|------|------|------|
| 开发 | `python watcher.py` | 改代码，自动生效 |
| 生产 | `python main.py` | 无监视开销，稳定运行 |
| 打包 | `python build_exe.py` | 输出 `.exe` |

## 创建任务

1. 托盘右键 →「打开主窗口」
2. 点击「＋ 新建」
3. 填写：
   - **时间**：下拉选择 HH:MM
   - **内容**：提醒文字
   - **执行方式**：
     - 📋 简单提醒 — 弹窗，点击关闭
     - ☕ 休息模式 — 弹窗置顶 + 需输入 `quit` 才能提前退出
     - 🔌 关机 — 弹窗 + 5 秒倒计时关机
   - **重复方式**：
     - 🔂 单次 — 触发后自动删除
     - 📅 每日 — 每天触发
     - 📆 每周 — 勾选星期几
     - 📌 每月 — 每月指定日期
4. 点击「确定」

## 开机自启

主窗口工具栏右侧点击 `🔕 开机自启: 关` 切换为 `🔔 开机自启: 开`。

## HTTP API（供外部程序/Agent 调用）

应用启动后自动在 `127.0.0.1:19520` 开启 HTTP 服务。

### 端点

| 方法 | 路径 | 说明 |
|------|------|------|
| `GET` | `/api/health` | 健康检查 |
| `GET` | `/api/tasks` | 列出所有任务 |
| `POST` | `/api/tasks` | 创建任务 |
| `GET` | `/api/tasks/<id>` | 查看单个任务 |
| `PUT` | `/api/tasks/<id>` | 更新任务（部分字段） |
| `DELETE` | `/api/tasks/<id>` | 删除任务 |
| `POST` | `/api/notify` | 立即弹出通知（不创建任务） |

### 请求/响应格式

所有请求和响应均为 `application/json`。

**POST /api/tasks** — 创建任务：

```json
{
  "time": "15:00",
  "content": "下午茶时间",
  "mode": "rest",
  "lock_minutes": 10,
  "repeat_type": "daily",
  "repeat_days": [0, 1, 2, 3, 4],
  "repeat_day": 1,
  "enabled": true
}
```

| 字段 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `time` | string | `"09:00"` | HH:MM 格式 |
| `content` | string | `""` | 提醒文字 |
| `mode` | string | `"simple"` | `simple` / `rest` / `shutdown` |
| `lock_minutes` | int | `5` | 休息模式锁定分钟数 (1-60) |
| `repeat_type` | string | `"daily"` | `once` / `daily` / `weekly` / `monthly` |
| `repeat_days` | [int] | `[0,1,2,3,4]` | 每周哪几天 (0=周一, 6=周日) |
| `repeat_day` | int | `1` | 每月几号 (1-31) |
| `enabled` | bool | `true` | 是否启用 |

**POST /api/notify** — 立即弹通知：

```json
{
  "content": "代码审查完成",
  "mode": "simple",
  "lock_minutes": 5
}
```

### curl 示例

```bash
# 立即弹通知
curl -X POST http://127.0.0.1:19520/api/notify \
  -H "Content-Type: application/json" \
  -d '{"content":"休息一下","mode":"rest","lock_minutes":5}'

# 创建每天下午 3 点的任务
curl -X POST http://127.0.0.1:19520/api/tasks \
  -H "Content-Type: application/json" \
  -d '{"time":"15:00","content":"下午茶","mode":"rest","lock_minutes":10}'

# 创建每周一三五的提醒
curl -X POST http://127.0.0.1:19520/api/tasks \
  -H "Content-Type: application/json" \
  -d '{"time":"10:00","content":"站会","mode":"simple","repeat_type":"weekly","repeat_days":[0,2,4]}'

# 列出所有任务
curl http://127.0.0.1:19520/api/tasks
```

### Python 示例

```python
import requests

# 立即通知
requests.post("http://127.0.0.1:19520/api/notify", json={
    "content": "Agent 任务完成！", "mode": "simple"
})

# 创建定时任务
requests.post("http://127.0.0.1:19520/api/tasks", json={
    "time": "17:30", "content": "下班打卡", "mode": "simple"
})
```

## 命令行参数

```bash
python main.py --port 8080     # 自定义 API 端口
python main.py --no-api        # 禁用 API 服务器
每日提醒.exe --port 8080       # EXE 同样支持
```

## 目录结构

```
Qreminder/
├── main.py              # 入口
├── watcher.py           # 开发模式热重载
├── build_exe.py         # 打包脚本 (PyInstaller)
├── requirements.txt
├── app/
│   ├── task_model.py    # 数据模型
│   ├── task_storage.py  # JSON 持久化
│   ├── scheduler.py     # 定时调度
│   ├── notification.py  # 通知弹窗
│   ├── main_window.py   # 主窗口 UI
│   ├── task_dialog.py   # 新建/编辑对话框
│   ├── system_tray.py   # 系统托盘
│   ├── startup.py       # 开机自启
│   └── api_server.py    # HTTP API
├── .claude/skills/
│   └── remind.md        # Claude Code Agent Skill
└── tasks.json           # 任务数据
```

# Minecraft Backup (GUI app)

Cross-platform desktop app to back up your `.minecraft` folder to any folder you choose, with optional scheduled backups and system tray.

**Supports:** Windows, macOS, Linux.

---

## Quick start (double-click)

### 1. Install Python and dependencies

- **Python 3.10+** — [python.org](https://www.python.org/downloads/). On install, check "Add Python to PATH".
- Open a terminal in the `app` folder and run:
  ```bash
  pip install -r requirements.txt
  ```

### 2. Run the app

- **Windows:** Double-click `run_backup_app.bat`, or in a terminal: `python main.py`
- **macOS / Linux:** In a terminal: `python3 main.py` (or make `run_backup_app.sh` executable and double-click it)

### 3. First use

1. **Minecraft folder** — Pre-filled with the default path for your OS. Change it if your `.minecraft` is elsewhere.
2. **Backup destination** — Click "Browse…" and choose where to save the backup (e.g. Dropbox, external drive, another folder).
3. Click **"Backup now"** — When it finishes, you’ll see a popup.
4. Optional: Enable **"Run backups on a schedule"** and pick frequency (hour, 2h, 6h, daily, weekly, or custom). The app can run in the background and show a notification when each backup completes.
5. Optional: Check **"Minimize to system tray when closing"** so closing the window keeps the schedule running; double-click the tray icon to open again.

---

## Where is `.minecraft`?

| OS      | Default path |
|---------|----------------|
| Windows | `%APPDATA%\.minecraft` — Win+R → `%APPDATA%\.minecraft` |
| macOS   | `~/Library/Application Support/minecraft` |
| Linux   | `~/.minecraft` |

The app fills in the correct default for your system. You can browse to another path if needed.

---

## Schedule options

- **Every hour / 2 hours / 6 hours** — Backup at that interval while the app is running (or in tray).
- **Daily / Weekly** — Once per day or once per week.
- **Custom** — Enter a number and choose **hours** or **days**.

When a scheduled backup finishes, a **popup notification** appears (or tray balloon on Windows).

---

## Requirements

- Python 3.10+
- PySide6 (Qt 6) — installed via `requirements.txt`
- For system tray: supported by your OS (Windows, macOS, most Linux desktops)

---

## Building a standalone executable (optional)

To get a single `.exe` (Windows) or app bundle (macOS) for users who don’t have Python:

```bash
pip install pyinstaller
pyinstaller --onefile --windowed --name "MinecraftBackup" main.py
```

The executable will be in `dist/`. Run it from the `app` directory or copy it; the first time you run it, set source and destination in the GUI.

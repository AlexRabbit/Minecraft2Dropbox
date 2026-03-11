#!/usr/bin/env python3
"""
Minecraft Backup — cross-platform GUI to copy .minecraft to a chosen folder,
with optional scheduled backups and system tray.
"""
import sys
from pathlib import Path

# Allow running as script from repo root or from app/
if __name__ == "__main__":
    app_dir = Path(__file__).resolve().parent
    if str(app_dir) not in sys.path:
        sys.path.insert(0, str(app_dir))

from PySide6.QtCore import QCoreApplication
from PySide6.QtWidgets import QApplication
from PySide6.QtGui import QFont

from window import MainWindow


def main():
    QCoreApplication.setOrganizationName("Minecraft2Dropbox")
    QCoreApplication.setApplicationName("BackupApp")

    app = QApplication(sys.argv)
    app.setApplicationDisplayName("Minecraft Backup")

    # Slightly larger default font for readability
    font = app.font()
    if font.pointSize() > 0:
        font.setPointSize(font.pointSize() + 1)
    app.setFont(font)

    window = MainWindow()
    window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()

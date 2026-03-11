"""
Main window UI: source/destination pickers, Backup now, schedule, tray.
"""
import os
from PySide6.QtCore import QSettings, QTimer, Qt
from PySide6.QtGui import QAction
from PySide6.QtWidgets import (
    QApplication,
    QFileDialog,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QCheckBox,
    QComboBox,
    QSpinBox,
    QSystemTrayIcon,
    QVBoxLayout,
    QWidget,
    QMainWindow,
    QMenu,
    QStatusBar,
)

from paths import get_default_minecraft_path, get_platform_name
from backup_worker import BackupThread


SETTINGS_ORG = "Minecraft2Dropbox"
SETTINGS_APP = "BackupApp"


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Minecraft Backup")
        self.setMinimumWidth(520)
        self.setMinimumHeight(380)

        self.settings = QSettings(QSettings.IniFormat, QSettings.UserScope, SETTINGS_ORG, SETTINGS_APP)
        self._backup_thread = None
        self._tray = None
        self._schedule_timer = QTimer(self)
        self._schedule_timer.timeout.connect(self._on_scheduled_backup)

        self._build_ui()
        self._load_settings()
        self._setup_tray()
        self._update_schedule_ui()  # applies schedule (starts timer if enabled)

    def _build_ui(self):
        central = QWidget()
        self.setCentralWidget(central)
        layout = QVBoxLayout(central)

        # --- Source (Minecraft folder) ---
        src_group = QGroupBox("Minecraft folder (source)")
        src_layout = QHBoxLayout(src_group)
        self.source_edit = QLineEdit()
        self.source_edit.setPlaceholderText("Path to .minecraft")
        src_layout.addWidget(self.source_edit)
        browse_src = QPushButton("Browse…")
        browse_src.clicked.connect(self._browse_source)
        src_layout.addWidget(browse_src)
        layout.addWidget(src_group)

        default_src = get_default_minecraft_path()
        if default_src and os.path.isdir(default_src):
            self.source_edit.setText(default_src)
        else:
            self.source_edit.setPlaceholderText(
                f"Default on {get_platform_name()}: {default_src}"
            )

        # --- Destination: parent folder (we create .minecraft inside) or exact .minecraft path ---
        dest_group = QGroupBox("Backup destination")
        dest_layout = QHBoxLayout(dest_group)
        self.dest_edit = QLineEdit()
        self.dest_edit.setPlaceholderText("e.g. D:\\Backups (creates D:\\Backups\\.minecraft) or choose the .minecraft folder itself")
        dest_layout.addWidget(self.dest_edit)
        browse_dest = QPushButton("Browse…")
        browse_dest.clicked.connect(self._browse_destination)
        dest_layout.addWidget(browse_dest)
        layout.addWidget(dest_group)

        # --- Backup now ---
        self.backup_btn = QPushButton("Backup now")
        self.backup_btn.setMinimumHeight(44)
        self.backup_btn.clicked.connect(self._start_backup)
        layout.addWidget(self.backup_btn)

        # --- Schedule ---
        schedule_group = QGroupBox("Schedule (run in background)")
        schedule_layout = QVBoxLayout(schedule_group)

        self.schedule_enabled = QCheckBox("Run backups on a schedule")
        self.schedule_enabled.toggled.connect(self._on_schedule_toggled)
        schedule_layout.addWidget(self.schedule_enabled)

        row = QHBoxLayout()
        row.addWidget(QLabel("Frequency:"))
        self.schedule_combo = QComboBox()
        self.schedule_combo.addItems([
            "Every hour",
            "Every 2 hours",
            "Every 6 hours",
            "Daily",
            "Weekly",
            "Custom",
        ])
        self.schedule_combo.currentTextChanged.connect(self._update_schedule_ui)
        row.addWidget(self.schedule_combo)

        self.custom_spin = QSpinBox()
        self.custom_spin.setMinimum(1)
        self.custom_spin.setMaximum(8760)
        self.custom_spin.setValue(24)
        self.custom_spin.setVisible(False)
        self.custom_spin.valueChanged.connect(self._apply_schedule)
        row.addWidget(self.custom_spin)

        self.custom_unit = QComboBox()
        self.custom_unit.addItems(["hours", "days"])
        self.custom_unit.setVisible(False)
        self.custom_unit.currentIndexChanged.connect(self._apply_schedule)
        row.addWidget(self.custom_unit)

        row.addStretch()
        schedule_layout.addLayout(row)
        layout.addWidget(schedule_group)

        # --- Options ---
        self.minimize_to_tray = QCheckBox("Minimize to system tray when closing (keep scheduling)")
        layout.addWidget(self.minimize_to_tray)

        # --- Status ---
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        self.status_bar.showMessage("Ready")

        layout.addStretch()

    def _browse_source(self):
        start = self.source_edit.text().strip() or os.path.expanduser("~")
        if not os.path.isdir(start):
            start = os.path.expanduser("~")
        path = QFileDialog.getExistingDirectory(self, "Select .minecraft folder", start)
        if path:
            self.source_edit.setText(path)

    def _browse_destination(self):
        start = self.dest_edit.text().strip() or os.path.expanduser("~")
        if not os.path.isdir(start):
            start = os.path.expanduser("~")
        path = QFileDialog.getExistingDirectory(self, "Select folder (the .minecraft folder will be created inside it)", start)
        if path:
            self.dest_edit.setText(path)

    def _update_schedule_ui(self):
        is_custom = self.schedule_combo.currentText() == "Custom"
        self.custom_spin.setVisible(is_custom)
        self.custom_unit.setVisible(is_custom)
        self._apply_schedule()

    def _on_schedule_toggled(self, checked: bool):
        self._apply_schedule()
        if checked:
            self.status_bar.showMessage("Scheduled backup enabled")
        else:
            self._schedule_timer.stop()
            self.status_bar.showMessage("Scheduling stopped")

    def _interval_seconds(self) -> int:
        """Return scheduled interval in seconds, or 0 if disabled."""
        if not self.schedule_enabled.isChecked():
            return 0
        text = self.schedule_combo.currentText()
        if text == "Every hour":
            return 3600
        if text == "Every 2 hours":
            return 2 * 3600
        if text == "Every 6 hours":
            return 6 * 3600
        if text == "Daily":
            return 24 * 3600
        if text == "Weekly":
            return 7 * 24 * 3600
        if text == "Custom":
            n = self.custom_spin.value()
            if self.custom_unit.currentText() == "days":
                return n * 24 * 3600
            return n * 3600
        return 0

    def _apply_schedule(self):
        sec = self._interval_seconds()
        if sec > 0:
            self._schedule_timer.start(sec * 1000)
        else:
            self._schedule_timer.stop()

    def _start_backup(self):
        src = self.source_edit.text().strip()
        dest = self.dest_edit.text().strip()

        if not src:
            QMessageBox.warning(
                self,
                "Source missing",
                "Please set the Minecraft folder (source).\n\n"
                f"On {get_platform_name()} the default is usually:\n"
                f"{get_default_minecraft_path()}",
            )
            return
        if not dest:
            QMessageBox.warning(
                self,
                "Destination missing",
                "Please choose where to save the backup.",
            )
            return
        if not os.path.isdir(src):
            QMessageBox.critical(
                self,
                "Source not found",
                f"This folder does not exist:\n{src}\n\nRun Minecraft at least once to create it.",
            )
            return
        # Destination can be a parent folder (we create .minecraft inside) or the exact folder path
        if not os.path.isdir(dest) and dest:
            parent = os.path.dirname(dest)
            if parent and not os.path.isdir(parent):
                QMessageBox.warning(
                    self,
                    "Destination invalid",
                    "The destination folder (or its parent) does not exist. Create it or choose an existing folder.",
                )
                return

        self._run_backup(src, dest, show_popup=True)

    def _run_backup(self, source: str, destination: str, show_popup: bool = False):
        """Start backup in background thread. show_popup: show tray/dialog when done."""
        self.backup_btn.setEnabled(False)
        self.status_bar.showMessage("Backup in progress…")

        self._backup_thread = BackupThread(source, destination)

        def on_progress(msg):
            self.status_bar.showMessage(msg)

        def on_finished():
            self.backup_btn.setEnabled(True)
            self.status_bar.showMessage("Backup completed.")
            self._show_backup_done(show_popup, success=True)
            self._backup_thread = None

        def on_failed(msg):
            self.backup_btn.setEnabled(True)
            self.status_bar.showMessage("Backup failed.")
            self._show_backup_done(show_popup, success=False, message=msg)
            self._backup_thread = None

        self._backup_thread.progress.connect(on_progress)
        self._backup_thread.backup_finished.connect(on_finished)
        self._backup_thread.backup_failed.connect(on_failed)

        self._backup_thread.start()

    def _show_backup_done(self, show_popup: bool, success: bool, message: str = ""):
        if not show_popup:
            return
        if success:
            title = "Minecraft Backup"
            text = "Backup completed successfully."
            if self._tray and self._tray.isVisible():
                self._tray.showMessage(title, text, QSystemTrayIcon.Information, 4000)
            else:
                QMessageBox.information(self, title, text)
        else:
            QMessageBox.critical(self, "Backup failed", message or "Unknown error.")

    def _on_scheduled_backup(self):
        src = self.source_edit.text().strip()
        dest = self.dest_edit.text().strip()
        if src and dest and os.path.isdir(src):
            self._run_backup(src, dest, show_popup=True)
        else:
            self.status_bar.showMessage("Scheduled backup skipped (check source/destination)")

    def _setup_tray(self):
        if not QSystemTrayIcon.isSystemTrayAvailable():
            return
        self._tray = QSystemTrayIcon(self)
        try:
            from PySide6.QtWidgets import QStyle
            self._tray.setIcon(self.style().standardIcon(QStyle.StandardPixmap.SP_ComputerIcon))
        except Exception:
            pass
        self._tray.setToolTip("Minecraft Backup")

        tray_menu = QMenu()
        backup_action = QAction("Backup now", self)
        backup_action.triggered.connect(self._start_backup)
        tray_menu.addAction(backup_action)
        open_action = QAction("Open", self)
        open_action.triggered.connect(self._show_window)
        tray_menu.addAction(open_action)
        quit_action = QAction("Quit", self)
        quit_action.triggered.connect(QApplication.quit)
        tray_menu.addAction(quit_action)
        self._tray.setContextMenu(tray_menu)
        self._tray.activated.connect(self._on_tray_activated)
        self._tray.show()

    def _on_tray_activated(self, reason):
        if reason == QSystemTrayIcon.DoubleClick or reason == QSystemTrayIcon.Trigger:
            self._show_window()

    def _show_window(self):
        self.show()
        self.raise_()
        self.activateWindow()

    def closeEvent(self, event):
        if self.minimize_to_tray.isChecked() and self._tray and QSystemTrayIcon.isSystemTrayAvailable():
            self.hide()
            event.ignore()
        else:
            self._save_settings()
            event.accept()

    def _load_settings(self):
        self.settings.beginGroup("Paths")
        src = self.settings.value("source", "")
        dest = self.settings.value("destination", "")
        self.settings.endGroup()
        if src:
            self.source_edit.setText(src)
        elif not self.source_edit.text():
            self.source_edit.setText(get_default_minecraft_path())
        if dest:
            self.dest_edit.setText(dest)

        self.settings.beginGroup("Schedule")
        self.schedule_enabled.setChecked(self.settings.value("enabled", False, type=bool))
        idx = self.settings.value("frequencyIndex", 0, type=int)
        self.schedule_combo.setCurrentIndex(min(idx, self.schedule_combo.count() - 1))
        self.custom_spin.setValue(self.settings.value("customValue", 24, type=int))
        self.custom_unit.setCurrentIndex(self.settings.value("customUnit", 0, type=int))
        self.settings.endGroup()

        self.settings.beginGroup("Window")
        self.minimize_to_tray.setChecked(self.settings.value("minimizeToTray", False, type=bool))
        self.settings.endGroup()

    def _save_settings(self):
        self.settings.beginGroup("Paths")
        self.settings.setValue("source", self.source_edit.text().strip())
        self.settings.setValue("destination", self.dest_edit.text().strip())
        self.settings.endGroup()

        self.settings.beginGroup("Schedule")
        self.settings.setValue("enabled", self.schedule_enabled.isChecked())
        self.settings.setValue("frequencyIndex", self.schedule_combo.currentIndex())
        self.settings.setValue("customValue", self.custom_spin.value())
        self.settings.setValue("customUnit", self.custom_unit.currentIndex())
        self.settings.endGroup()

        self.settings.beginGroup("Window")
        self.settings.setValue("minimizeToTray", self.minimize_to_tray.isChecked())
        self.settings.endGroup()

        self.settings.sync()

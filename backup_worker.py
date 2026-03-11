"""
Background thread that copies the .minecraft folder to the destination.
Runs the copy inside QThread.run(). Keeps the .minecraft folder name so everything stays organized.
"""
import os
import shutil
from PySide6.QtCore import QThread, Signal


class BackupThread(QThread):
    """Runs backup in its own thread. Emits progress and done/failed."""

    progress = Signal(str)
    backup_finished = Signal()
    backup_failed = Signal(str)

    def __init__(self, source: str, destination: str, parent=None):
        super().__init__(parent)
        self._source = os.path.normpath(os.path.abspath(source))
        self._destination_input = os.path.normpath(os.path.abspath(destination))
        self._cancelled = False

    def cancel(self):
        self._cancelled = True

    def run(self):
        try:
            if not os.path.isdir(self._source):
                self.backup_failed.emit(f"Source folder does not exist:\n{self._source}")
                return

            # Source folder name (e.g. ".minecraft")
            source_folder_name = os.path.basename(self._source)

            # If user already selected the .minecraft folder, use it as destination.
            # Otherwise treat selection as parent: copy to parent/.minecraft/
            dest_input_basename = os.path.basename(self._destination_input.rstrip(os.sep))
            if dest_input_basename == source_folder_name:
                destination = self._destination_input
            else:
                destination = os.path.join(self._destination_input, source_folder_name)

            # Don't copy onto ourselves
            if os.path.normpath(os.path.abspath(destination)) == self._source:
                self.backup_failed.emit("Source and destination are the same folder.")
                return

            parent_dir = os.path.dirname(destination)
            if parent_dir and not os.path.isdir(parent_dir):
                try:
                    os.makedirs(parent_dir, exist_ok=True)
                except OSError as e:
                    self.backup_failed.emit(f"Cannot create folder:\n{e}")
                    return

            self.progress.emit("Copying .minecraft folder…")

            # One code path: copytree with dirs_exist_ok handles both new and existing destination
            try:
                shutil.copytree(
                    self._source,
                    destination,
                    dirs_exist_ok=True,
                    copy_function=shutil.copy2,
                )
            except (OSError, shutil.Error) as e:
                self.backup_failed.emit(str(e))
                return

            if self._cancelled:
                self.backup_failed.emit("Backup cancelled.")
                return

            self.progress.emit("Done.")
            self.backup_finished.emit()
        except Exception as e:
            self.backup_failed.emit(str(e))

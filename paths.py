"""
Cross-platform paths for the Minecraft folder.
"""
import os
import sys


def get_default_minecraft_path() -> str:
    """Return the default .minecraft path for the current OS."""
    if sys.platform == "win32":
        appdata = os.environ.get("APPDATA", "")
        return os.path.join(appdata, ".minecraft") if appdata else ""
    if sys.platform == "darwin":
        return os.path.expanduser("~/Library/Application Support/minecraft")
    # Linux and other Unix-like
    return os.path.expanduser("~/.minecraft")


def get_platform_name() -> str:
    """Return display name for current platform."""
    if sys.platform == "win32":
        return "Windows"
    if sys.platform == "darwin":
        return "macOS"
    return "Linux"

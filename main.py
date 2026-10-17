"""
main.py — Entry point for the Voice-Based Form Filling System.

Run:
    python main.py

Keyboard shortcuts:
    F5   → Voice Form
    F6   → Manual Form
    F7   → Dashboard
    F8   → Toggle Dark/Light Mode
    Ctrl+Q → Quit
    Ctrl+E → Export Excel
    Ctrl+P → Export PDF
"""

import os
import sys
import logging
from datetime import datetime

# ─────────────────────────────────────────────
# Ensure the project root is on sys.path
# ─────────────────────────────────────────────
PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from config import (
    APP_TITLE, APP_VERSION, LOG_FILE, LOGS_DIR,
    DB_DIR, EXCEL_DIR, PDF_DIR, SCREENSHOTS,
)


# ─────────────────────────────────────────────
# Logging setup
# ─────────────────────────────────────────────
def setup_logging():
    """Configure root logger with both file and console handlers."""
    os.makedirs(LOGS_DIR, exist_ok=True)

    fmt     = "%(asctime)s  %(levelname)-8s  %(name)s — %(message)s"
    datefmt = "%Y-%m-%d %H:%M:%S"

    root_logger = logging.getLogger()
    root_logger.setLevel(logging.DEBUG)

    # File handler — full DEBUG output
    fh = logging.FileHandler(LOG_FILE, encoding="utf-8")
    fh.setLevel(logging.DEBUG)
    fh.setFormatter(logging.Formatter(fmt, datefmt))

    # Console handler — INFO+
    ch = logging.StreamHandler()
    ch.setLevel(logging.INFO)
    ch.setFormatter(logging.Formatter(fmt, datefmt))

    root_logger.addHandler(fh)
    root_logger.addHandler(ch)

    logging.info("=" * 70)
    logging.info("  %s  v%s  —  Started %s", APP_TITLE, APP_VERSION,
                 datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
    logging.info("=" * 70)


# ─────────────────────────────────────────────
# Ensure required directories exist
# ─────────────────────────────────────────────
def ensure_dirs():
    for path in (DB_DIR, EXCEL_DIR, PDF_DIR, SCREENSHOTS, LOGS_DIR):
        os.makedirs(path, exist_ok=True)


# ─────────────────────────────────────────────
# Dependency check
# ─────────────────────────────────────────────
def check_dependencies() -> list[str]:
    """
    Return a list of missing packages.
    Non-fatal — the app may still work partially without optional packages.
    """
    required = {
        "customtkinter":     "customtkinter",
        "PIL":               "Pillow",
        "speech_recognition":"SpeechRecognition",
        "sounddevice":       "sounddevice",
        "scipy":             "scipy",
        "numpy":             "numpy",
        "pyttsx3":           "pyttsx3",
        "pandas":            "pandas",
        "openpyxl":          "openpyxl",
        "reportlab":         "reportlab",
    }
    missing = []
    for module, package in required.items():
        try:
            __import__(module)
        except ImportError:
            missing.append(package)
    return missing


# ─────────────────────────────────────────────
# Main
# ─────────────────────────────────────────────
def main():
    setup_logging()
    ensure_dirs()
    logger = logging.getLogger("main")

    # Dependency check
    missing = check_dependencies()
    if missing:
        logger.warning("Missing packages: %s", missing)
        try:
            import tkinter as tk
            from tkinter import messagebox
            root = tk.Tk()
            root.withdraw()
            messagebox.showwarning(
                "Missing Dependencies",
                f"The following packages are not installed:\n\n"
                + "\n".join(f"  • {p}" for p in missing)
                + "\n\nPlease run:\n  pip install "
                + " ".join(missing)
                + "\n\nThe application will attempt to continue.",
            )
            root.destroy()
        except Exception:
            print(f"WARNING: Missing packages: {missing}")

    # Launch GUI
    try:
        from gui import Application
        logger.info("Launching GUI…")
        app = Application()
        app.mainloop()
        logger.info("Application closed normally.")
    except Exception as exc:
        logger.critical("Fatal error: %s", exc, exc_info=True)
        try:
            import tkinter as tk
            from tkinter import messagebox
            root = tk.Tk()
            root.withdraw()
            messagebox.showerror(
                "Fatal Error",
                f"The application encountered a fatal error:\n\n{exc}\n\n"
                "Please check logs/application.log for details.",
            )
            root.destroy()
        except Exception:
            print(f"FATAL: {exc}")
        sys.exit(1)


if __name__ == "__main__":
    main()

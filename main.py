"""
System Health Monitoring - Main Entry Point
=================================

Intelligent Desktop System Observability and Anomaly Response Tool

This is a desktop application for monitoring system resources (CPU, RAM, Disk),
detecting anomalies, and providing alerts for unusual system behavior.

Project: Final Year BCA Project
Author: Mallikarjun
Year: 2026
"""

import sys
import os
import logging
from logging.handlers import RotatingFileHandler

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import config

# ---------------------------------------------------------------------------
# Logging setup — rotating file + console
# ---------------------------------------------------------------------------
_log_formatter = logging.Formatter(
    "%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)

_file_handler = RotatingFileHandler(
    config.LOG_FILE, maxBytes=5 * 1024 * 1024, backupCount=3, encoding="utf-8"
)
_file_handler.setFormatter(_log_formatter)
_file_handler.setLevel(logging.DEBUG)

_console_handler = logging.StreamHandler(sys.stdout)
_console_handler.setFormatter(_log_formatter)
_console_handler.setLevel(logging.INFO)

logging.basicConfig(level=logging.DEBUG, handlers=[_file_handler, _console_handler])
logger = logging.getLogger("SystemHealthMonitoring")


def setup_application():
    """
    Set up the Qt application with proper configuration.

    Returns:
        QApplication: Configured Qt application instance
    """
    from PySide6.QtWidgets import QApplication

    app = QApplication(sys.argv)

    # Set application properties
    app.setApplicationName(config.APP_NAME)
    app.setApplicationVersion(config.VERSION)
    app.setOrganizationName("BCA Project")

    # Set style
    app.setStyle('Fusion')

    return app


def check_dependencies():
    """
    Check if all required dependencies are installed.

    Returns:
        bool: True if all dependencies are available
    """
    missing_deps = []

    # Check PySide6
    try:
        from PySide6 import QtCore, QtWidgets, QtGui
    except ImportError:
        missing_deps.append("PySide6")

    # Check psutil
    try:
        import psutil
    except ImportError:
        missing_deps.append("psutil")

    if missing_deps:
        logger.error("Missing required dependencies: %s", ", ".join(missing_deps))
        print("=" * 60)
        print("ERROR: Missing required dependencies!")
        print("=" * 60)
        print(f"Please install the following packages:")
        for dep in missing_deps:
            print(f"  - {dep}")
        print()
        print("Install using pip:")
        print(f"  pip install {' '.join(missing_deps)}")
        print("=" * 60)
        return False

    return True


def main():
    """
    Main entry point for the System Health Monitoring application.

    This function:
    1. Checks for required dependencies
    2. Sets up the Qt application
    3. Creates and displays the main window
    4. Runs the application event loop
    """
    # Print startup banner
    print("=" * 60)
    print(f"  {config.APP_NAME} v{config.VERSION}")
    print("  Intelligent Desktop System Observability and")
    print("                  Anomaly Response Tool")
    print(f"  Author: {config.AUTHOR}")
    print("=" * 60)
    print()

    logger.info("Application starting — v%s", config.VERSION)
    logger.info("Log file: %s", config.LOG_FILE)
    logger.info("Refresh interval: %d second(s)", config.REFRESH_INTERVAL)

    # Check dependencies
    if not check_dependencies():
        input("Press Enter to exit...")
        sys.exit(1)

    # Setup application
    app = setup_application()

    # Create main window
    try:
        from ui.main_window import MainWindow

        window = MainWindow()
        window.show()
        logger.info("Main window displayed successfully")
        print()
        print("Application is running. Close the window to exit.")
        print("=" * 60)

    except Exception as e:
        logger.critical("Failed to create main window: %s", e, exc_info=True)
        # Show a GUI error dialog if possible
        try:
            from PySide6.QtWidgets import QMessageBox
            QMessageBox.critical(
                None,
                "Startup Error",
                f"Failed to start the application:\n\n{e}\n\nCheck logs/system.log for details.",
            )
        except Exception:
            pass
        input("Press Enter to exit...")
        sys.exit(1)

    # Run application event loop
    exit_code = app.exec()

    logger.info("Application closed (exit code %d)", exit_code)
    sys.exit(exit_code)


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        logger.critical("Unhandled exception: %s", e, exc_info=True)
        print(f"\nFATAL ERROR: {e}")
        input("Press Enter to exit...")
        sys.exit(1)

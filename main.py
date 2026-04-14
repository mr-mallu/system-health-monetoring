"""
System Health Monitoring - Main Entry Point
=================================

Intelligent Desktop System Observability and Anomaly Response Tool

This is a desktop application for monitoring system resources (CPU, RAM, Disk),
detecting anomalies, and providing alerts for unusual system behavior.

Project: Final Year BCA Project
Author: Student Name
Year: 2024
"""

import sys
import os

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from PySide6.QtWidgets import QApplication, QMessageBox
from PySide6.QtCore import Qt

from ui.main_window import MainWindow
import config


def setup_application():
    """
    Set up the Qt application with proper configuration.
    
    Returns:
        QApplication: Configured Qt application instance
    """
    # Create application
    app = QApplication(sys.argv)
    
    # Set application properties
    app.setApplicationName("System Health Monitoring")
    app.setApplicationVersion("1.0.0")
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
    print("  System Health Monitoring - Desktop Monitoring Tool")
    print("  Intelligent Desktop System Observability and")
    print("                  Anomaly Response Tool")
    print("=" * 60)
    print()
    print("Starting application...")
    print(f"Log file: {config.LOG_FILE}")
    print(f"Refresh interval: {config.REFRESH_INTERVAL} second(s)")
    print()
    
    # Check dependencies
    if not check_dependencies():
        input("Press Enter to exit...")
        sys.exit(1)
    
    # Setup application
    app = setup_application()
    
    # Create main window
    try:
        window = MainWindow()
        window.show()
        print("Main window displayed successfully!")
        print()
        print("Application is running. Close the window to exit.")
        print("=" * 60)
        
    except Exception as e:
        print(f"ERROR: Failed to create main window: {e}")
        import traceback
        traceback.print_exc()
        input("Press Enter to exit...")
        sys.exit(1)
    
    # Run application event loop
    exit_code = app.exec()
    
    print()
    print("Application closed.")
    sys.exit(exit_code)


if __name__ == "__main__":
    main()


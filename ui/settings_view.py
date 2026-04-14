"""
Settings View Module
Provides user interface for managing application settings.
"""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGroupBox,
    QLabel, QCheckBox, QPushButton, QSpinBox,
    QComboBox, QScrollArea, QMessageBox, QLineEdit,
    QGridLayout, QFormLayout
)
from PySide6.QtCore import Signal, Qt
from PySide6.QtGui import QFont

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import config
from backend.database import get_database


class SettingsView(QWidget):
    """
    Settings management interface.
    Allows users to enable/disable features and customize behavior.
    """
    
    # Signal emitted when settings change
    settings_changed = Signal(dict)
    
    def __init__(self, parent=None):
        """Initialize settings view."""
        super().__init__(parent)
        
        # Get database instance
        self.db = get_database()
        
        # Current settings
        self.settings = {}
        self._loading_settings = False
        
        # Initialize UI
        self.init_ui()
        
        # Load current settings
        self.load_settings()
    
    def init_ui(self):
        """Initialize the user interface."""
        layout = QVBoxLayout(self)
        
        # Title
        title = QLabel("⚙️ Settings")
        title_font = QFont()
        title_font.setPointSize(16)
        title_font.setBold(True)
        title.setFont(title_font)
        layout.addWidget(title)
        
        # Create scroll area
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        
        scroll_content = QWidget()
        scroll_layout = QVBoxLayout(scroll_content)
        
        # Create settings groups
        scroll_layout.addWidget(self.create_monitoring_group())
        scroll_layout.addWidget(self.create_alerts_group())
        scroll_layout.addWidget(self.create_suggestions_group())
        scroll_layout.addWidget(self.create_appearance_group())
        scroll_layout.addWidget(self.create_database_group())
        
        scroll_layout.addStretch()
        
        scroll.setWidget(scroll_content)
        layout.addWidget(scroll)
        
        # Buttons
        button_layout = QHBoxLayout()
        auto_save_label = QLabel("Settings are applied automatically")
        button_layout.addWidget(auto_save_label)
        
        self.reset_btn = QPushButton("Reset to Defaults")
        self.reset_btn.clicked.connect(self.reset_to_defaults)
        button_layout.addWidget(self.reset_btn)
        
        button_layout.addStretch()
        
        layout.addLayout(button_layout)
        
        # Auto-save settings when controls change
        self._setup_auto_save()
    
    def create_monitoring_group(self) -> QGroupBox:
        """Create monitoring settings group."""
        group = QGroupBox("📊 Monitoring")
        layout = QVBoxLayout(group)
        
        # Enable monitoring
        self.enable_monitoring_cb = QCheckBox("Enable System Monitoring")
        self.enable_monitoring_cb.setToolTip(
            "Enable real-time monitoring of CPU, RAM, and Disk usage"
        )
        layout.addWidget(self.enable_monitoring_cb)
        
        # Enable anomaly detection
        self.enable_anomaly_cb = QCheckBox("Enable Anomaly Detection")
        self.enable_anomaly_cb.setToolTip(
            "Detect unusual system behavior based on historical patterns"
        )
        layout.addWidget(self.enable_anomaly_cb)
        
        # Refresh interval
        interval_layout = QHBoxLayout()
        interval_layout.addWidget(QLabel("Refresh Interval:"))
        
        self.refresh_interval_spin = QSpinBox()
        self.refresh_interval_spin.setRange(1, 60)
        self.refresh_interval_spin.setSuffix(" seconds")
        self.refresh_interval_spin.setToolTip(
            "How often to update system metrics"
        )
        interval_layout.addWidget(self.refresh_interval_spin)
        interval_layout.addStretch()
        
        layout.addLayout(interval_layout)
        
        return group
    
    def create_alerts_group(self) -> QGroupBox:
        """Create alert settings group."""
        group = QGroupBox("🔔 Alerts")
        layout = QVBoxLayout(group)
        
        # Enable popup alerts
        self.enable_popup_alerts_cb = QCheckBox("Enable Popup Alerts")
        self.enable_popup_alerts_cb.setToolTip(
            "Show desktop popup for critical alerts"
        )
        layout.addWidget(self.enable_popup_alerts_cb)
        
        # Enable tray notifications
        self.enable_tray_notifications_cb = QCheckBox("Enable System Tray Notifications")
        self.enable_tray_notifications_cb.setToolTip(
            "Show notifications in system tray for medium priority alerts"
        )
        layout.addWidget(self.enable_tray_notifications_cb)
        
        # Alert cooldown
        cooldown_layout = QHBoxLayout()
        cooldown_layout.addWidget(QLabel("Alert Cooldown:"))
        
        self.alert_cooldown_spin = QSpinBox()
        self.alert_cooldown_spin.setRange(5, 300)
        self.alert_cooldown_spin.setSuffix(" seconds")
        self.alert_cooldown_spin.setToolTip(
            "Minimum time between repeated alerts of the same type"
        )
        cooldown_layout.addWidget(self.alert_cooldown_spin)
        cooldown_layout.addStretch()
        
        layout.addLayout(cooldown_layout)
        
        return group
    
    def create_suggestions_group(self) -> QGroupBox:
        """Create suggestions settings group."""
        group = QGroupBox("💡 Suggestions")
        layout = QVBoxLayout(group)
        
        # Enable startup suggestions
        self.enable_startup_suggestions_cb = QCheckBox("Enable Startup Program Suggestions")
        self.enable_startup_suggestions_cb.setToolTip(
            "Analyze startup programs and suggest safe ones to disable"
        )
        layout.addWidget(self.enable_startup_suggestions_cb)
        
        # Enable cache cleanup suggestions
        self.enable_cache_cleanup_cb = QCheckBox("Enable Cache Cleanup Suggestions")
        self.enable_cache_cleanup_cb.setToolTip(
            "Analyze temporary files and suggest cleanup"
        )
        layout.addWidget(self.enable_cache_cleanup_cb)
        
        return group
    
    def create_appearance_group(self) -> QGroupBox:
        """Create appearance settings group."""
        group = QGroupBox("🎨 Appearance")
        layout = QVBoxLayout(group)
        
        # Theme selection
        theme_layout = QHBoxLayout()
        theme_layout.addWidget(QLabel("Theme:"))
        
        self.theme_combo = QComboBox()
        self.theme_combo.addItems(["Dark", "Light"])
        self.theme_combo.setToolTip("Application color theme")
        theme_layout.addWidget(self.theme_combo)
        theme_layout.addStretch()
        
        layout.addLayout(theme_layout)
        
        return group
    
    def create_database_group(self) -> QGroupBox:
        """Create database management group."""
        group = QGroupBox("💾 Database")
        layout = QVBoxLayout(group)
        
        # Database stats
        self.db_stats_label = QLabel("Loading database stats...")
        layout.addWidget(self.db_stats_label)
        
        # Cleanup button
        cleanup_layout = QHBoxLayout()
        
        cleanup_btn = QPushButton("Cleanup Old Data")
        cleanup_btn.setToolTip("Remove data older than 7 days")
        cleanup_btn.clicked.connect(self.cleanup_database)
        cleanup_layout.addWidget(cleanup_btn)
        
        cleanup_layout.addStretch()
        
        layout.addLayout(cleanup_layout)
        
        return group
    
    def load_settings(self):
        """Load settings from database."""
        # Get all settings from database
        self.settings = self.db.get_all_settings()
        self._loading_settings = True
        
        # Apply to UI
        self.enable_monitoring_cb.setChecked(
            self.settings.get('enable_monitoring', True)
        )
        self.enable_anomaly_cb.setChecked(
            self.settings.get('enable_anomaly_detection', True)
        )
        self.enable_popup_alerts_cb.setChecked(
            self.settings.get('enable_popup_alerts', True)
        )
        self.enable_tray_notifications_cb.setChecked(
            self.settings.get('enable_tray_notifications', True)
        )
        self.enable_startup_suggestions_cb.setChecked(
            self.settings.get('enable_startup_suggestions', True)
        )
        self.enable_cache_cleanup_cb.setChecked(
            self.settings.get('enable_cache_cleanup_suggestions', True)
        )
        
        self.refresh_interval_spin.setValue(
            self.settings.get('refresh_interval', 1)
        )
        self.alert_cooldown_spin.setValue(
            self.settings.get('alert_cooldown_seconds', config.ALERT_COOLDOWN_DEFAULT)
        )
        
        theme = self.settings.get('theme', 'dark')
        self.theme_combo.setCurrentText(theme.capitalize())
        self._loading_settings = False
        
        # Update database stats
        self.update_database_stats()

    def _setup_auto_save(self):
        """Connect settings widgets for immediate apply/save."""
        self.enable_monitoring_cb.toggled.connect(
            lambda v: self._save_single_setting('enable_monitoring', v)
        )
        self.enable_anomaly_cb.toggled.connect(
            lambda v: self._save_single_setting('enable_anomaly_detection', v)
        )
        self.enable_popup_alerts_cb.toggled.connect(
            lambda v: self._save_single_setting('enable_popup_alerts', v)
        )
        self.enable_tray_notifications_cb.toggled.connect(
            lambda v: self._save_single_setting('enable_tray_notifications', v)
        )
        self.enable_startup_suggestions_cb.toggled.connect(
            lambda v: self._save_single_setting('enable_startup_suggestions', v)
        )
        self.enable_cache_cleanup_cb.toggled.connect(
            lambda v: self._save_single_setting('enable_cache_cleanup_suggestions', v)
        )
        self.refresh_interval_spin.valueChanged.connect(
            lambda v: self._save_single_setting('refresh_interval', v)
        )
        self.alert_cooldown_spin.valueChanged.connect(
            lambda v: self._save_single_setting('alert_cooldown_seconds', v)
        )
        self.theme_combo.currentTextChanged.connect(
            lambda t: self._save_single_setting('theme', t.lower())
        )

    def _save_single_setting(self, key, value):
        """Save one setting immediately and notify listeners."""
        if self._loading_settings:
            return
        self.db.set_setting(key, value)
        self.settings[key] = value
        self.settings_changed.emit({key: value})

    def save_settings(self):
        """Save settings to database."""
        # Kept for compatibility; settings are now auto-saved on change.
        if not self._loading_settings:
            QMessageBox.information(
                self,
                "Auto Save Enabled",
                "Settings now apply immediately. No manual save is required."
            )
            return

        # Collect settings
        new_settings = {
            'enable_monitoring': self.enable_monitoring_cb.isChecked(),
            'enable_anomaly_detection': self.enable_anomaly_cb.isChecked(),
            'enable_popup_alerts': self.enable_popup_alerts_cb.isChecked(),
            'enable_tray_notifications': self.enable_tray_notifications_cb.isChecked(),
            'enable_startup_suggestions': self.enable_startup_suggestions_cb.isChecked(),
            'enable_cache_cleanup_suggestions': self.enable_cache_cleanup_cb.isChecked(),
            'refresh_interval': self.refresh_interval_spin.value(),
            'alert_cooldown_seconds': self.alert_cooldown_spin.value(),
            'theme': self.theme_combo.currentText().lower()
        }
        
        # Save each setting
        for key, value in new_settings.items():
            self.db.set_setting(key, value)
        
        # Update current settings
        self.settings = new_settings
        
        # Emit signal
        self.settings_changed.emit(new_settings)
        
        # Show confirmation
        QMessageBox.information(
            self,
            "Settings Saved",
            "Your settings have been saved successfully!\n\n"
            "Some changes may require restarting the application."
        )
    
    def reset_to_defaults(self):
        """Reset all settings to default values."""
        reply = QMessageBox.question(
            self,
            "Reset Settings",
            "Are you sure you want to reset all settings to default values?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            # Set defaults
            defaults = {
                'enable_monitoring': True,
                'enable_anomaly_detection': True,
                'enable_popup_alerts': True,
                'enable_tray_notifications': True,
                'enable_startup_suggestions': True,
                'enable_cache_cleanup_suggestions': True,
                'refresh_interval': 1,
                'alert_cooldown_seconds': config.ALERT_COOLDOWN_DEFAULT,
                'theme': 'dark'
            }
            
            # Save defaults
            for key, value in defaults.items():
                self.db.set_setting(key, value)
            
            # Reload UI
            self.load_settings()
            
            # Emit signal
            self.settings_changed.emit(defaults)
            
            QMessageBox.information(
                self,
                "Settings Reset",
                "All settings have been reset to default values."
            )
    
    def cleanup_database(self):
        """Clean up old data from database."""
        reply = QMessageBox.question(
            self,
            "Cleanup Database",
            "This will remove all data older than 7 days.\n\n"
            "Are you sure you want to continue?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            result = self.db.cleanup_old_data(7)
            
            QMessageBox.information(
                self,
                "Cleanup Complete",
                f"Cleaned up:\n"
                f"- {result['metrics_deleted']} metric records\n"
                f"- {result['alerts_deleted']} alert records\n"
                f"- {result['process_deleted']} process records"
            )
            
            # Update stats display
            self.update_database_stats()
    
    def update_database_stats(self):
        """Update database statistics display."""
        stats = self.db.get_database_stats()
        
        size_mb = stats.get('database_size_bytes', 0) / (1024 * 1024)
        
        self.db_stats_label.setText(
            f"Records: {stats.get('system_metrics_count', 0)} metrics, "
            f"{stats.get('alerts_count', 0)} alerts, "
            f"{stats.get('process_history_count', 0)} processes\n"
            f"Database size: {size_mb:.2f} MB"
        )
    
    def get_settings(self) -> dict:
        """Get current settings dictionary."""
        return self.settings.copy()
    
    def apply_theme(self, theme_name: str):
        """Apply theme to the application."""
        # This would typically be called from main window
        # to apply the QSS theme
        pass

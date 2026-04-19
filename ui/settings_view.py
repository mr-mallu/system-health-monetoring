"""
Settings View Module
Provides user interface for managing application settings.
Features premium toggle switches instead of plain checkboxes.
"""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGroupBox,
    QLabel, QPushButton, QSpinBox,
    QComboBox, QScrollArea, QMessageBox, QFormLayout
)
from PySide6.QtCore import Signal, Qt, QSize, Property, QPropertyAnimation, QEasingCurve, QRect
from PySide6.QtGui import QFont, QPainter, QColor, QPen

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import config
from backend.database import get_database


class ToggleSwitch(QWidget):
    """
    Premium animated toggle switch widget.
    Replaces plain QCheckBox with a modern, iOS-style toggle.
    """
    toggled = Signal(bool)

    def __init__(self, parent=None, initial=False):
        super().__init__(parent)
        self._checked = initial
        self._thumb_pos = 22.0 if initial else 2.0
        self.setFixedSize(QSize(48, 26))
        self.setCursor(Qt.PointingHandCursor)

        self._animation = QPropertyAnimation(self, b"thumb_pos")
        self._animation.setDuration(200)
        self._animation.setEasingCurve(QEasingCurve.InOutCubic)

    def _get_thumb_pos(self):
        return self._thumb_pos

    def _set_thumb_pos(self, pos):
        self._thumb_pos = pos
        self.update()

    thumb_pos = Property(float, _get_thumb_pos, _set_thumb_pos)

    def isChecked(self):
        return self._checked

    def setChecked(self, checked):
        if self._checked == checked:
            return
        self._checked = checked
        self._animate()
        self.toggled.emit(self._checked)

    def _animate(self):
        self._animation.stop()
        self._animation.setStartValue(self._thumb_pos)
        self._animation.setEndValue(22.0 if self._checked else 2.0)
        self._animation.start()

    def mousePressEvent(self, event):
        self._checked = not self._checked
        self._animate()
        self.toggled.emit(self._checked)

    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)

        # Track
        track_color = QColor("#4cd964") if self._checked else QColor("#555555")
        p.setBrush(track_color)
        p.setPen(Qt.NoPen)
        p.drawRoundedRect(0, 0, self.width(), self.height(), 13, 13)

        # Thumb (circle)
        p.setBrush(QColor("#ffffff"))
        p.setPen(QPen(QColor("#cccccc"), 0.5))
        p.drawEllipse(int(self._thumb_pos), 2, 22, 22)
        p.end()


class SettingsView(QWidget):
    """
    Settings management interface.
    Allows users to enable/disable features and customize behavior.
    Uses premium animated toggle switches.
    """
    
    settings_changed = Signal(dict)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.db = get_database()
        self.settings = {}
        self._loading_settings = False
        
        self.init_ui()
        self.load_settings()
    
    def init_ui(self):
        layout = QVBoxLayout(self)
        
        # Title
        title = QLabel("⚙️ Settings")
        title_font = QFont()
        title_font.setPointSize(16)
        title_font.setBold(True)
        title.setFont(title_font)
        layout.addWidget(title)
        
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        
        scroll_content = QWidget()
        scroll_layout = QVBoxLayout(scroll_content)
        
        # Centralizing the settings inside a max-width container to prevent spacing out.
        centered_container = QWidget()
        container_layout = QVBoxLayout(centered_container)
        container_layout.setContentsMargins(0, 0, 0, 0)
        
        container_layout.addWidget(self.create_monitoring_group())
        container_layout.addWidget(self.create_alerts_group())
        container_layout.addWidget(self.create_suggestions_group())
        container_layout.addWidget(self.create_appearance_group())
        container_layout.addWidget(self.create_database_group())
        
        scroll_layout.addWidget(centered_container)
        scroll_layout.addStretch()
        
        scroll.setWidget(scroll_content)
        layout.addWidget(scroll)
        
        button_layout = QHBoxLayout()
        auto_save_label = QLabel("Settings are applied automatically")
        button_layout.addWidget(auto_save_label)
        
        self.reset_btn = QPushButton("Reset to Defaults")
        self.reset_btn.clicked.connect(self.reset_to_defaults)
        button_layout.addWidget(self.reset_btn)
        
        button_layout.addStretch()
        layout.addLayout(button_layout)
        
        self._setup_auto_save()

    def _create_toggle(self, label_text: str, tooltip: str = "") -> tuple:
        lbl = QLabel(label_text)
        if tooltip:
            lbl.setToolTip(tooltip)
        toggle = ToggleSwitch()
        if tooltip:
            toggle.setToolTip(tooltip)
        return lbl, toggle

    def create_monitoring_group(self) -> QGroupBox:
        group = QGroupBox("📊 Monitoring")
        layout = QVBoxLayout(group)
        layout.setSpacing(15)
        
        row1 = QHBoxLayout()
        lbl, self.enable_monitoring_toggle = self._create_toggle("Enable System Monitoring", "Enable real-time monitoring of CPU, RAM, and Disk usage")
        row1.addWidget(lbl)
        row1.addStretch()
        row1.addWidget(self.enable_monitoring_toggle)
        layout.addLayout(row1)
        
        row2 = QHBoxLayout()
        lbl, self.enable_anomaly_toggle = self._create_toggle("Enable Anomaly Detection", "Detect unusual system behavior based on historical patterns")
        row2.addWidget(lbl)
        row2.addStretch()
        row2.addWidget(self.enable_anomaly_toggle)
        layout.addLayout(row2)
        
        row3 = QHBoxLayout()
        self.refresh_interval_spin = QSpinBox()
        self.refresh_interval_spin.setRange(1, 60)
        self.refresh_interval_spin.setSuffix(" seconds")
        self.refresh_interval_spin.setFixedSize(100, 26)
        row3.addWidget(QLabel("Refresh Interval:"))
        row3.addStretch()
        row3.addWidget(self.refresh_interval_spin)
        layout.addLayout(row3)
        
        return group
    
    def create_alerts_group(self) -> QGroupBox:
        group = QGroupBox("🔔 Alerts")
        layout = QVBoxLayout(group)
        layout.setSpacing(15)
        
        row1 = QHBoxLayout()
        lbl, self.enable_popup_alerts_toggle = self._create_toggle("Enable Popup Alerts", "Show desktop popup for critical alerts")
        row1.addWidget(lbl)
        row1.addStretch()
        row1.addWidget(self.enable_popup_alerts_toggle)
        layout.addLayout(row1)
        
        row2 = QHBoxLayout()
        lbl, self.enable_tray_notifications_toggle = self._create_toggle("Enable System Tray Notifications", "Show notifications in system tray for medium priority alerts")
        row2.addWidget(lbl)
        row2.addStretch()
        row2.addWidget(self.enable_tray_notifications_toggle)
        layout.addLayout(row2)
        
        row3 = QHBoxLayout()
        self.alert_cooldown_spin = QSpinBox()
        self.alert_cooldown_spin.setRange(5, 300)
        self.alert_cooldown_spin.setSuffix(" seconds")
        self.alert_cooldown_spin.setFixedSize(100, 26)
        row3.addWidget(QLabel("Alert Cooldown:"))
        row3.addStretch()
        row3.addWidget(self.alert_cooldown_spin)
        layout.addLayout(row3)
        
        return group
    
    def create_suggestions_group(self) -> QGroupBox:
        group = QGroupBox("💡 Suggestions")
        layout = QVBoxLayout(group)
        layout.setSpacing(15)
        
        row1 = QHBoxLayout()
        lbl, self.enable_startup_suggestions_toggle = self._create_toggle("Enable Startup Suggestions", "Analyze startup programs and suggest safe ones to disable")
        row1.addWidget(lbl)
        row1.addStretch()
        row1.addWidget(self.enable_startup_suggestions_toggle)
        layout.addLayout(row1)
        
        row2 = QHBoxLayout()
        lbl, self.enable_cache_cleanup_toggle = self._create_toggle("Enable Cache Cleanup Suggestions", "Analyze temporary files and suggest cleanup")
        row2.addWidget(lbl)
        row2.addStretch()
        row2.addWidget(self.enable_cache_cleanup_toggle)
        layout.addLayout(row2)
        
        return group
    
    def create_appearance_group(self) -> QGroupBox:
        group = QGroupBox("🎨 Appearance")
        layout = QVBoxLayout(group)
        layout.setSpacing(15)
        
        row1 = QHBoxLayout()
        self.theme_combo = QComboBox()
        self.theme_combo.addItems(["Dark", "Light"])
        self.theme_combo.setFixedSize(100, 26)
        row1.addWidget(QLabel("Theme:"))
        row1.addStretch()
        row1.addWidget(self.theme_combo)
        layout.addLayout(row1)
        
        return group
    
    def create_database_group(self) -> QGroupBox:
        group = QGroupBox("💾 Database")
        layout = QVBoxLayout(group)
        
        self.db_stats_label = QLabel("Loading database stats...")
        layout.addWidget(self.db_stats_label)
        
        cleanup_btn = QPushButton("Cleanup Old Data")
        cleanup_btn.setToolTip("Remove data older than 7 days")
        cleanup_btn.clicked.connect(self.cleanup_database)
        cleanup_btn.setFixedWidth(150)
        layout.addWidget(cleanup_btn)
        
        return group
    
    def load_settings(self):
        self.settings = self.db.get_all_settings()
        self._loading_settings = True
        
        self.enable_monitoring_toggle.setChecked(self.settings.get('enable_monitoring', True))
        self.enable_anomaly_toggle.setChecked(self.settings.get('enable_anomaly_detection', True))
        self.enable_popup_alerts_toggle.setChecked(self.settings.get('enable_popup_alerts', True))
        self.enable_tray_notifications_toggle.setChecked(self.settings.get('enable_tray_notifications', True))
        self.enable_startup_suggestions_toggle.setChecked(self.settings.get('enable_startup_suggestions', True))
        self.enable_cache_cleanup_toggle.setChecked(self.settings.get('enable_cache_cleanup_suggestions', True))
        
        self.refresh_interval_spin.setValue(self.settings.get('refresh_interval', 1))
        self.alert_cooldown_spin.setValue(self.settings.get('alert_cooldown_seconds', config.ALERT_COOLDOWN_DEFAULT))
        
        theme = self.settings.get('theme', 'dark')
        self.theme_combo.setCurrentText(theme.capitalize())
        self._loading_settings = False
        
        self.update_database_stats()

    def _setup_auto_save(self):
        self.enable_monitoring_toggle.toggled.connect(lambda v: self._save_single_setting('enable_monitoring', v))
        self.enable_anomaly_toggle.toggled.connect(lambda v: self._save_single_setting('enable_anomaly_detection', v))
        self.enable_popup_alerts_toggle.toggled.connect(lambda v: self._save_single_setting('enable_popup_alerts', v))
        self.enable_tray_notifications_toggle.toggled.connect(lambda v: self._save_single_setting('enable_tray_notifications', v))
        self.enable_startup_suggestions_toggle.toggled.connect(lambda v: self._save_single_setting('enable_startup_suggestions', v))
        self.enable_cache_cleanup_toggle.toggled.connect(lambda v: self._save_single_setting('enable_cache_cleanup_suggestions', v))
        self.refresh_interval_spin.valueChanged.connect(lambda v: self._save_single_setting('refresh_interval', v))
        self.alert_cooldown_spin.valueChanged.connect(lambda v: self._save_single_setting('alert_cooldown_seconds', v))
        self.theme_combo.currentTextChanged.connect(lambda t: self._save_single_setting('theme', t.lower()))

    def _save_single_setting(self, key, value):
        if self._loading_settings: return
        self.db.set_setting(key, value)
        self.settings[key] = value
        self.settings_changed.emit({key: value})

    def reset_to_defaults(self):
        reply = QMessageBox.question(self, "Reset Settings", "Are you sure you want to reset all settings?", QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
        if reply == QMessageBox.Yes:
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
            for key, value in defaults.items():
                self.db.set_setting(key, value)
            self.load_settings()
            self.settings_changed.emit(defaults)
            QMessageBox.information(self, "Settings Reset", "Settings have been reset to defaults.")
    
    def cleanup_database(self):
        reply = QMessageBox.question(self, "Cleanup Database", "This will remove all data older than 7 days.\n\nAre you sure you want to continue?", QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
        if reply == QMessageBox.Yes:
            result = self.db.cleanup_old_data(7)
            QMessageBox.information(self, "Cleanup Complete", f"Cleaned up:\n- {result['metrics_deleted']} metrics\n- {result['alerts_deleted']} alerts\n- {result['process_deleted']} processes")
            self.update_database_stats()
    
    def update_database_stats(self):
        stats = self.db.get_database_stats()
        size_mb = stats.get('database_size_bytes', 0) / (1024 * 1024)
        self.db_stats_label.setText(f"Records: {stats.get('system_metrics_count', 0)} metrics, {stats.get('alerts_count', 0)} alerts, {stats.get('process_history_count', 0)} processes\nDatabase size: {size_mb:.2f} MB")
    
    def get_settings(self) -> dict:
        return self.settings.copy()
    
    def apply_theme(self, theme_name: str):
        pass

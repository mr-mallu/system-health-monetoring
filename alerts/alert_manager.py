"""
Alert Manager Module
Manages alerts, notifications, and logging for detected anomalies.
Enhanced with severity-based handling, cooldown, and settings integration.
"""

import logging
import os
from datetime import datetime
from PySide6.QtWidgets import QMessageBox
from PySide6.QtCore import QTimer
import config
from monitor.process_monitor import ProcessMonitor


class AlertManager:
    """
    Manages system alerts and notifications.
    Handles desktop popups and logging with severity-based filtering.
    """
    
    def __init__(self, parent=None):
        """
        Initialize alert manager.
        
        Args:
            parent: Parent widget for message boxes
        """
        self.parent = parent
        self.alert_history = []
        self.pending_alerts = []

        self._setup_logging()

        # Cooldown — prevent popup spam (default 5 minutes)
        self.alert_cooldown = config.ALERT_COOLDOWN_DEFAULT
        self.last_alert_time = {}
        self.last_alert_content = {}

        # Per-process suppression (30 minutes after dismiss)
        self.suppression_window = 1800
        self.suppressed_processes = {}

        # Feature flags (controlled by settings tab)
        self.enable_popup_alerts = True
        self.enable_tray_notifications = True
        self.enable_ml_detection = True

        # Database handle (set via set_database)
        self.db = None

        # Active popup references — prevents garbage collection
        self._active_popups = []
    
    def _setup_logging(self):
        """Set up logging to file."""
        os.makedirs(config.LOGS_DIR, exist_ok=True)
        
        self.logger = logging.getLogger('SystemObserver')
        self.logger.setLevel(logging.INFO)
        self.logger.handlers = []
        
        file_handler = logging.FileHandler(config.LOG_FILE)
        file_handler.setLevel(logging.INFO)
        formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
        file_handler.setFormatter(formatter)
        self.logger.addHandler(file_handler)
        
        self.logger.info("=" * 50)
        self.logger.info("System Health Monitoring - Alert Manager Started")
        self.logger.info("=" * 50)
    
    def set_database(self, db):
        """Set database reference for persistent storage."""
        self.db = db
    
    def update_settings(self, settings: dict):
        """
        Update alert manager settings.
        
        Args:
            settings: Dictionary of settings
        """
        if 'enable_popup_alerts' in settings:
            self.enable_popup_alerts = settings['enable_popup_alerts']
        
        if 'enable_tray_notifications' in settings:
            self.enable_tray_notifications = settings['enable_tray_notifications']
        
        if 'alert_cooldown_seconds' in settings:
            self.alert_cooldown = settings['alert_cooldown_seconds']
        
        if 'enable_ml_detection' in settings:
            self.enable_ml_detection = settings['enable_ml_detection']
        
        self.logger.info(f"Alert settings updated: popup={self.enable_popup_alerts}, "
                        f"tray={self.enable_tray_notifications}, cooldown={self.alert_cooldown}s")
    
    def should_show_alert(self, alert_type: str, process_info: dict = None) -> bool:
        """
        Check if we should show an alert based on cooldown and process suppression.
        
        Args:
            alert_type: Type of alert
            process_info: Optional dict with 'name' and 'pid' keys
            
        Returns:
            bool: True if alert should be shown
        """
        current_time = datetime.now().timestamp()
        
        # Check global cooldown
        if alert_type in self.last_alert_time:
            time_since_last = current_time - self.last_alert_time[alert_type]
            if time_since_last < self.alert_cooldown:
                return False
        
        # Check process-level suppression
        if process_info:
            proc_name = process_info.get('name', '')
            proc_pid = process_info.get('pid', 0)
            
            if proc_name and proc_pid:
                suppression_key = f"{proc_name}_{proc_pid}"
                
                # Check if this process is suppressed
                if suppression_key in self.suppressed_processes:
                    expiry = self.suppressed_processes[suppression_key]
                    if current_time < expiry:
                        # Still suppressed, don't show alert
                        return False
                    else:
                        # Suppression expired, remove it
                        del self.suppressed_processes[suppression_key]
        
        self.last_alert_time[alert_type] = current_time
        return True
    
    def suppress_process(self, process_info: dict):
        """
        Suppress alerts for a specific process for 30 minutes.
        Called when user clicks Dismiss on a process alert.
        
        Args:
            process_info: Dict with 'name' and 'pid' keys
        """
        proc_name = process_info.get('name', '')
        proc_pid = process_info.get('pid', 0)
        
        if proc_name and proc_pid:
            suppression_key = f"{proc_name}_{proc_pid}"
            expiry_time = datetime.now().timestamp() + self.suppression_window
            self.suppressed_processes[suppression_key] = expiry_time
            
            self.logger.info(f"Suppressed alerts for {proc_name} (PID: {proc_pid}) for 30 minutes")
    
    def get_suppressed_processes(self) -> dict:
        """Get currently suppressed processes."""
        return self.suppressed_processes.copy()
    
    def clear_expired_suppressions(self):
        """Clear expired process suppressions."""
        current_time = datetime.now().timestamp()
        expired = [k for k, v in self.suppressed_processes.items() if current_time >= v]
        for k in expired:
            del self.suppressed_processes[k]
    
    def should_show_popup(self, severity: str) -> bool:
        """
        Determine if popup should be shown based on severity and settings.
        
        Args:
            severity: Alert severity level
            
        Returns:
            bool: True if popup should be shown
        """
        if not self.enable_popup_alerts:
            return False
        
        # Critical always shows popup
        if severity == config.SEVERITY_CRITICAL:
            return True
        
        # High shows popup if enabled
        if severity == config.SEVERITY_HIGH:
            return True
        
        # Medium and Low don't show popup (they appear in Alerts tab)
        return False
    
    def should_show_tray_notification(self, severity: str) -> bool:
        """
        Determine if system tray notification should be shown.
        
        Args:
            severity: Alert severity level
            
        Returns:
            bool: True if tray notification should be shown
        """
        if not self.enable_tray_notifications:
            return False
        
        # Tray notifications for Medium and above
        return severity in [config.SEVERITY_MEDIUM, config.SEVERITY_HIGH, config.SEVERITY_CRITICAL]
    
    def create_alert(self, anomaly: dict) -> dict:
        """
        Create an alert from an anomaly.
        
        Args:
            anomaly: Dictionary containing anomaly details
            
        Returns:
            dict: Alert information
        """
        alert = {
            'id': len(self.alert_history) + 1,
            'timestamp': datetime.now(),
            'type': anomaly.get('type', 'Unknown'),
            'severity': anomaly.get('severity', config.SEVERITY_LOW),
            'description': anomaly.get('description', ''),
            'acknowledged': False,
            'process': anomaly.get('process'),
            'ml_confirmed': anomaly.get('ml_confirmed'),
            'ml_score': anomaly.get('ml_score'),
            'source': anomaly.get('source', 'Rule-based')
        }
        
        return alert
    
    def show_desktop_alert(self, anomaly: dict):
        """
        Show a desktop popup alert for an anomaly.
        Enhanced with severity-based filtering, settings, and process suppression.
        
        Args:
            anomaly: Dictionary containing anomaly details
            
        Returns:
            dict: Created alert or None if suppressed
        """
        # Get process info from anomaly
        process_info = anomaly.get('process')
        
        # Check cooldown with process info for suppression
        alert_type = anomaly.get('type', 'Unknown')
        if not self.should_show_alert(alert_type, process_info):
            return None
        
        # Create alert
        alert = self.create_alert(anomaly)
        severity = alert.get('severity', config.SEVERITY_LOW)
        
        # Always log the alert
        self.log_alert(alert)
        
        # Add to history (appears in Alerts tab)
        self.alert_history.append(alert)
        
        # Save to database if available
        if self.db:
            try:
                self.db.insert_alert(
                    severity=alert['severity'],
                    message=alert['description'],
                    source=alert['type']
                )
            except Exception as e:
                self.logger.error(f"Failed to save alert to database: {e}")
        
        # Show popup only for High/Critical severity
        if self.should_show_popup(severity):
            self._show_desktop_notification(alert)
        
        return alert
    
    def _show_desktop_notification(self, alert: dict):
        """Show desktop notification using non-modal QMessageBox.
        
        Uses .show() instead of .exec() so the main UI thread keeps
        processing background metrics and remains fully responsive.
        """
        severity = alert['severity']
        
        # Determine icon and title based on severity
        if severity == config.SEVERITY_CRITICAL:
            icon = QMessageBox.Critical
            title = "🔴 CRITICAL ALERT"
        elif severity == config.SEVERITY_HIGH:
            icon = QMessageBox.Warning
            title = "🟠 High Priority Alert"
        elif severity == config.SEVERITY_MEDIUM:
            icon = QMessageBox.Warning
            title = "🟡 Medium Priority Alert"
        else:
            icon = QMessageBox.Information
            title = "ℹ️ Low Priority Alert"
        
        # Add ML info to description if available
        description = alert['description']
        if alert.get('ml_confirmed') is not None:
            ml_status = "ML Confirmed" if alert['ml_confirmed'] else "ML Normal"
            description += f"\n({ml_status})"
        
        # Build non-modal message box
        msg_box = QMessageBox(self.parent)
        msg_box.setIcon(icon)
        msg_box.setWindowTitle(title)
        msg_box.setText(f"<b>{alert['type']}</b>")
        msg_box.setInformativeText(description)
        msg_box.setModal(False)  # Non-blocking so UI stays responsive
        
        # Add buttons
        log_button = msg_box.addButton("Log Incident", QMessageBox.ActionRole)
        dismiss_button = msg_box.addButton("Dismiss", QMessageBox.RejectRole)
        
        # If there's a process involved, add terminate option
        terminate_button = None
        if alert.get('process'):
            terminate_button = msg_box.addButton("Simulate Terminate", QMessageBox.ActionRole)
        
        # --- Async click handler ---------------------------------------------------
        def _handle_click(clicked_button):
            """Process user's button choice without blocking."""
            if clicked_button == log_button:
                alert['acknowledged'] = True
                self.logger.info(f"Alert {alert['id']} acknowledged and logged by user")
            elif clicked_button == dismiss_button:
                # Suppress this process for 30 minutes to prevent popup spam
                if alert.get('process'):
                    self.suppress_process(alert['process'])
                self.logger.info(f"Alert {alert['id']} dismissed by user")
            elif terminate_button is not None and clicked_button == terminate_button:
                # Actually simulate termination through ProcessMonitor
                process_info = alert.get('process', {})
                pid = process_info.get('pid')
                if pid:
                    pm = ProcessMonitor()
                    result = pm.terminate_process(pid, simulate=True)
                    self.logger.info(
                        f"Alert {alert['id']} – Simulate Terminate: {result['message']}"
                    )
                    # Suppress future alerts for this process
                    self.suppress_process(process_info)
                else:
                    self.logger.info(f"Alert {alert['id']} – Terminate requested but no PID available")
            # Clean up the message box
            msg_box.deleteLater()
        
        msg_box.buttonClicked.connect(_handle_click)
        
        # Keep a reference so the dialog isn't garbage-collected
        self._active_popups.append(msg_box)
        msg_box.destroyed.connect(
            lambda: self._active_popups.remove(msg_box)
            if msg_box in self._active_popups else None
        )
        
        # Show non-modally — the UI keeps running
        msg_box.show()
        
        return alert
    
    def log_alert(self, alert: dict):
        """Log an alert to file."""
        log_message = f"ALERT [{alert['severity']}] - {alert['type']}: {alert['description']}"
        
        if alert.get('process'):
            process = alert['process']
            log_message += f" | Process: {process.get('name', 'Unknown')} (PID: {process.get('pid', 'N/A')})"
        
        if alert.get('ml_confirmed') is not None:
            log_message += f" | ML: {'Confirmed' if alert['ml_confirmed'] else 'Normal'} (score: {alert.get('ml_score', 0):.1f})"
        
        self.logger.info(log_message)
    
    def log_incident(self, incident_type: str, description: str, severity: str, process_info: dict = None):
        """Log a custom incident to file."""
        log_message = f"INCIDENT [{severity}] - {incident_type}: {description}"
        
        if process_info:
            log_message += f" | Process: {process_info.get('name', 'Unknown')} (PID: {process_info.get('pid', 'N/A')})"
        
        self.logger.info(log_message)
    
    def get_alert_history(self) -> list:
        """Get alert history."""
        return self.alert_history
    
    def get_recent_alerts(self, count: int = 10) -> list:
        """Get recent alerts."""
        return self.alert_history[-count:]
    
    def get_unacknowledged_alerts(self) -> list:
        """Get unacknowledged alerts."""
        return [a for a in self.alert_history if not a['acknowledged']]
    
    def acknowledge_alert(self, alert_id: int) -> bool:
        """Acknowledge an alert."""
        for alert in self.alert_history:
            if alert['id'] == alert_id:
                alert['acknowledged'] = True
                self.logger.info(f"Alert {alert_id} acknowledged")
                return True
        return False
    
    def clear_alert_history(self):
        """Clear alert history."""
        self.alert_history = []
        self.logger.info("Alert history cleared")
    
    def get_alert_summary(self) -> dict:
        """Get summary of alerts."""
        if not self.alert_history:
            return {
                'total': 0,
                'critical': 0,
                'high': 0,
                'medium': 0,
                'low': 0,
                'unacknowledged': 0
            }
        
        return {
            'total': len(self.alert_history),
            'critical': sum(1 for a in self.alert_history if a['severity'] == config.SEVERITY_CRITICAL),
            'high': sum(1 for a in self.alert_history if a['severity'] == config.SEVERITY_HIGH),
            'medium': sum(1 for a in self.alert_history if a['severity'] == config.SEVERITY_MEDIUM),
            'low': sum(1 for a in self.alert_history if a['severity'] == config.SEVERITY_LOW),
            'unacknowledged': len(self.get_unacknowledged_alerts())
        }


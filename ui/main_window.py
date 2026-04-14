"""
Main Window Module
Creates the main GUI window for the System Health Monitoring application.
Enhanced with background threading for better UI performance.
"""

import sys
import os
from datetime import datetime

from PySide6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
    QTabWidget, QTableWidget, QTableWidgetItem, QLabel,
    QPushButton, QHeaderView, QFrame, QGridLayout,
    QGroupBox, QScrollArea, QApplication, QMessageBox
)
from PySide6.QtCore import QTimer, Qt
from PySide6.QtGui import QColor, QFont

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import config
from monitor.cpu_monitor import CPUMonitor
from monitor.memory_monitor import MemoryMonitor
from monitor.disk_monitor import DiskMonitor
from monitor.process_monitor import ProcessMonitor
from analysis.anomaly_detector import AnomalyDetector
from analysis.ml_detector import get_ml_detector
from analysis.performance_analyzer import PerformanceAnalyzer
from analysis.suggestions_engine import SuggestionsEngine
from alerts.alert_manager import AlertManager
from backend.database import get_database
from backend.monitor_worker import get_monitor_worker
from backend.report_generator import ReportGenerator
from backend.daily_summary import DailySummary

# Import new views
from ui.settings_view import SettingsView
from ui.history_view import HistoryView
from ui.suggestions_view import SuggestionsView
from ui.graph_dashboard import GraphDashboard


class MainWindow(QMainWindow):
    """Main application window for System Health Monitoring."""
    
    def __init__(self):
        """Initialize the main window."""
        super().__init__()
        
        # Initialize monitors (for initial display)
        self.cpu_monitor = CPUMonitor(history_size=config.HISTORY_SIZE)
        self.memory_monitor = MemoryMonitor(history_size=config.HISTORY_SIZE)
        self.disk_monitor = DiskMonitor(history_size=config.HISTORY_SIZE)
        self.process_monitor = ProcessMonitor(
            high_cpu_threshold=config.PROCESS_HIGH_CPU_THRESHOLD,
            high_memory_threshold_mb=config.PROCESS_HIGH_MEMORY_THRESHOLD,
            long_running_hours=config.PROCESS_LONG_RUNNING_HOURS
        )
        
        # Initialize anomaly detector with ML integration
        self.anomaly_detector = AnomalyDetector()
        self.ml_detector = get_ml_detector()
        self.anomaly_detector.set_ml_detector(self.ml_detector)

        # Feature modules (non-blocking, used from UI thread)
        self.performance_analyzer = PerformanceAnalyzer()
        self.suggestions_engine = SuggestionsEngine()
        self.report_generator = ReportGenerator()
        self.daily_summary = DailySummary()
        
        # Initialize alert manager
        self.alert_manager = AlertManager(parent=self)
        
        # Initialize database
        self.db = get_database()
        self.alert_manager.set_database(self.db)
        
        # Current data (updated by background worker)
        self.current_metrics = {
            'cpu': {'usage': 0.0, 'average': 0.0},
            'memory': {'usage': 0.0, 'info': {}, 'average': 0.0},
            'disk': {'usage': 0.0, 'info': {}},
            'processes': {'count': 0, 'top_cpu': [], 'top_memory': [], 'summary': {}},
            'health_score': 100.0,
            'health_status': 'Excellent',
            'anomalies': []  # FIX: Initialize anomalies list
        }
        self.anomalies = []
        self.current_impact_analysis = {}
        self.current_suggestions = []
        
        # Cache for process list
        self._cached_processes = []
        
        # Track visible tab for lazy loading
        self._current_tab_index = 0
        self.processes_tab_index = -1
        self.anomalies_tab_index = -1
        self.alerts_tab_index = -1
        self.history_tab_index = -1
        
        # Setup UI
        self.init_ui()
        
        # Apply dark theme
        self.apply_theme()
        
        # Load settings from database
        self._load_settings()
        
        # Setup background monitoring worker
        self._setup_background_monitoring()

        # Refresh daily stats panel periodically
        self.daily_summary_timer = QTimer(self)
        self.daily_summary_timer.timeout.connect(self.update_daily_summary_panel)
        self.daily_summary_timer.start(60000)
        
        # Initial update
        self.update_metrics()
        self.update_daily_summary_panel()
    
    def _load_settings(self):
        """Load settings from database."""
        try:
            settings = self.db.get_all_settings()
            self.on_settings_changed(settings)
        except Exception as e:
            print(f"Error loading settings: {e}")
    
    def _setup_background_monitoring(self):
        """Setup background monitoring with QThread."""
        # Get or create monitor worker
        refresh_interval = config.REFRESH_INTERVAL
        self.monitor_worker = get_monitor_worker(refresh_interval)
        
        # Connect signals
        self.monitor_worker.metrics_updated.connect(self.on_metrics_updated)
        self.monitor_worker.anomaly_detected.connect(self.on_anomaly_detected)
        self.monitor_worker.error_occurred.connect(self.on_monitor_error)
        
        # Start monitoring
        self.monitor_worker.start()
        
        print("Background monitoring started")
    
    def on_metrics_updated(self, metrics):
        """Handle metrics update from background worker."""
        # Update current metrics
        self.current_metrics = metrics
        # FIX: Get anomalies from metrics
        self.anomalies = metrics.get('anomalies', [])

        # Analyze root cause and suggestions from latest process metrics
        top_cpu = metrics.get('processes', {}).get('top_cpu', []) or []
        top_memory = metrics.get('processes', {}).get('top_memory', []) or []
        merged_processes = top_cpu + [
            p for p in top_memory if p.get('pid') not in {x.get('pid') for x in top_cpu}
        ]

        self.current_impact_analysis = self.performance_analyzer.analyze_process_impact(
            top_cpu, top_memory,
            metrics.get('cpu', {}).get('usage', 0),
            metrics.get('memory', {}).get('usage', 0)
        )
        self.current_suggestions = self.suggestions_engine.generate_suggestions(metrics, merged_processes)
        
        # Update UI (always update system display)
        self.update_system_display()
        self.suggestions_view.set_live_suggestions(self.current_suggestions)
        if hasattr(self, 'overview_graph_dashboard'):
            self.overview_graph_dashboard.update_metrics(
                metrics.get('cpu', {}).get('usage', 0),
                metrics.get('memory', {}).get('usage', 0),
                metrics.get('health_score', 100)
            )
        
        # Update current tab only for better performance
        current_tab = self.tabs.currentIndex()
        if current_tab == self.processes_tab_index:
            self.update_process_table()
        elif current_tab == self.anomalies_tab_index:
            self.update_anomaly_table()
        elif current_tab == self.alerts_tab_index:
            self.update_alert_display()
        elif current_tab == self.history_tab_index:
            self.history_view.load_history_data()
    
    def on_anomaly_detected(self, anomaly):
        """Handle anomaly detected from background worker."""
        # Attach performance cause explanation to anomaly context shown in alerts
        explanation = self.current_impact_analysis.get('explanation', '')
        if explanation:
            anomaly = dict(anomaly)
            original = anomaly.get('description', '')
            anomaly['description'] = f"{original}\nCause: {explanation}"

        # Show alert
        self.alert_manager.show_desktop_alert(anomaly)
    
    def on_monitor_error(self, error_msg):
        """Handle monitoring error."""
        print(f"Monitor error: {error_msg}")
    
    def apply_theme(self):
        """Apply dark theme to the application."""
        theme_path = os.path.join(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
            'themes', 'dark.qss'
        )
        
        if os.path.exists(theme_path):
            try:
                with open(theme_path, 'r') as f:
                    theme_content = f.read()
                app = QApplication.instance()
                if app:
                    app.setStyleSheet(theme_content)
            except Exception as e:
                print(f"Failed to load theme: {e}")
    
    def init_ui(self):
        """Initialize the user interface."""
        self.setWindowTitle("System Health Monitoring - Desktop Monitoring Tool")
        self.setGeometry(100, 100, 1200, 800)
        
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        main_layout = QVBoxLayout(central_widget)
        
        # Add header with health score
        self.create_header(main_layout)
        
        # Create tab widget
        self.tabs = QTabWidget()
        main_layout.addWidget(self.tabs)
        
        # Create tabs
        self.create_system_tab()
        self.create_processes_tab()
        self.create_anomalies_tab()
        self.create_alerts_tab()
        self.create_history_tab()
        self.create_suggestions_tab()
        self.create_settings_tab()
        
        # Connect tab change for lazy loading
        self.tabs.currentChanged.connect(self.on_tab_changed)
        
        # Connect settings changes
        self.settings_view.settings_changed.connect(self.on_settings_changed)
    
    def create_header(self, parent_layout):
        """Create header with health score."""
        header_group = QGroupBox()
        header_layout = QHBoxLayout(header_group)
        
        # Title
        title_label = QLabel("🖥️ System Health Monitoring")
        title_font = QFont()
        title_font.setPointSize(16)
        title_font.setBold(True)
        title_label.setFont(title_font)
        header_layout.addWidget(title_label)
        
        header_layout.addStretch()
        
        # Health Score Display
        health_label = QLabel("System Health:")
        header_layout.addWidget(health_label)
        
        self.health_score_label = QLabel("100")
        health_font = QFont()
        health_font.setPointSize(24)
        health_font.setBold(True)
        self.health_score_label.setFont(health_font)
        self.health_score_label.setStyleSheet("color: green;")
        header_layout.addWidget(self.health_score_label)
        
        self.health_status_label = QLabel("Excellent")
        status_font = QFont()
        status_font.setPointSize(14)
        self.health_status_label.setFont(status_font)
        header_layout.addWidget(self.health_status_label)
        
        # ML Status indicator
        self.ml_status_label = QLabel("ML: Training...")
        ml_font = QFont()
        ml_font.setPointSize(10)
        self.ml_status_label.setFont(ml_font)
        self.ml_status_label.setStyleSheet("color: gray;")
        header_layout.addWidget(self.ml_status_label)
        
        parent_layout.addWidget(header_group)
    
    def create_system_tab(self):
        """Create system metrics tab."""
        tab = QWidget()
        tab_layout = QVBoxLayout(tab)
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll_content = QWidget()
        layout = QVBoxLayout(scroll_content)

        # Graph panel at top of overview (in front of dedicated sections)
        overview_graph_group = QGroupBox("Live Graph Dashboard")
        overview_graph_layout = QVBoxLayout(overview_graph_group)
        self.overview_graph_dashboard = GraphDashboard()
        self.overview_graph_dashboard.setMinimumHeight(220)
        self.overview_graph_dashboard.setMaximumHeight(320)
        overview_graph_layout.addWidget(self.overview_graph_dashboard)
        layout.addWidget(overview_graph_group)

        # CPU Section
        cpu_group = QGroupBox("CPU Usage")
        cpu_layout = QGridLayout(cpu_group)
        cpu_layout.addWidget(QLabel("CPU Usage:"), 0, 0)
        self.cpu_value_label = QLabel("0%")
        cpu_font = QFont()
        cpu_font.setPointSize(20)
        cpu_font.setBold(True)
        self.cpu_value_label.setFont(cpu_font)
        cpu_layout.addWidget(self.cpu_value_label, 0, 1)
        self.cpu_indicator = QLabel("*")
        indicator_font = QFont()
        indicator_font.setPointSize(20)
        self.cpu_indicator.setFont(indicator_font)
        self.cpu_indicator.setStyleSheet("color: green;")
        cpu_layout.addWidget(self.cpu_indicator, 0, 2)
        cpu_layout.addWidget(QLabel(f"Cores: {self.cpu_monitor.get_cpu_count()}"), 1, 0, 1, 3)
        layout.addWidget(cpu_group)

        # Memory Section
        memory_group = QGroupBox("Memory Usage (RAM)")
        memory_layout = QGridLayout(memory_group)
        memory_layout.addWidget(QLabel("Memory Usage:"), 0, 0)
        self.memory_value_label = QLabel("0%")
        self.memory_value_label.setFont(cpu_font)
        memory_layout.addWidget(self.memory_value_label, 0, 1)
        self.memory_indicator = QLabel("*")
        self.memory_indicator.setFont(indicator_font)
        self.memory_indicator.setStyleSheet("color: green;")
        memory_layout.addWidget(self.memory_indicator, 0, 2)
        self.memory_details_label = QLabel("Loading...")
        memory_layout.addWidget(self.memory_details_label, 1, 0, 1, 3)
        layout.addWidget(memory_group)

        # Disk Section
        disk_group = QGroupBox("Disk Usage (C:)")
        disk_layout = QGridLayout(disk_group)
        disk_layout.addWidget(QLabel("Disk Usage:"), 0, 0)
        self.disk_value_label = QLabel("0%")
        self.disk_value_label.setFont(cpu_font)
        disk_layout.addWidget(self.disk_value_label, 0, 1)
        self.disk_indicator = QLabel("*")
        self.disk_indicator.setFont(indicator_font)
        self.disk_indicator.setStyleSheet("color: green;")
        disk_layout.addWidget(self.disk_indicator, 0, 2)
        self.disk_details_label = QLabel("Loading...")
        disk_layout.addWidget(self.disk_details_label, 1, 0, 1, 3)
        layout.addWidget(disk_group)

        # Process Summary
        process_summary_group = QGroupBox("Process Summary")
        process_summary_layout = QGridLayout(process_summary_group)
        process_summary_layout.addWidget(QLabel("Total Processes:"), 0, 0)
        self.total_processes_label = QLabel("0")
        process_summary_layout.addWidget(self.total_processes_label, 0, 1)
        process_summary_layout.addWidget(QLabel("High CPU Processes:"), 1, 0)
        self.high_cpu_count_label = QLabel("0")
        process_summary_layout.addWidget(self.high_cpu_count_label, 1, 1)
        process_summary_layout.addWidget(QLabel("High Memory Processes:"), 2, 0)
        self.high_memory_count_label = QLabel("0")
        process_summary_layout.addWidget(self.high_memory_count_label, 2, 1)
        process_summary_layout.addWidget(QLabel("Long-running Processes:"), 3, 0)
        self.long_running_count_label = QLabel("0")
        process_summary_layout.addWidget(self.long_running_count_label, 3, 1)
        layout.addWidget(process_summary_group)

        # Performance cause explanation
        performance_group = QGroupBox("Performance Cause Explanation")
        performance_layout = QVBoxLayout(performance_group)
        self.performance_explanation_label = QLabel("System performance is currently healthy.")
        self.performance_explanation_label.setWordWrap(True)
        performance_layout.addWidget(self.performance_explanation_label)
        self.performance_recommendation_label = QLabel("No immediate action required.")
        self.performance_recommendation_label.setWordWrap(True)
        performance_layout.addWidget(self.performance_recommendation_label)
        self.performance_risk_label = QLabel("Risk Level: Low")
        performance_layout.addWidget(self.performance_risk_label)
        layout.addWidget(performance_group)

        # Daily system summary
        daily_group = QGroupBox("Daily System Summary")
        daily_layout = QGridLayout(daily_group)
        daily_layout.addWidget(QLabel("Peak CPU:"), 0, 0)
        self.daily_peak_cpu_label = QLabel("0.0%")
        daily_layout.addWidget(self.daily_peak_cpu_label, 0, 1)
        daily_layout.addWidget(QLabel("Peak Memory:"), 0, 2)
        self.daily_peak_memory_label = QLabel("0.0%")
        daily_layout.addWidget(self.daily_peak_memory_label, 0, 3)
        daily_layout.addWidget(QLabel("Alerts Today:"), 1, 0)
        self.daily_alert_count_label = QLabel("0")
        daily_layout.addWidget(self.daily_alert_count_label, 1, 1)
        daily_layout.addWidget(QLabel("Avg Health:"), 1, 2)
        self.daily_avg_health_label = QLabel("100.0")
        daily_layout.addWidget(self.daily_avg_health_label, 1, 3)
        self.refresh_daily_btn = QPushButton("Refresh Daily Summary")
        self.refresh_daily_btn.clicked.connect(self.update_daily_summary_panel)
        daily_layout.addWidget(self.refresh_daily_btn, 2, 0, 1, 2)
        layout.addWidget(daily_group)

        # Report action
        actions_layout = QHBoxLayout()
        self.generate_report_btn = QPushButton("Generate System Report")
        self.generate_report_btn.clicked.connect(self.generate_system_report)
        actions_layout.addWidget(self.generate_report_btn)
        self.report_status_label = QLabel("Report status: Not generated yet")
        actions_layout.addWidget(self.report_status_label)
        actions_layout.addStretch()
        layout.addLayout(actions_layout)

        layout.addStretch()
        scroll.setWidget(scroll_content)
        tab_layout.addWidget(scroll)
        self.tabs.addTab(tab, "System Overview")
    def create_processes_tab(self):
        """Create processes tab with table."""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        button_layout = QHBoxLayout()
        refresh_btn = QPushButton("Refresh Process List")
        refresh_btn.clicked.connect(self.update_process_table)
        button_layout.addWidget(refresh_btn)
        button_layout.addStretch()
        
        self.terminate_btn = QPushButton("Simulate Terminate Selected")
        self.terminate_btn.clicked.connect(self.terminate_selected_process)
        self.terminate_btn.setEnabled(False)
        button_layout.addWidget(self.terminate_btn)
        
        layout.addLayout(button_layout)
        
        self.process_table = QTableWidget()
        self.process_table.setColumnCount(6)
        self.process_table.setHorizontalHeaderLabels([
            "PID", "Process Name", "CPU %", "Memory (MB)", "Memory %", "Uptime (hrs)"
        ])
        self.process_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
        self.process_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.process_table.setSelectionMode(QTableWidget.SingleSelection)
        self.process_table.itemSelectionChanged.connect(self.process_selection_changed)
        
        layout.addWidget(self.process_table)
        
        self.processes_tab_index = self.tabs.addTab(tab, "Processes")
    
    def create_anomalies_tab(self):
        """Create anomalies tab."""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        # FIX: Add refresh button for anomalies
        button_layout = QHBoxLayout()
        refresh_btn = QPushButton("Refresh Anomalies")
        refresh_btn.clicked.connect(self.update_anomaly_table)
        button_layout.addWidget(refresh_btn)
        button_layout.addStretch()
        
        layout.addLayout(button_layout)
        
        self.anomaly_count_label = QLabel("Active Anomalies: 0")
        anomaly_font = QFont()
        anomaly_font.setPointSize(12)
        anomaly_font.setBold(True)
        self.anomaly_count_label.setFont(anomaly_font)
        layout.addWidget(self.anomaly_count_label)
        
        self.anomaly_table = QTableWidget()
        self.anomaly_table.setColumnCount(4)
        self.anomaly_table.setHorizontalHeaderLabels([
            "Time", "Type", "Severity", "Description"
        ])
        self.anomaly_table.horizontalHeader().setSectionResizeMode(3, QHeaderView.Stretch)
        
        layout.addWidget(self.anomaly_table)
        
        self.anomalies_tab_index = self.tabs.addTab(tab, "Anomalies")
    
    def create_alerts_tab(self):
        """Create alerts tab."""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        button_layout = QHBoxLayout()
        
        self.alert_summary_label = QLabel("Total Alerts: 0")
        button_layout.addWidget(self.alert_summary_label)
        
        button_layout.addStretch()
        
        clear_btn = QPushButton("Clear Alert History")
        clear_btn.clicked.connect(self.clear_alerts)
        button_layout.addWidget(clear_btn)
        
        layout.addLayout(button_layout)
        
        self.alert_table = QTableWidget()
        self.alert_table.setColumnCount(5)
        self.alert_table.setHorizontalHeaderLabels([
            "Time", "Type", "Severity", "Description", "Acknowledged"
        ])
        self.alert_table.horizontalHeader().setSectionResizeMode(3, QHeaderView.Stretch)
        
        layout.addWidget(self.alert_table)
        
        self.alerts_tab_index = self.tabs.addTab(tab, "Alerts")
    
    def create_history_tab(self):
        """Create history tab."""
        self.history_view = HistoryView()
        self.history_tab_index = self.tabs.addTab(self.history_view, "History")
    
    def create_suggestions_tab(self):
        """Create suggestions tab."""
        self.suggestions_view = SuggestionsView()
        self.tabs.addTab(self.suggestions_view, "Suggestions")
    
    def create_settings_tab(self):
        """Create settings tab."""
        self.settings_view = SettingsView()
        self.tabs.addTab(self.settings_view, "Settings")

    def update_metrics(self):
        """Update all system metrics (called initially and as fallback)."""
        # Get current readings from monitors
        self.current_metrics['cpu']['usage'] = self.cpu_monitor.record_reading()
        self.current_metrics['memory']['usage'] = self.memory_monitor.record_reading()
        self.current_metrics['disk']['usage'] = self.disk_monitor.record_reading()
        
        # Get process list
        process_list = self.process_monitor.get_all_processes()
        self._cached_processes = process_list
        self.current_metrics['processes']['count'] = len(process_list)
        self.current_metrics['processes']['summary'] = self.process_monitor.get_system_process_summary()
        
        # Update display
        self.update_system_display()

        # Keep overview graph populated on initial/fallback refresh path.
        if hasattr(self, 'overview_graph_dashboard'):
            self.overview_graph_dashboard.update_metrics(
                self.current_metrics['cpu'].get('usage', 0),
                self.current_metrics['memory'].get('usage', 0),
                self.current_metrics.get('health_score', 100)
            )
    
    def on_tab_changed(self, index):
        """Handle tab change with deferred loading."""
        self._current_tab_index = index
        
        if index == self.processes_tab_index:
            self.update_process_table()
        elif index == self.anomalies_tab_index:
            self.update_anomaly_table()
        elif index == self.alerts_tab_index:
            self.update_alert_display()
        elif index == self.history_tab_index:
            self.history_view.load_history_data()
    
    def update_system_display(self):
        """Update system metrics display."""
        # Update CPU
        cpu_usage = self.current_metrics['cpu']['usage']
        self.cpu_value_label.setText(f"{cpu_usage:.1f}%")
        self.update_indicator(self.cpu_indicator, cpu_usage, 
                            config.CPU_WARNING_THRESHOLD, config.CPU_CRITICAL_THRESHOLD)
        
        # Update Memory
        memory_usage = self.current_metrics['memory']['usage']
        self.memory_value_label.setText(f"{memory_usage:.1f}%")
        self.update_indicator(self.memory_indicator, memory_usage,
                            config.MEMORY_WARNING_THRESHOLD, config.MEMORY_CRITICAL_THRESHOLD)
        
        # Memory details
        mem_info = self.current_metrics['memory'].get('info', {})
        if mem_info:
            self.memory_details_label.setText(
                f"Used: {mem_info.get('used', 0):.0f} MB | "
                f"Available: {mem_info.get('available', 0):.0f} MB | "
                f"Total: {mem_info.get('total', 0):.0f} MB"
            )
        
        # Update Disk
        disk_usage = self.current_metrics['disk']['usage']
        self.disk_value_label.setText(f"{disk_usage:.1f}%")
        self.update_indicator(self.disk_indicator, disk_usage,
                            config.DISK_WARNING_THRESHOLD, config.DISK_CRITICAL_THRESHOLD)
        
        # Disk details
        disk_info = self.current_metrics['disk'].get('info', {})
        if disk_info:
            self.disk_details_label.setText(
                f"Used: {disk_info.get('used', 0):.1f} GB | "
                f"Free: {disk_info.get('free', 0):.1f} GB | "
                f"Total: {disk_info.get('total', 0):.1f} GB"
            )
        
        # Process summary
        summary = self.current_metrics['processes'].get('summary', {})
        if summary:
            self.total_processes_label.setText(str(summary.get('total_count', 0)))
            self.high_cpu_count_label.setText(str(summary.get('high_cpu_count', 0)))
            self.high_memory_count_label.setText(str(summary.get('high_memory_count', 0)))
            self.long_running_count_label.setText(str(summary.get('long_running_count', 0)))

        # Performance explanation
        if self.current_impact_analysis:
            explanation = self.current_impact_analysis.get('explanation', 'System performance is currently healthy.')
            recommendation = self.current_impact_analysis.get('recommendation', 'No immediate action required.')
            risk = self.current_impact_analysis.get('risk_level', 'Low')
            self.performance_explanation_label.setText(explanation)
            self.performance_recommendation_label.setText(f"Recommendation: {recommendation}")
            self.performance_risk_label.setText(f"Risk Level: {risk}")
        
        # Update health score
        health_score = self.current_metrics.get('health_score', 100)
        self.health_score_label.setText(f"{health_score:.0f}")
        status = self.current_metrics.get('health_status', 'Excellent')
        self.health_status_label.setText(status)
        
        # Color based on score
        if health_score >= 80:
            color = "green"
        elif health_score >= 60:
            color = "lightgreen"
        elif health_score >= 40:
            color = "yellow"
        elif health_score >= 20:
            color = "orange"
        else:
            color = "red"
        
        self.health_score_label.setStyleSheet(f"color: {color};")
        
        # Update ML status
        ml_ready = self.current_metrics.get('ml_ready', False)
        if ml_ready:
            self.ml_status_label.setText("ML: Active")
            self.ml_status_label.setStyleSheet("color: green;")
        else:
            self.ml_status_label.setText("ML: Training...")
            self.ml_status_label.setStyleSheet("color: orange;")

    def update_daily_summary_panel(self):
        """Refresh daily summary labels from SQLite statistics."""
        try:
            stats = self.daily_summary.calculate_daily_stats()
            self.daily_peak_cpu_label.setText(f"{stats.get('peak_cpu', 0):.1f}%")
            self.daily_peak_memory_label.setText(f"{stats.get('peak_memory', 0):.1f}%")
            self.daily_alert_count_label.setText(str(stats.get('alert_count', 0)))
            self.daily_avg_health_label.setText(f"{stats.get('avg_health_score', 0):.1f}")
        except Exception as e:
            self.daily_peak_cpu_label.setText("N/A")
            self.daily_peak_memory_label.setText("N/A")
            self.daily_alert_count_label.setText("N/A")
            self.daily_avg_health_label.setText("N/A")
            print(f"Daily summary refresh failed: {e}")

    def generate_system_report(self):
        """Generate TXT/CSV system report from current state."""
        try:
            daily_stats = self.daily_summary.calculate_daily_stats()
            report_info = self.report_generator.generate_report(
                metrics=self.current_metrics,
                anomalies=self.anomalies,
                suggestions=self.current_suggestions,
                daily_summary=daily_stats,
                include_processes=True
            )

            filename = os.path.basename(report_info['txt_path'])
            self.report_status_label.setText(f"Report generated: {filename}")
            QMessageBox.information(
                self,
                "System Report Generated",
                f"TXT: {report_info['txt_path']}\nCSV: {report_info['csv_path']}"
            )
        except Exception as e:
            self.report_status_label.setText("Report generation failed")
            QMessageBox.warning(self, "Report Error", f"Failed to generate report: {e}")
    
    def update_indicator(self, indicator, value, warning_threshold, critical_threshold):
        """Update indicator color based on value."""
        if value >= critical_threshold:
            indicator.setStyleSheet("color: red;")
        elif value >= warning_threshold:
            indicator.setStyleSheet("color: orange;")
        else:
            indicator.setStyleSheet("color: green;")
    
    def update_process_table(self):
        """Update process table."""
        processes = self.current_metrics['processes'].get('top_cpu', [])
        
        if not processes:
            processes = self._cached_processes
        
        if not processes:
            return
        
        # Sort by CPU usage
        processes.sort(key=lambda x: x.get('cpu_percent', 0), reverse=True)
        processes = processes[:100]
        
        self.process_table.setRowCount(len(processes))
        
        for row, proc in enumerate(processes):
            self.process_table.setItem(row, 0, QTableWidgetItem(str(proc.get('pid', 0))))
            self.process_table.setItem(row, 1, QTableWidgetItem(proc.get('name', 'Unknown')))
            
            cpu_item = QTableWidgetItem(f"{proc.get('cpu_percent', 0):.1f}")
            if proc.get('cpu_percent', 0) >= config.PROCESS_HIGH_CPU_THRESHOLD:
                cpu_item.setBackground(QColor(255, 200, 200))
            self.process_table.setItem(row, 2, cpu_item)
            
            memory_item = QTableWidgetItem(f"{proc.get('memory_mb', 0):.1f}")
            if proc.get('memory_mb', 0) >= config.PROCESS_HIGH_MEMORY_THRESHOLD:
                memory_item.setBackground(QColor(255, 200, 200))
            self.process_table.setItem(row, 3, memory_item)
            
            self.process_table.setItem(row, 4, QTableWidgetItem(f"{proc.get('memory_percent', 0):.1f}"))
            self.process_table.setItem(row, 5, QTableWidgetItem(f"{proc.get('uptime_hours', 0):.1f}"))
    
    def process_selection_changed(self):
        """Handle process selection change."""
        selected = self.process_table.selectedItems()
        self.terminate_btn.setEnabled(len(selected) > 0)
    
    def terminate_selected_process(self):
        """Terminate the selected process (simulated)."""
        selected_rows = self.process_table.selectionModel().selectedRows()
        if selected_rows:
            row = selected_rows[0].row()
            pid_item = self.process_table.item(row, 0)
            pid = int(pid_item.text())
            
            result = self.process_monitor.terminate_process(pid, simulate=True)
            
            self.alert_manager.log_incident(
                "Process Termination",
                result['message'],
                config.SEVERITY_MEDIUM,
                {'pid': pid}
            )
    
    def update_anomaly_table(self):
        """Update anomaly table with current anomalies."""
        # FIX: Use self.anomalies directly which is updated by on_metrics_updated
        anomalies = self.anomalies if self.anomalies else self.current_metrics.get('anomalies', [])
        
        self.anomaly_count_label.setText(f"Active Anomalies: {len(anomalies)}")
        
        self.anomaly_table.setRowCount(len(anomalies))
        
        for row, anomaly in enumerate(anomalies):
            timestamp = datetime.now().strftime("%H:%M:%S")
            self.anomaly_table.setItem(row, 0, QTableWidgetItem(timestamp))
            self.anomaly_table.setItem(row, 1, QTableWidgetItem(anomaly.get('type', 'Unknown')))
            
            severity_item = QTableWidgetItem(anomaly.get('severity', 'Low'))
            severity = anomaly.get('severity', 'Low')
            if severity == config.SEVERITY_CRITICAL:
                severity_item.setBackground(QColor(255, 0, 0))
                severity_item.setForeground(QColor(255, 255, 255))
            elif severity == config.SEVERITY_HIGH:
                severity_item.setBackground(QColor(255, 165, 0))
            elif severity == config.SEVERITY_MEDIUM:
                severity_item.setBackground(QColor(255, 255, 0))
            self.anomaly_table.setItem(row, 2, severity_item)
            
            self.anomaly_table.setItem(row, 3, QTableWidgetItem(anomaly.get('description', '')))
    
    def update_alert_display(self):
        """Update alert display."""
        summary = self.alert_manager.get_alert_summary()
        
        self.alert_summary_label.setText(
            f"Total Alerts: {summary['total']} | "
            f"Critical: {summary['critical']} | "
            f"High: {summary['high']} | "
            f"Medium: {summary['medium']} | "
            f"Low: {summary['low']}"
        )
        
        alerts = self.alert_manager.get_alert_history()
        alerts = alerts[-50:]
        
        self.alert_table.setRowCount(len(alerts))
        
        for row, alert in enumerate(alerts):
            time_str = alert['timestamp'].strftime("%Y-%m-%d %H:%M:%S")
            self.alert_table.setItem(row, 0, QTableWidgetItem(time_str))
            self.alert_table.setItem(row, 1, QTableWidgetItem(alert.get('type', 'Unknown')))
            
            severity_item = QTableWidgetItem(alert.get('severity', 'Low'))
            severity = alert.get('severity', 'Low')
            if severity == config.SEVERITY_CRITICAL:
                severity_item.setBackground(QColor(255, 0, 0))
                severity_item.setForeground(QColor(255, 255, 255))
            elif severity == config.SEVERITY_HIGH:
                severity_item.setBackground(QColor(255, 165, 0))
            self.alert_table.setItem(row, 2, severity_item)
            
            self.alert_table.setItem(row, 3, QTableWidgetItem(alert.get('description', '')))
            
            ack_text = "Yes" if alert.get('acknowledged', False) else "No"
            ack_item = QTableWidgetItem(ack_text)
            if not alert.get('acknowledged', False):
                ack_item.setBackground(QColor(255, 255, 0))
            self.alert_table.setItem(row, 4, ack_item)
    
    def clear_alerts(self):
        """Clear alert history."""
        self.alert_manager.clear_alert_history()
        self.update_alert_display()
    
    def closeEvent(self, event):
        """Handle window close event."""
        # Stop monitoring
        if hasattr(self, 'monitor_worker') and self.monitor_worker:
            self.monitor_worker.stop()
        
        # Log shutdown
        if hasattr(self, 'alert_manager'):
            self.alert_manager.logger.info("System Health Monitoring - Application Closed")
        
        event.accept()
    
    def on_settings_changed(self, settings):
        """Handle settings changes from settings view."""
        # Update alert manager
        self.alert_manager.update_settings(settings)
        
        # Update monitor worker if exists
        if hasattr(self, 'monitor_worker') and self.monitor_worker:
            self.monitor_worker.update_settings(settings)
        
        # FIX: Apply theme immediately without restart
        if 'theme' in settings:
            self._apply_theme(settings['theme'].lower())
    
    def _apply_theme(self, theme_name):
        """Apply theme to the application."""
        theme_path = os.path.join(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
            'themes', f'{theme_name}.qss'
        )
        
        if os.path.exists(theme_path):
            try:
                with open(theme_path, 'r') as f:
                    theme_content = f.read()
                app = QApplication.instance()
                if app:
                    app.setStyleSheet(theme_content)
            except Exception as e:
                print(f"Failed to load theme: {e}")




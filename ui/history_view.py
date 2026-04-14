"""
History View Module
Provides interface for viewing historical system data.
"""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGroupBox,
    QLabel, QPushButton, QTableWidget, QTableWidgetItem,
    QHeaderView, QComboBox, QDateTimeEdit, QLineEdit,
    QGridLayout, QFrame
)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QFont
from datetime import datetime, timedelta
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.database import get_database


class HistoryView(QWidget):
    """
    Historical data view for system metrics.
    Displays past monitoring data and trends.
    """
    
    # Signal to request data refresh from main window
    refresh_requested = Signal()
    
    def __init__(self, parent=None):
        """Initialize history view."""
        super().__init__(parent)
        
        # Database
        self.db = get_database()
        
        # Current filter
        self.current_time_range = "1h"
        
        # Lazy load flag - only load when tab is clicked
        self._data_loaded = False
        
        # Initialize UI
        self.init_ui()
    
    def init_ui(self):
        """Initialize the user interface."""
        layout = QVBoxLayout(self)
        
        # Title
        title = QLabel("📈 History")
        title_font = QFont()
        title_font.setPointSize(16)
        title_font.setBold(True)
        title.setFont(title_font)
        layout.addWidget(title)
        
        # Filter controls
        filter_group = QGroupBox("Filter")
        filter_layout = QHBoxLayout(filter_group)
        
        filter_layout.addWidget(QLabel("Time Range:"))
        
        self.time_range_combo = QComboBox()
        # FIX: Use addItem(text, userData) properly - value stored in userData
        self.time_range_combo.addItem("Last 1 Hour", "1h")
        self.time_range_combo.addItem("Last 6 Hours", "6h")
        self.time_range_combo.addItem("Last 24 Hours", "24h")
        self.time_range_combo.addItem("Last 7 Days", "7d")
        self.time_range_combo.addItem("Last 30 Days", "30d")
        self.time_range_combo.setCurrentIndex(0)
        # FIX: Connect to currentIndexChanged for proper index-based handling
        self.time_range_combo.currentIndexChanged.connect(self.on_time_range_index_changed)
        filter_layout.addWidget(self.time_range_combo)
        
        filter_layout.addStretch()
        
        # Refresh button
        refresh_btn = QPushButton("Refresh")
        refresh_btn.clicked.connect(self.load_history_data)
        filter_layout.addWidget(refresh_btn)
        
        layout.addWidget(filter_group)
        
        # Statistics summary
        stats_group = QGroupBox("Statistics Summary")
        stats_layout = QGridLayout(stats_group)
        
        # CPU Stats
        stats_layout.addWidget(QLabel("CPU Average:"), 0, 0)
        self.cpu_avg_label = QLabel("--")
        stats_layout.addWidget(self.cpu_avg_label, 0, 1)
        
        stats_layout.addWidget(QLabel("CPU Peak:"), 0, 2)
        self.cpu_peak_label = QLabel("--")
        stats_layout.addWidget(self.cpu_peak_label, 0, 3)
        
        # Memory Stats
        stats_layout.addWidget(QLabel("Memory Average:"), 1, 0)
        self.memory_avg_label = QLabel("--")
        stats_layout.addWidget(self.memory_avg_label, 1, 1)
        
        stats_layout.addWidget(QLabel("Memory Peak:"), 1, 2)
        self.memory_peak_label = QLabel("--")
        stats_layout.addWidget(self.memory_peak_label, 1, 3)
        
        # Disk Stats
        stats_layout.addWidget(QLabel("Disk Average:"), 2, 0)
        self.disk_avg_label = QLabel("--")
        stats_layout.addWidget(self.disk_avg_label, 2, 1)
        
        stats_layout.addWidget(QLabel("Disk Peak:"), 2, 2)
        self.disk_peak_label = QLabel("--")
        stats_layout.addWidget(self.disk_peak_label, 2, 3)
        
        # Process Count
        stats_layout.addWidget(QLabel("Avg Processes:"), 3, 0)
        self.process_avg_label = QLabel("--")
        stats_layout.addWidget(self.process_avg_label, 3, 1)
        
        stats_layout.addWidget(QLabel("Record Count:"), 3, 2)
        self.record_count_label = QLabel("--")
        stats_layout.addWidget(self.record_count_label, 3, 3)
        
        layout.addWidget(stats_group)
        
        # Data table
        self.table = QTableWidget()
        self.table.setColumnCount(6)
        self.table.setHorizontalHeaderLabels([
            "Timestamp", "CPU %", "Memory %", "Disk %", "Processes", "Health Score"
        ])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table.setAlternatingRowColors(True)
        self.table.setSortingEnabled(True)
        
        layout.addWidget(self.table)
        
        # Footer info
        self.footer_label = QLabel("Click Refresh to load data")
        layout.addWidget(self.footer_label)
    
    def on_time_range_index_changed(self, index):
        """Handle time range selection change by index."""
        # FIX: Get value from combo box userData (set in addItem)
        item_value = self.time_range_combo.itemData(index)
        
        if item_value:
            self.current_time_range = item_value
        else:
            # Fallback mapping if userData is not set
            value_map = {0: "1h", 1: "6h", 2: "24h", 3: "7d", 4: "30d"}
            self.current_time_range = value_map.get(index, "1h")
        
        self.load_history_data()
    
    def get_start_time(self) -> str:
        """Get start time based on current time range."""
        now = datetime.now()
        
        if self.current_time_range == "1h":
            delta = timedelta(hours=1)
        elif self.current_time_range == "6h":
            delta = timedelta(hours=6)
        elif self.current_time_range == "24h":
            delta = timedelta(hours=24)
        elif self.current_time_range == "7d":
            delta = timedelta(days=7)
        elif self.current_time_range == "30d":
            delta = timedelta(days=30)
        else:
            delta = timedelta(hours=1)
        
        start_time = now - delta
        return start_time.isoformat()
    
    def load_history_data(self):
        """Load history data from database."""
        try:
            start_time = self.get_start_time()
            
            # Get metrics history - FIX: pass start_time correctly
            data = self.db.get_metrics_history(limit=1000, start_time=start_time)
            
            # Update table
            self.table.setRowCount(len(data))
            
            for row, record in enumerate(data):
                # Timestamp
                timestamp = record.get('timestamp', '')
                self.table.setItem(row, 0, QTableWidgetItem(timestamp))
                
                # CPU
                cpu = record.get('cpu_usage', 0)
                self.table.setItem(row, 1, QTableWidgetItem(f"{cpu:.1f}"))
                
                # Memory
                memory = record.get('memory_usage', 0)
                self.table.setItem(row, 2, QTableWidgetItem(f"{memory:.1f}"))
                
                # Disk
                disk = record.get('disk_usage', 0)
                self.table.setItem(row, 3, QTableWidgetItem(f"{disk:.1f}"))
                
                # Processes
                processes = record.get('process_count', 0)
                self.table.setItem(row, 4, QTableWidgetItem(str(processes)))
                
                # Health Score (calculated)
                health = 100 - (cpu * 0.35 + memory * 0.35)
                self.table.setItem(row, 5, QTableWidgetItem(f"{max(0, min(100, health)):.0f}"))
            
            # Update statistics
            self.update_statistics(data)
            
            # Update footer - FIX: Format timestamp for display
            display_time = datetime.fromisoformat(start_time).strftime("%Y-%m-%d %H:%M")
            self.footer_label.setText(f"Showing {len(data)} records since {display_time}")
            
            # Mark as loaded
            self._data_loaded = True
            
        except Exception as e:
            print(f"Error loading history data: {e}")
            self.footer_label.setText(f"Error loading data: {str(e)}")
    
    def update_statistics(self, data):
        """Update statistics display."""
        if not data:
            self.cpu_avg_label.setText("--")
            self.cpu_peak_label.setText("--")
            self.memory_avg_label.setText("--")
            self.memory_peak_label.setText("--")
            self.disk_avg_label.setText("--")
            self.disk_peak_label.setText("--")
            self.process_avg_label.setText("--")
            self.record_count_label.setText("0")
            return
        
        cpu_values = [r.get('cpu_usage', 0) for r in data]
        memory_values = [r.get('memory_usage', 0) for r in data]
        disk_values = [r.get('disk_usage', 0) for r in data]
        process_values = [r.get('process_count', 0) for r in data]
        
        # CPU
        cpu_avg = sum(cpu_values) / len(cpu_values) if cpu_values else 0
        cpu_peak = max(cpu_values) if cpu_values else 0
        self.cpu_avg_label.setText(f"{cpu_avg:.1f}%")
        self.cpu_peak_label.setText(f"{cpu_peak:.1f}%")
        
        # Memory
        memory_avg = sum(memory_values) / len(memory_values) if memory_values else 0
        memory_peak = max(memory_values) if memory_values else 0
        self.memory_avg_label.setText(f"{memory_avg:.1f}%")
        self.memory_peak_label.setText(f"{memory_peak:.1f}%")
        
        # Disk
        disk_avg = sum(disk_values) / len(disk_values) if disk_values else 0
        disk_peak = max(disk_values) if disk_values else 0
        self.disk_avg_label.setText(f"{disk_avg:.1f}%")
        self.disk_peak_label.setText(f"{disk_peak:.1f}%")
        
        # Process
        process_avg = sum(process_values) / len(process_values) if process_values else 0
        self.process_avg_label.setText(f"{process_avg:.0f}")
        
        # Record count
        self.record_count_label.setText(str(len(data)))
    
    def refresh(self):
        """Refresh the history data."""
        self.load_history_data()

"""
Suggestions View Module
Provides startup program and cache cleanup recommendations.
"""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGroupBox,
    QLabel, QPushButton, QTableWidget, QTableWidgetItem,
    QHeaderView, QComboBox, QMessageBox, QProgressBar,
    QGridLayout, QScrollArea, QFrame
)
from PySide6.QtCore import Qt, Signal, QThread
from PySide6.QtGui import QFont, QColor
from datetime import datetime
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.startup_checker import StartupChecker
from backend.cache_cleaner import CacheCleaner


class ScanThread(QThread):
    """Thread for running scans in background."""
    
    finished = Signal(dict)
    progress = Signal(str)
    
    def __init__(self, scan_type):
        super().__init__()
        self.scan_type = scan_type
    
    def run(self):
        """Run the scan."""
        if self.scan_type == 'startup':
            self.progress.emit("Scanning startup programs...")
            checker = StartupChecker()
            programs = checker.get_startup_programs()
            summary = checker.get_impact_summary()
            self.finished.emit({
                'type': 'startup',
                'programs': programs,
                'summary': summary
            })
        elif self.scan_type == 'cache':
            self.progress.emit("Scanning cache and temporary files...")
            cleaner = CacheCleaner()
            results = cleaner.scan_all()
            total = cleaner.get_safe_to_clean_total()
            category = cleaner.get_category_summary()
            self.finished.emit({
                'type': 'cache',
                'results': results,
                'total': total,
                'category': category
            })


class SuggestionsView(QWidget):
    """
    Suggestions view for startup programs and cache cleanup.
    Provides recommendations to improve system performance.
    """
    
    def __init__(self, parent=None):
        """Initialize suggestions view."""
        super().__init__(parent)
        
        # Initialize components
        self.startup_checker = StartupChecker()
        self.cache_cleaner = CacheCleaner()
        
        # Scan results
        self.startup_programs = []
        self.cache_results = []
        
        # Current tab
        self.current_tab = 'startup'
        
        # Initialize UI
        self.init_ui()
    
    def init_ui(self):
        """Initialize the user interface."""
        layout = QVBoxLayout(self)
        
        # Title
        title = QLabel("💡 Suggestions")
        title_font = QFont()
        title_font.setPointSize(16)
        title_font.setBold(True)
        title.setFont(title_font)
        layout.addWidget(title)

        # Live smart suggestions from metrics pipeline
        live_group = QGroupBox("Live Smart Suggestions")
        live_layout = QVBoxLayout(live_group)
        self.live_summary_label = QLabel("No live suggestions yet.")
        live_layout.addWidget(self.live_summary_label)

        self.live_suggestions_table = QTableWidget()
        self.live_suggestions_table.setColumnCount(3)
        self.live_suggestions_table.setHorizontalHeaderLabels([
            "Severity", "Title", "Message"
        ])
        self.live_suggestions_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeToContents)
        self.live_suggestions_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeToContents)
        self.live_suggestions_table.horizontalHeader().setSectionResizeMode(2, QHeaderView.Stretch)
        self.live_suggestions_table.setAlternatingRowColors(True)
        self.live_suggestions_table.setMaximumHeight(220)
        live_layout.addWidget(self.live_suggestions_table)

        layout.addWidget(live_group)
        
        # Tab buttons
        tab_layout = QHBoxLayout()
        
        self.startup_btn = QPushButton("🚀 Startup Programs")
        self.startup_btn.setCheckable(True)
        self.startup_btn.setChecked(True)
        self.startup_btn.clicked.connect(lambda: self.switch_tab('startup'))
        tab_layout.addWidget(self.startup_btn)
        
        self.cache_btn = QPushButton("🧹 Cache Cleanup")
        self.cache_btn.setCheckable(True)
        self.cache_btn.clicked.connect(lambda: self.switch_tab('cache'))
        tab_layout.addWidget(self.cache_btn)
        
        tab_layout.addStretch()
        
        layout.addLayout(tab_layout)
        
        # Content area
        self.content_stack = QWidget()
        self.content_layout = QVBoxLayout(self.content_stack)
        
        # Startup programs content
        self.startup_content = self.create_startup_content()
        self.content_layout.addWidget(self.startup_content)
        
        # Cache cleanup content (initially hidden)
        self.cache_content = self.create_cache_content()
        self.cache_content.hide()
        self.content_layout.addWidget(self.cache_content)
        
        layout.addWidget(self.content_stack)
    
    def create_startup_content(self) -> QWidget:
        """Create startup programs content."""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # Summary
        self.startup_summary = QLabel("Click 'Scan' to analyze startup programs")
        layout.addWidget(self.startup_summary)
        
        # Scan button
        scan_layout = QHBoxLayout()
        
        self.scan_startup_btn = QPushButton("Scan Startup Programs")
        self.scan_startup_btn.clicked.connect(self.scan_startup_programs)
        scan_layout.addWidget(self.scan_startup_btn)
        
        scan_layout.addStretch()
        
        layout.addLayout(scan_layout)
        
        # Progress
        self.startup_progress = QLabel()
        layout.addWidget(self.startup_progress)
        
        # Tips
        tips_group = QGroupBox("💡 Tips")
        tips_layout = QVBoxLayout(tips_group)
        
        tips = [
            "Startup programs slow down your computer's boot time.",
            "High impact programs use more resources at startup.",
            "System required programs should not be disabled.",
            "You can manage startup programs in Task Manager."
        ]
        
        for tip in tips:
            tip_label = QLabel(f"• {tip}")
            tips_layout.addWidget(tip_label)
        
        layout.addWidget(tips_group)
        
        # Results table
        self.startup_table = QTableWidget()
        self.startup_table.setColumnCount(5)
        self.startup_table.setHorizontalHeaderLabels([
            "Program", "Impact", "Source", "Location", "Recommendation"
        ])
        self.startup_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.startup_table.setAlternatingRowColors(True)
        
        layout.addWidget(self.startup_table)
        
        return widget
    
    def create_cache_content(self) -> QWidget:
        """Create cache cleanup content."""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # Summary
        self.cache_summary = QLabel("Click 'Scan' to analyze cache files")
        layout.addWidget(self.cache_summary)
        
        # Scan button
        scan_layout = QHBoxLayout()
        
        self.scan_cache_btn = QPushButton("Scan Cache Files")
        self.scan_cache_btn.clicked.connect(self.scan_cache_files)
        scan_layout.addWidget(self.scan_cache_btn)
        
        self.clean_btn = QPushButton("Simulate Clean All")
        self.clean_btn.setEnabled(False)
        self.clean_btn.clicked.connect(self.clean_cache)
        scan_layout.addWidget(self.clean_btn)
        
        scan_layout.addStretch()
        
        layout.addLayout(scan_layout)
        
        # Progress
        self.cache_progress = QLabel()
        layout.addWidget(self.cache_progress)
        
        # Category summary
        category_group = QGroupBox("Cache Categories")
        self.category_layout = QGridLayout(category_group)
        
        self.category_labels = {}
        categories = ['temp', 'browser', 'cache', 'logs', 'update', 'recent']
        row = 0
        col = 0
        for cat in categories:
            label = QLabel(f"{cat}: --")
            self.category_layout.addWidget(label, row, col)
            self.category_labels[cat] = label
            col += 1
            if col >= 2:
                col = 0
                row += 1
        
        layout.addWidget(category_group)
        
        # Results table
        self.cache_table = QTableWidget()
        self.cache_table.setColumnCount(5)
        self.cache_table.setHorizontalHeaderLabels([
            "Location", "Category", "Size", "Files", "Safe to Clean"
        ])
        self.cache_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.cache_table.setAlternatingRowColors(True)
        
        layout.addWidget(self.cache_table)
        
        return widget
    
    def switch_tab(self, tab):
        """Switch between tabs."""
        self.current_tab = tab
        
        if tab == 'startup':
            self.startup_btn.setChecked(True)
            self.cache_btn.setChecked(False)
            self.startup_content.show()
            self.cache_content.hide()
        else:
            self.startup_btn.setChecked(False)
            self.cache_btn.setChecked(True)
            self.startup_content.hide()
            self.cache_content.show()
    
    def scan_startup_programs(self):
        """Scan startup programs."""
        self.scan_startup_btn.setEnabled(False)
        self.startup_progress.setText("Scanning startup programs...")
        
        # Run scan in thread
        self.scan_thread = ScanThread('startup')
        self.scan_thread.progress.connect(self.startup_progress.setText)
        self.scan_thread.finished.connect(self.on_startup_scan_complete)
        self.scan_thread.start()
    
    def on_startup_scan_complete(self, result):
        """Handle startup scan completion."""
        self.scan_startup_btn.setEnabled(True)
        
        if result['type'] == 'startup':
            self.startup_programs = result['programs']
            summary = result['summary']
            
            # Update summary
            self.startup_summary.setText(
                f"Found {summary['total']} startup programs: "
                f"{summary['high_impact']} High, "
                f"{summary['medium_impact']} Medium, "
                f"{summary['low_impact']} Low impact"
            )
            
            # Update table
            self.startup_table.setRowCount(len(self.startup_programs))
            
            for row, program in enumerate(self.startup_programs):
                self.startup_table.setItem(row, 0, QTableWidgetItem(program['name']))
                
                # Impact
                impact_item = QTableWidgetItem(program['impact'])
                if program['impact'] == 'High':
                    impact_item.setBackground(QColor(255, 200, 200))
                elif program['impact'] == 'Medium':
                    impact_item.setBackground(QColor(255, 255, 200))
                else:
                    impact_item.setBackground(QColor(200, 255, 200))
                self.startup_table.setItem(row, 1, impact_item)
                
                self.startup_table.setItem(row, 2, QTableWidgetItem(program['source']))
                self.startup_table.setItem(row, 3, QTableWidgetItem(program['location'][:50]))
                self.startup_table.setItem(row, 4, QTableWidgetItem(program['recommendation']))
            
            self.startup_progress.setText(f"Scan complete! Found {len(self.startup_programs)} programs.")
    
    def scan_cache_files(self):
        """Scan cache files."""
        self.scan_cache_btn.setEnabled(False)
        self.clean_btn.setEnabled(False)
        self.cache_progress.setText("Scanning cache files...")
        
        # Run scan in thread
        self.scan_thread = ScanThread('cache')
        self.scan_thread.progress.connect(self.cache_progress.setText)
        self.scan_thread.finished.connect(self.on_cache_scan_complete)
        self.scan_thread.start()
    
    def on_cache_scan_complete(self, result):
        """Handle cache scan completion."""
        self.scan_cache_btn.setEnabled(True)
        
        if result['type'] == 'cache':
            self.cache_results = result['results']
            total = result['total']
            category = result['category']
            
            # Update summary
            self.cache_summary.setText(
                f"Total cleanable: {total['total_formatted']} "
                f"in {total['item_count']} locations ({total['file_count']} files)"
            )
            
            # Update category labels
            for cat, label in self.category_labels.items():
                if cat in category:
                    cat_data = category[cat]
                    label.setText(f"{cat}: {cat_data['total_formatted']}")
                else:
                    label.setText(f"{cat}: 0 B")
            
            # Update table
            self.cache_table.setRowCount(len(self.cache_results))
            
            for row, item in enumerate(self.cache_results):
                self.cache_table.setItem(row, 0, QTableWidgetItem(item['name']))
                self.cache_table.setItem(row, 1, QTableWidgetItem(item['category']))
                self.cache_table.setItem(row, 2, QTableWidgetItem(item.get('size_formatted', '0 B')))
                self.cache_table.setItem(row, 3, QTableWidgetItem(str(item.get('file_count', 0))))
                
                # Safe to clean
                safe_item = QTableWidgetItem("Yes" if item.get('safe_to_clean', False) else "No")
                if item.get('safe_to_clean', False):
                    safe_item.setBackground(QColor(200, 255, 200))
                else:
                    safe_item.setBackground(QColor(255, 200, 200))
                self.cache_table.setItem(row, 4, safe_item)
            
            # Enable clean button if there's something to clean
            if total['total_bytes'] > 0:
                self.clean_btn.setEnabled(True)
            
            self.cache_progress.setText(f"Scan complete! Found {len(self.cache_results)} locations.")
    
    def clean_cache(self):
        """Simulate cache cleaning."""
        reply = QMessageBox.question(
            self,
            "Simulate Clean",
            "This will simulate cleaning all safe cache files.\n\n"
            "No files will actually be deleted.\n\n"
            "Do you want to continue?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            result = self.cache_cleaner.clean_all_safe(simulate=True)
            
            QMessageBox.information(
                self,
                "Simulation Complete",
                f"Simulation results:\n\n"
                f"Locations that would be cleaned: {result['locations_cleaned']}\n"
                f"Files that would be deleted: {result['total_files_deleted']}\n"
                f"Space that would be freed: {result['total_formatted']}\n\n"
                f"{result['message']}"
            )
    
    def refresh(self):
        """Refresh the suggestions."""
        if self.current_tab == 'startup':
            self.scan_startup_programs()
        else:
            self.scan_cache_files()

    def set_live_suggestions(self, suggestions):
        """
        Update smart suggestions panel from latest metrics.

        Args:
            suggestions: List of suggestion dictionaries
        """
        suggestions = suggestions or []
        self.live_suggestions_table.setRowCount(len(suggestions))

        if not suggestions:
            self.live_summary_label.setText("No live suggestions for the current system state.")
            return

        counts = {'Critical': 0, 'High': 0, 'Medium': 0, 'Low': 0}

        for row, suggestion in enumerate(suggestions):
            severity = suggestion.get('severity', 'Low')
            title = suggestion.get('title', 'Suggestion')
            message = suggestion.get('message', '')

            sev_item = QTableWidgetItem(severity)
            if severity == 'Critical':
                sev_item.setBackground(QColor(255, 120, 120))
            elif severity == 'High':
                sev_item.setBackground(QColor(255, 200, 140))
            elif severity == 'Medium':
                sev_item.setBackground(QColor(255, 245, 170))
            else:
                sev_item.setBackground(QColor(200, 255, 200))

            self.live_suggestions_table.setItem(row, 0, sev_item)
            self.live_suggestions_table.setItem(row, 1, QTableWidgetItem(title))
            self.live_suggestions_table.setItem(row, 2, QTableWidgetItem(message))

            if severity in counts:
                counts[severity] += 1

        self.live_summary_label.setText(
            f"Live suggestions: {len(suggestions)} "
            f"(Critical: {counts['Critical']}, High: {counts['High']}, "
            f"Medium: {counts['Medium']}, Low: {counts['Low']})"
        )

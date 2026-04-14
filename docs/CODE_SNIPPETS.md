"""
SYSTEM OBSERVER - CODE INTEGRATION SNIPPETS
============================================

Complete code snippets for integrating all 6 features.
Copy and paste these into the appropriate files.
"""

═════════════════════════════════════════════════════════════════════════
FILE: ui/main_window.py
═════════════════════════════════════════════════════════════════════════

SECTION 1: ADD THESE IMPORTS (at top of file, after existing imports):
──────────────────────────────────────────────────────────────────────

from analysis.performance_analyzer import PerformanceAnalyzer
from analysis.suggestions_engine import SuggestionsEngine
from backend.report_generator import ReportGenerator
from backend.daily_summary import DailySummary
from ui.graph_dashboard import GraphDashboard


SECTION 2: IN MainWindow.__init__() (after existing monitor initialization):
─────────────────────────────────────────────────────────────────────────

# Initialize new feature modules
self.performance_analyzer = PerformanceAnalyzer()
self.suggestions_engine = SuggestionsEngine()
self.report_generator = ReportGenerator()
self.daily_summary = DailySummary()

# Store current suggestions
self.current_suggestions = []
self.current_impact_analysis = {}


SECTION 3: IN init_ui() (after adding other tabs):
──────────────────────────────────────────────────

# Add graphs tab
self.graph_dashboard = GraphDashboard()
self.tab_widget.addTab(self.graph_dashboard, "Graphs")


SECTION 4: IN _setup_background_monitoring() (after existing connection):
──────────────────────────────────────────────────────────────────────

self.monitor_worker.metrics_updated.connect(self._process_new_metrics)


SECTION 5: ADD THIS NEW METHOD TO MainWindow CLASS:
───────────────────────────────────────────────────

def _process_new_metrics(self, metrics):
    """Process new metrics with feature analysis."""
    # Call existing handler first
    self.on_metrics_updated(metrics)

    # Feature 1: Performance Analysis
    try:
        top_cpu = self.current_metrics['processes'].get('top_cpu', [])
        top_memory = self.current_metrics['processes'].get('top_memory', [])
        cpu_usage = self.current_metrics['cpu']['usage']
        memory_usage = self.current_metrics['memory']['usage']

        self.current_impact_analysis = self.performance_analyzer.analyze_process_impact(
            top_cpu, top_memory, cpu_usage, memory_usage
        )
        self.current_metrics['impact_analysis'] = self.current_impact_analysis
    except Exception as e:
        print(f"Performance analysis error: {e}")

    # Feature 2: Smart Suggestions
    try:
        all_processes = (
            self.current_metrics['processes'].get('top_cpu', []) +
            self.current_metrics['processes'].get('top_memory', [])
        )
        self.current_suggestions = self.suggestions_engine.generate_suggestions(
            self.current_metrics,
            all_processes
        )
    except Exception as e:
        print(f"Suggestions error: {e}")

    # Update suggestions view
    self._update_suggestions_view()

    # Update graphs
    if hasattr(self, 'graph_dashboard'):
        self.graph_dashboard.update_metrics(
            cpu_usage,
            memory_usage,
            self.current_metrics.get('health_score', 0)
        )


SECTION 6: ADD THESE METHODS TO MainWindow CLASS:
──────────────────────────────────────────────────

def _update_suggestions_view(self):
    """Update suggestions view with new data."""
    if hasattr(self, 'suggestions_view'):
        try:
            daily_stats = self.daily_summary.calculate_daily_stats()
            self.suggestions_view.update_suggestions(
                self.current_suggestions,
                daily_stats,
                self.current_metrics,
                self.current_impact_analysis
            )
        except Exception as e:
            print(f"View update error: {e}")


def generate_system_report(self):
    """Generate diagnostic report."""
    try:
        report_info = self.report_generator.generate_report(
            metrics=self.current_metrics,
            anomalies=self.current_metrics.get('anomalies', []),
            suggestions=self.current_suggestions,
            daily_summary=self.daily_summary.calculate_daily_stats(),
            include_processes=True
        )

        from PySide6.QtWidgets import QMessageBox
        QMessageBox.information(
            self, "Report Generated",
            f"Diagnostic report saved to:\n{report_info['txt_path']}\n\n"
            f"CSV available at:\n{report_info['csv_path']}"
        )
    except Exception as e:
        from PySide6.QtWidgets import QMessageBox
        QMessageBox.critical(self, "Error", f"Report generation failed: {e}")


def clear_graphs(self):
    """Clear graph history."""
    if hasattr(self, 'graph_dashboard'):
        self.graph_dashboard.clear_history()


═════════════════════════════════════════════════════════════════════════
FILE: ui/suggestions_view.py
═════════════════════════════════════════════════════════════════════════

SECTION 1: ADD THESE IMPORTS (at top):
──────────────────────────────────────

from backend.daily_summary import DailySummary
from backend.report_generator import ReportGenerator


SECTION 2: IN SuggestionsView.__init__() (after existing init):
───────────────────────────────────────────────────────────────

self.daily_summary = DailySummary()
self.report_generator = ReportGenerator()
self.current_suggestions = []
self.current_metrics = {}


SECTION 3: ADD THESE METHODS TO SuggestionsView CLASS:
──────────────────────────────────────────────────────

def display_smart_suggestions(self, suggestions):
    """Display smart suggestions in table."""
    self.suggestions_table.setRowCount(0)

    if not suggestions:
        return

    for suggestion in suggestions:
        row = self.suggestions_table.rowCount()
        self.suggestions_table.insertRow(row)

        severity = suggestion.get('severity', '')
        title = suggestion.get('title', '')
        message = suggestion.get('message', '')[:150]

        severity_item = QTableWidgetItem(severity)
        title_item = QTableWidgetItem(title)
        message_item = QTableWidgetItem(message)

        # Color code by severity
        if severity == 'Critical':
            color = QColor('#D32F2F')
        elif severity == 'High':
            color = QColor('#F57C00')
        elif severity == 'Medium':
            color = QColor('#FBC02D')
        else:
            color = QColor('#388E3C')

        for item in [severity_item, title_item, message_item]:
            item.setForeground(color)

        self.suggestions_table.setItem(row, 0, severity_item)
        self.suggestions_table.setItem(row, 1, title_item)
        self.suggestions_table.setItem(row, 2, message_item)


def display_daily_stats(self, daily_stats):
    """Display daily statistics."""
    if not hasattr(self, 'daily_stats_label'):
        self.daily_stats_label = QLabel()
        # Add to your layout

    stats_text = self.daily_summary.format_summary_for_display(daily_stats)
    self.daily_stats_label.setText(stats_text)


def update_suggestions(self, suggestions, daily_stats, metrics, impact_analysis=None):
    """Update suggestions view with new data."""
    self.current_suggestions = suggestions
    self.current_metrics = metrics

    self.display_smart_suggestions(suggestions)
    self.display_daily_stats(daily_stats)


def on_generate_report_clicked(self):
    """Handle generate report button."""
    try:
        report_info = self.report_generator.generate_report(
            metrics=self.current_metrics,
            anomalies=self.current_metrics.get('anomalies', []),
            suggestions=self.current_suggestions,
            daily_summary=self.daily_summary.calculate_daily_stats(),
            include_processes=True
        )

        QMessageBox.information(
            self, "Success",
            f"Report saved to:\n{report_info['txt_path']}"
        )
    except Exception as e:
        QMessageBox.critical(self, "Error", f"Failed: {str(e)}")


═════════════════════════════════════════════════════════════════════════
OPTIONAL: UI BUTTONS
════════════════════════════════════════════════════════════════════════

Add these buttons to toolbar for easy access:

In main_window.py or suggestions_view.py:

generate_report_btn = QPushButton("Generate Report")
generate_report_btn.clicked.connect(self.generate_system_report)
toolbar.addWidget(generate_report_btn)

clear_graphs_btn = QPushButton("Clear Graphs")
clear_graphs_btn.clicked.connect(self.clear_graphs)
toolbar.addWidget(clear_graphs_btn)


═════════════════════════════════════════════════════════════════════════

That's all the code you need! Follow the sections in order and everything
will integrate smoothly.

Questions? See docs/QUICK_START.md or docs/FEATURES.md
"""

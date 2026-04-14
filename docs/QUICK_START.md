"""
SYSTEM OBSERVER - QUICK START GUIDE
===================================

Follow these steps to integrate the 6 new features into your project.
"""

OVERVIEW
========

6 new features have been created to extend System Observer:
1. Performance Cause Explanation
2. Smart Suggestions Engine
3. Diagnostic Report Generator
4. Daily System Summary
5. Graph Dashboard
6. Startup Impact Analyzer (already implemented)

All features are production-ready and require NO rewriting of existing code.


NEW FILES CREATED
=================

Python Modules (in their respective folders):
  • analysis/performance_analyzer.py
  • analysis/suggestions_engine.py
  • backend/report_generator.py
  • backend/daily_summary.py
  • ui/graph_dashboard.py

All are ready to use - just copy them to your project.


INTEGRATION - 3 SIMPLE STEPS
=============================

STEP 1: Install Dependencies
────────────────────────────
Already done in requirements.txt:
  pip install -r requirements.txt

(Adds: pyqtgraph, matplotlib for graph visualization)


STEP 2: Modify ui/main_window.py
─────────────────────────────────

Add imports (at top):
  from analysis.performance_analyzer import PerformanceAnalyzer
  from analysis.suggestions_engine import SuggestionsEngine
  from backend.report_generator import ReportGenerator
  from backend.daily_summary import DailySummary
  from ui.graph_dashboard import GraphDashboard

In MainWindow.__init__() add:
  self.performance_analyzer = PerformanceAnalyzer()
  self.suggestions_engine = SuggestionsEngine()
  self.report_generator = ReportGenerator()
  self.daily_summary = DailySummary()

In init_ui() after other tabs, add:
  self.graph_dashboard = GraphDashboard()
  self.tab_widget.addTab(self.graph_dashboard, "Graphs")

Create new method:
  def _process_new_metrics(self, metrics):
      """Process new metrics with feature analysis."""
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

      # Feature 2: Suggestions
      try:
          self.current_suggestions = self.suggestions_engine.generate_suggestions(
              self.current_metrics,
              top_cpu + top_memory
          )
      except Exception as e:
          print(f"Suggestions error: {e}")

      # Update suggestions view
      if hasattr(self, 'suggestions_view'):
          try:
              daily_stats = self.daily_summary.calculate_daily_stats()
              self.suggestions_view.update_suggestions(
                  self.current_suggestions,
                  daily_stats,
                  self.current_metrics
              )
          except Exception as e:
              print(f"View update error: {e}")

      # Update graphs
      if hasattr(self, 'graph_dashboard'):
          self.graph_dashboard.update_metrics(
              cpu_usage,
              memory_usage,
              self.current_metrics.get('health_score', 0)
          )

In _setup_background_monitoring() add:
  self.monitor_worker.metrics_updated.connect(self._process_new_metrics)

Add method for report generation:
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
              self, "Success",
              f"Report saved to:\n{report_info['txt_path']}"
          )
      except Exception as e:
          from PySide6.QtWidgets import QMessageBox
          QMessageBox.critical(self, "Error", f"Failed: {str(e)}")


STEP 3: Enhance ui/suggestions_view.py
───────────────────────────────────────

Add imports:
  from backend.daily_summary import DailySummary
  from backend.report_generator import ReportGenerator

In __init__() add:
  self.daily_summary = DailySummary()
  self.report_generator = ReportGenerator()
  self.current_suggestions = []
  self.current_metrics = {}

Add method for displaying suggestions:
  def display_smart_suggestions(self, suggestions):
      """Display suggestions in table."""
      self.suggestions_table.setRowCount(0)

      for suggestion in suggestions:
          row = self.suggestions_table.rowCount()
          self.suggestions_table.insertRow(row)

          severity = suggestion.get('severity', '')
          title = suggestion.get('title', '')
          message = suggestion.get('message', '')[:100]

          self.suggestions_table.setItem(row, 0, QTableWidgetItem(severity))
          self.suggestions_table.setItem(row, 1, QTableWidgetItem(title))
          self.suggestions_table.setItem(row, 2, QTableWidgetItem(message))

          # Color by severity
          if severity == 'Critical':
              color = QColor('#D32F2F')
          elif severity == 'High':
              color = QColor('#F57C00')
          elif severity == 'Medium':
              color = QColor('#FBC02D')
          else:
              color = QColor('#388E3C')

          for col in range(3):
              self.suggestions_table.item(row, col).setForeground(color)

Add method to update from data:
  def update_suggestions(self, suggestions, daily_stats, metrics):
      """Update suggestions view."""
      self.current_suggestions = suggestions
      self.current_metrics = metrics
      self.display_smart_suggestions(suggestions)

Add button handler:
  def on_generate_report_clicked(self):
      """Generate diagnostic report."""
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


VERIFICATION
=============

After integration, verify:

1. Application starts without errors
   Windows: double-click `run_app.bat`
   Command Line: `python main.py`

2. New "Graphs" tab appears in UI

3. Suggestions appear in Suggestions tab

4. Generate Report button works

5. Daily statistics display correctly

Quick test:
  python example_features.py


SUPPORT
========

For detailed information:
  • See: docs/FEATURES.md (feature overview)
  • See: docs/CODE_SNIPPETS.md (more code examples)
  • For troubleshooting: See docs/TROUBLESHOOTING.md

All code snippets above are copy-paste ready!


DONE!
======

That's it! The 6 features are now integrated.

Next: Run the application and test the new features.

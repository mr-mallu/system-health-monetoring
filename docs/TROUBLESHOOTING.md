"""
TROUBLESHOOTING GUIDE
====================

Common issues and solutions for System Observer extension.
"""

IMPORT ERRORS
=============

Error: "ModuleNotFoundError: No module named 'performance_analyzer'"
─────────────────────────────────────────────────────────────────

Cause: New modules not in correct location or not copied

Solution:
  1. Check files are in correct folders:
     - analysis/performance_analyzer.py
     - analysis/suggestions_engine.py
     - backend/report_generator.py
     - backend/daily_summary.py
     - ui/graph_dashboard.py

  2. Check imports in main_window.py reference correct paths

  3. Reinstall if needed:
     pip install -r requirements.txt


Error: "ImportError: cannot import name 'GraphDashboard'"
─────────────────────────────────────────────────────────

Cause: ui/graph_dashboard.py not found or import path wrong

Solution:
  1. Verify file exists: ui/graph_dashboard.py
  2. Check import statement:
     from ui.graph_dashboard import GraphDashboard
  3. Ensure you're in project root when running


GRAPH DISPLAY ISSUES
====================

Graphs Tab Shows Text Instead of Graphs
────────────────────────────────────────

Cause: PyQtGraph not installed (uses fallback message)

Solution A (Install PyQtGraph):
  pip install pyqtgraph>=0.12.0
  Run app again

Solution B (Use Matplotlib):
  pip install matplotlib>=3.5.0
  PyQtGraph will try first, then fall back to Matplotlib


Graphs Tab Doesn't Appear
──────────────────────────

Cause: GraphDashboard initialization failed silently

Solution:
  1. Check console for errors
  2. Verify code in init_ui():
     self.graph_dashboard = GraphDashboard()
     self.tab_widget.addTab(self.graph_dashboard, "Graphs")
  3. Verify that tab_widget is initialized before adding tab


Graphs Not Updating
───────────────────

Cause: Signal connection not established

Solution:
  1. Verify in _process_new_metrics():
     self.graph_dashboard.update_metrics(cpu, memory, health)
  2. Check metrics are numeric (not None)
  3. Verify monitor worker is running


SUGGESTIONS NOT APPEARING
==========================

No Suggestions in Suggestions Tab
─────────────────────────────────

Cause: Suggestions update method not called or empty

Solutions:
  1. System might be running normally:
     - Suggestions appear when issues detected
     - Run a heavy application to trigger suggestions

  2. Verify code:
     - Check _update_suggestions_view() is called
     - Check suggestions_view.update_suggestions() exists

  3. Check console for errors

  4. Verify generate_suggestions is working:
     - Run: python example_features.py
     - Should show suggestions output


Suggestions Table Empty or Errors
──────────────────────────────────

Cause: Display method not implemented or data format wrong

Solution:
  1. Check display_smart_suggestions() method added
  2. Verify suggestion dict has required keys:
     - 'severity'
     - 'title'
     - 'message'
  3. Check for exceptions in console


REPORT GENERATION ISSUES
========================

Reports Not Creating (Button Does Nothing)
───────────────────────────────────────────

Cause: Button not connected or method not implemented

Solution:
  1. Verify button exists and connected:
     generate_report_btn.clicked.connect(self.generate_system_report)
  2. Verify generate_system_report() method exists
  3. Check console for error messages


Reports Not Saving to Disk
──────────────────────────

Cause: data/reports/ directory doesn't exist or no permissions

Solution:
  1. Create directory:
     mkdir data/reports

  2. Check permissions:
     ls -la data/reports/

  3. Verify path in report_generator.py is correct

  4. Try manual test:
     from backend.report_generator import ReportGenerator
     gen = ReportGenerator()
     report = gen.generate_report({...})


"Permission Denied" Error
─────────────────────────

Cause: data/reports/ directory permissions

Solution:
  1. Check directory permissions:
     ls -ld data/reports/

  2. Fix permissions (Windows):
     Right-click folder → Properties → Security → Edit

  3. Or create fresh directory:
     rmdir data/reports (if safe)
     mkdir data/reports


DAILY STATISTICS ISSUES
=======================

Daily Stats Not Displaying
──────────────────────────

Cause: Daily stats label not created or updated

Solution:
  1. Check daily_stats_label exists in suggestions_view.py
  2. Verify display_daily_stats() method called
  3. Check for database errors in console
  4. Ensure database has metrics (monitoring runs for a while first)


Database Query Errors
─────────────────────

Cause: Database table structure issue

Solution:
  1. This should not happen - uses existing tables
  2. If it does, check:
     - system_observer.db file exists
     - Database not corrupted
  3. If corrupted:
     - Backup current DB
     - Delete system_observer.db
     - Restart app (recreates DB)


PERFORMANCE ISSUES
==================

Application Running Slowly
───────────────────────────

Cause: Feature analysis running in main thread too often

Solution:
  1. Check _process_new_metrics() is called less frequently
  2. Verify error handling - exceptions slow things down
  3. Check CPU usage with:
     python example_features.py
     (If fast here, issue is integration)


Memory Usage High
─────────────────

Cause: Graph history or cache growing too large

Solution:
  1. Clear graph history:
     Clear Graphs button in UI
     Or: graph_dashboard.clear_history()
  2. Old reports are stored - delete manually:
     rm data/reports/system_report_*.txt


TESTING & VERIFICATION
======================

To Test Just Features (Without Full App):
──────────────────────────────────────────

Run:
  python example_features.py

This tests:
  ✓ Performance analyzer
  ✓ Suggestions engine
  ✓ Report generator
  ✓ Daily summary
  ✓ All features working together

If this works, issue is with integration into UI


Manual Feature Testing:
───────────────────────

Test Performance Analyzer:
  from analysis.performance_analyzer import PerformanceAnalyzer
  analyzer = PerformanceAnalyzer()
  impact = analyzer.analyze_process_impact([...], [...], 75, 85)
  print(impact['explanation'])

Test Suggestions Engine:
  from analysis.suggestions_engine import SuggestionsEngine
  engine = SuggestionsEngine()
  suggestions = engine.generate_suggestions(metrics, processes)
  print(f"Generated {len(suggestions)} suggestions")

Test Report Generator:
  from backend.report_generator import ReportGenerator
  gen = ReportGenerator()
  report = gen.generate_report(metrics, anomalies, suggestions, daily_stats)
  print(f"Report: {report['txt_path']}")


DEBUGGING TIPS
==============

Enable Debug Output
────────────────────

In main_window.py, change:
  except Exception as e:
      print(f"Error: {e}")

To:
  except Exception as e:
      import traceback
      print(f"Error: {e}")
      traceback.print_exc()

This shows full error stack trace


Check What's Running
─────────────────────

Add debug prints:
  print(f"Metrics: CPU={cpu}%, Memory={memory}%")
  print(f"Suggestions generated: {len(suggestions)}")
  print(f"Graph updated")


Monitor Database Access
────────────────────────

Check if database working:
  from backend.database import get_database
  db = get_database()
  metrics = db.get_metrics_history(limit=5)
  print(f"Found {len(metrics)} records")


GETTING HELP
=============

If You're Still Stuck:

1. Check console output for actual error messages
2. Run: python example_features.py
   (Confirms features work)
3. Check file locations are correct
4. Verify all new files copied to project
5. Reinstall dependencies:
   pip install -r requirements.txt --upgrade

If still stuck:
  • Review docs/QUICK_START.md
  • Check docs/CODE_SNIPPETS.md for exact code
  • Verify code matches examples exactly
  • Check Python version (3.8+)
  • Verify PyS IDE6 works (launch existing app first)


═══════════════════════════════════════════════════════════════════════

Most Common Issues:
  1. Files not in correct folders → Copy to right location
  2. Imports not added → Add to top of file
  3. Methods not added → Copy methods exactly
  4. Signal not connected → Add connect() call
  5. Graphs library missing → pip install pyqtgraph

95% of issues fixed by these steps!
"""

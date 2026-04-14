"""
FEATURES DEMONSTRATION EXAMPLE
================================

This example demonstrates all 6 new features working together.
Run this script to see the modules in action.
"""

#!/usr/bin/env python3
"""
Example: Using all new System Observer features
"""

import sys
import os
from datetime import datetime

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def example_performance_analyzer():
    """FEATURE 1: Performance Cause Explanation"""
    print("\\n" + "="*70)
    print("FEATURE 1: PERFORMANCE CAUSE EXPLANATION")
    print("="*70)

    from analysis.performance_analyzer import PerformanceAnalyzer

    analyzer = PerformanceAnalyzer()

    # Example top processes
    top_cpu = [
        {'name': 'chrome.exe', 'pid': 1234, 'cpu_percent': 52.0, 'memory_mb': 500},
        {'name': 'python.exe', 'pid': 5678, 'cpu_percent': 25.0, 'memory_mb': 200},
    ]

    top_memory = [
        {'name': 'chrome.exe', 'pid': 1234, 'cpu_percent': 52.0, 'memory_mb': 500, 'memory_percent': 45},
        {'name': 'outlook.exe', 'pid': 9999, 'cpu_percent': 5.0, 'memory_mb': 300, 'memory_percent': 28},
    ]

    # Analyze impact
    impact = analyzer.analyze_process_impact(
        top_cpu_processes=top_cpu,
        top_memory_processes=top_memory,
        current_cpu=75.0,
        current_memory=85.0
    )

    print(f"\\nPrimary Cause: {impact['primary_cause']}")
    print(f"Risk Level: {impact['risk_level']}")
    print(f"\\nExplanation:\\n{impact['explanation']}")
    print(f"\\nRecommendation:\\n{impact['recommendation']}")

    # Get process summary
    all_processes = top_cpu + top_memory
    summary = analyzer.get_process_summary(all_processes)
    print(f"\\nProcess Summary: {summary}")


def example_suggestions_engine():
    """FEATURE 2: Smart Suggestions Engine"""
    print("\\n" + "="*70)
    print("FEATURE 2: SMART SUGGESTIONS ENGINE")
    print("="*70)

    from analysis.suggestions_engine import SuggestionsEngine

    engine = SuggestionsEngine()

    # Example metrics
    metrics = {
        'cpu': {'usage': 85.0, 'average': 65.0},
        'memory': {'usage': 80.0, 'average': 60.0},
        'disk': {'usage': 92.0},
        'processes': {'count': 200}
    }

    processes = [
        {'name': 'chrome.exe', 'pid': 1234, 'cpu_percent': 40.0, 'memory_percent': 35},
        {'name': 'firefox.exe', 'pid': 5678, 'cpu_percent': 25.0, 'memory_percent': 30},
        {'name': 'notepad.exe', 'pid': 9999, 'cpu_percent': 5.0, 'memory_percent': 5},
    ]

    # Generate suggestions
    suggestions = engine.generate_suggestions(metrics, processes)

    print(f"\\nGenerated {len(suggestions)} suggestions:\\n")

    by_severity = {}
    for suggestion in suggestions:
        severity = suggestion.get('severity')
        if severity not in by_severity:
            by_severity[severity] = []
        by_severity[severity].append(suggestion)

    for severity in ['Critical', 'High', 'Medium', 'Low']:
        if severity in by_severity:
            print(f"\\n{severity}:")
            for suggestion in by_severity[severity]:
                print(f"  • {suggestion.get('title')}")
                print(f"    {suggestion.get('message')}")


def example_report_generator():
    """FEATURE 3: Diagnostic Report Generator"""
    print("\\n" + "="*70)
    print("FEATURE 3: DIAGNOSTIC REPORT GENERATOR")
    print("="*70)

    from backend.report_generator import ReportGenerator

    generator = ReportGenerator()

    # Example data
    metrics = {
        'cpu': {'usage': 65.0, 'average': 50.0, 'cores': 8},
        'memory': {'usage': 70.0, 'average': 60.0, 'info': {'used_mb': 7000, 'total_mb': 10000}},
        'disk': {'usage': 80.0, 'info': {'used_gb': 400, 'total_gb': 500}},
        'processes': {'count': 180, 'top_cpu': [], 'top_memory': []},
        'health_score': 75.0,
        'health_status': 'Good'
    }

    anomalies = [
        {'type': 'High CPU', 'severity': 'High', 'description': 'CPU usage exceeded threshold'},
    ]

    suggestions = [
        {'type': 'CPU_HIGH', 'severity': 'High', 'title': 'High CPU Usage', 'message': 'Consider closing unnecessary applications'},
    ]

    daily_summary = {
        'peak_cpu': 85.0,
        'peak_memory': 90.0,
        'avg_cpu': 60.0,
        'avg_memory': 65.0,
        'alert_count': 5,
        'avg_health_score': 72.0
    }

    # Generate report
    report = generator.generate_report(
        metrics=metrics,
        anomalies=anomalies,
        suggestions=suggestions,
        daily_summary=daily_summary,
        include_processes=True
    )

    print(f"\\nReport Generated:")
    print(f"  TXT: {report['txt_path']}")
    print(f"  CSV: {report['csv_path']}")
    print(f"  Timestamp: {report['timestamp']}")

    # List available reports
    reports = generator.list_reports()
    print(f"\\nTotal reports available: {len(reports)}")
    if reports:
        print(f"Latest report: {reports[0]['filename']}")


def example_daily_summary():
    """FEATURE 5: Daily System Summary"""
    print("\\n" + "="*70)
    print("FEATURE 5: DAILY SYSTEM SUMMARY")
    print("="*70)

    from backend.daily_summary import DailySummary

    daily = DailySummary()

    # Get today's stats
    today_stats = daily.calculate_daily_stats()

    print("\\nToday's Statistics:")
    print(daily.format_summary_for_display(today_stats))

    # Get weekly summary
    print("\\n\\nWeekly Summary (Last 7 Days):")
    weekly = daily.get_weekly_summary()

    print("\\nDate          Peak CPU  Peak Memory  Avg CPU  Avg Memory  Alerts")
    print("-" * 70)
    for day_stats in weekly:
        print(
            f"{day_stats['date']}  "
            f"{day_stats['peak_cpu']:>6.1f}%  "
            f"{day_stats['peak_memory']:>7.1f}%    "
            f"{day_stats['avg_cpu']:>6.1f}%  "
            f"{day_stats['avg_memory']:>7.1f}%    "
            f"{day_stats['alert_count']:>3}"
        )


def example_graph_dashboard():
    """FEATURE 6: Graph Dashboard"""
    print("\\n" + "="*70)
    print("FEATURE 6: GRAPH DASHBOARD")
    print("="*70)

    from ui.graph_dashboard import GraphDashboard

    print("\\nNote: GraphDashboard is a GUI component (PySide6/Qt widget)")
    print("It requires a running Qt application to display.")
    print("\\nWhen integrated in the main application, it displays:")
    print("  • Real-time CPU usage graph")
    print("  • Real-time Memory usage graph")
    print("  • Real-time Health score trend graph")
    print("\\nGraphs update automatically with each metrics refresh.")

    # In a real scenario (would need Qt application running):
    # from PySide6.QtWidgets import QApplication
    # app = QApplication(sys.argv)
    # dashboard = GraphDashboard()
    # for i in range(60):
    #     dashboard.update_metrics(50 + i % 30, 60 + i % 20, 75 - i % 15)


def example_integration():
    """EXAMPLE: All features working together"""
    print("\\n" + "="*70)
    print("INTEGRATION EXAMPLE: ALL FEATURES TOGETHER")
    print("="*70)

    from analysis.performance_analyzer import PerformanceAnalyzer
    from analysis.suggestions_engine import SuggestionsEngine
    from backend.report_generator import ReportGenerator
    from backend.daily_summary import DailySummary

    # Initialize modules
    analyzer = PerformanceAnalyzer()
    engine = SuggestionsEngine()
    report_gen = ReportGenerator()
    daily = DailySummary()

    # Simulate current system state
    metrics = {
        'cpu': {'usage': 75.0, 'average': 60.0, 'cores': 8},
        'memory': {'usage': 82.0, 'average': 65.0, 'info': {'used_mb': 8200, 'total_mb': 10000}},
        'disk': {'usage': 88.0},
        'processes': {'count': 220, 'top_cpu': [], 'top_memory': []},
        'health_score': 70.0,
        'health_status': 'Fair',
        'anomalies': []
    }

    # Setup top processes
    top_cpu = [
        {'name': 'chrome.exe', 'pid': 1000, 'cpu_percent': 45.0, 'memory_mb': 600},
    ]
    top_memory = [
        {'name': 'chrome.exe', 'pid': 1000, 'memory_mb': 600, 'memory_percent': 42},
    ]

    metrics['processes']['top_cpu'] = top_cpu
    metrics['processes']['top_memory'] = top_memory

    print("\\n1. Analyzing performance impact...")
    impact = analyzer.analyze_process_impact(top_cpu, top_memory, 75.0, 82.0)
    print(f"   Primary cause: {impact['primary_cause']} ({impact['risk_level']} risk)")

    print("\\n2. Generating smart suggestions...")
    suggestions = engine.generate_suggestions(metrics, top_cpu + top_memory)
    critical_count = sum(1 for s in suggestions if s['severity'] == 'Critical')
    high_count = sum(1 for s in suggestions if s['severity'] == 'High')
    print(f"   Generated {len(suggestions)} suggestions ({critical_count} critical, {high_count} high)")

    print("\\n3. Calculating daily statistics...")
    daily_stats = daily.calculate_daily_stats()
    print(f"   Peak CPU: {daily_stats['peak_cpu']:.1f}%")
    print(f"   Peak Memory: {daily_stats['peak_memory']:.1f}%")
    print(f"   Alerts today: {daily_stats['alert_count']}")

    print("\\n4. Generating diagnostic report...")
    report = report_gen.generate_report(
        metrics=metrics,
        anomalies=metrics['anomalies'],
        suggestions=suggestions,
        daily_summary=daily_stats,
        include_processes=True
    )
    print(f"   Report saved: {os.path.basename(report['txt_path'])}")

    print("\\n5. Summary:")
    print(f"   • System Status: {metrics['health_status']}")
    print(f"   • Health Score: {metrics['health_score']:.1f}/100")
    print(f"   • Top Issue: {impact['primary_cause']}")
    print(f"   • Action Items: {len([s for s in suggestions if s['severity'] in ['Critical', 'High']])}")

    print("\\n" + "="*70)
    print("Integration example complete!")
    print("="*70)


if __name__ == '__main__':
    print("\\n" + "="*70)
    print("SYSTEM OBSERVER - NEW FEATURES DEMONSTRATION")
    print("="*70)

    try:
        example_performance_analyzer()
        example_suggestions_engine()
        example_report_generator()
        example_daily_summary()
        example_graph_dashboard()
        example_integration()

        print("\\n\\nDemonstration complete!")
        print("Check the data/reports/ directory for generated report files.")

    except Exception as e:
        print(f"\\nError during demonstration: {e}")
        import traceback
        traceback.print_exc()

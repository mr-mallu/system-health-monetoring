"""
Report Generator Module
Generates comprehensive system diagnostic reports in PDF format.
Includes system metrics, health score, anomalies, suggestions,
and robust HTML layout designed explicitly for PySide6's QTextDocument.
"""

import os
from datetime import datetime
from typing import List, Dict, Optional
import config


PROJECT_OVERVIEW = {
    'title': 'System Health Monitoring System',
    'description': (
        'The System Health Monitoring System is a desktop application that monitors '
        'computer health in real time. It tracks CPU usage, memory usage, disk usage, '
        'and system activity so users can identify performance issues early and '
        'respond before they turn into failures.'
    ),
    'purpose': [
        'Automate day-to-day system monitoring.',
        'Reduce the risk of crashes and slowdowns.',
        'Improve overall performance visibility.',
        'Provide timely alerts and status updates.'
    ],
    'problems_solved': [
        'Manual monitoring is time-consuming and inconsistent.',
        'Users often receive no early warning before a failure.',
        'Tracking multiple hardware metrics together is difficult.'
    ],
    'key_features': [
        'Real-time CPU monitoring',
        'RAM usage tracking',
        'Disk space analysis',
        'Alert and notification support',
        'Simple dashboard interface'
    ],
    'workflow': [
        'Collect CPU, memory, disk, and process data.',
        'Analyze the readings in the backend.',
        'Store relevant monitoring history in the database.',
        'Display insights and trends in the dashboard.',
        'Generate alerts when thresholds are exceeded.'
    ],
    'architecture': [
        'User',
        'Dashboard (UI)',
        'Backend services',
        'System metrics (CPU, RAM, Disk)'
    ],
    'modules': [
        'Data Collection Module',
        'Monitoring Module',
        'Alert Module',
        'User Interface Module'
    ],
    'technologies': [
        'Python',
        'PySide6 desktop UI',
        'psutil system monitoring',
        'SQLite database'
    ],
    'advantages': [
        'Easy to use',
        'Real-time monitoring',
        'Helps prevent system failure',
        'Saves time through automation'
    ],
    'limitations': [
        'Focused on the local machine by default.',
        'Alert handling is basic compared with enterprise monitoring tools.',
        'Remote or cloud monitoring is not yet built in.'
    ],
    'future_scope': [
        'Mobile app integration',
        'Cloud and multi-device monitoring',
        'AI-based predictive health analysis'
    ],
    'conclusion': (
        'This project provides an efficient way to observe system performance and '
        'maintain system health through live metrics, alerts, historical insight, '
        'and report generation.'
    )
}


class ReportGenerator:
    """
    Generates comprehensive system diagnostic reports.
    Supports PDF output format with highly compatible HTML template.
    """

    def __init__(self, reports_dir: str = None):
        if reports_dir is None:
            base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            reports_dir = os.path.join(base_dir, 'data', 'reports')

        self.reports_dir = reports_dir
        os.makedirs(reports_dir, exist_ok=True)

    def generate_report(self, metrics: Dict, anomalies: List[Dict],
                       suggestions: List[Dict], daily_summary: Optional[Dict] = None,
                       include_processes: bool = False,
                       graph_data: Optional[Dict] = None,
                       alerts: Optional[List[Dict]] = None,
                       graph_image_paths=None) -> Dict:
        """
        Generate a comprehensive system PDF report.
        """
        timestamp = datetime.now()
        report_filename = f"system_report_{timestamp.strftime('%Y%m%d_%H%M%S')}"
        pdf_path = os.path.join(self.reports_dir, f"{report_filename}.pdf")

        html_content = self._generate_html_content(
            metrics, anomalies, suggestions, daily_summary,
            include_processes, graph_data, alerts
        )

        from PySide6.QtGui import QTextDocument
        from PySide6.QtPrintSupport import QPrinter

        doc = QTextDocument()
        doc.setHtml(html_content)
        printer = QPrinter(QPrinter.HighResolution)
        printer.setOutputFormat(QPrinter.PdfFormat)
        printer.setOutputFileName(pdf_path)
        doc.print_(printer)

        return {
            'pdf_path': pdf_path,
            'txt_path': pdf_path,
            'csv_path': '-',
            'timestamp': timestamp,
            'filename_base': report_filename,
            'metrics_snapshot': metrics
        }

    # ------------------------------------------------------------------ #
    # Strict HTML 3.2 Compatible Layout Builder
    # ------------------------------------------------------------------ #

    def _build_metric_graph(self, title: str, value: float, color: str) -> str:
        """
        Creates a horizontal progress bar using simple tables to ensure compatibility
        with QTextDocument parser.
        """
        safe_val = min(max(value, 0), 100)
        remaining = 100 - safe_val
        
        return f"""
        <table width="32%" cellpadding="10" cellspacing="0" style="border: 1px solid #cbd5e1" bgcolor="#f8fafc" align="left" hspace="5">
            <tr>
                <td align="center">
                    <font color="#1e3a8a" size="4"><b>{title}</b></font><br>
                    <font color="{color}" size="6"><b>{safe_val:.1f}%</b></font><br><br>
                    <table width="100%" cellpadding="0" cellspacing="0">
                        <tr>
                            <td width="{safe_val}%" bgcolor="{color}" height="10"></td>
                            <td width="{remaining}%" bgcolor="#e2e8f0" height="10"></td>
                        </tr>
                    </table>
                </td>
            </tr>
        </table>
        """

    def _build_bullet_list(self, items: List[str], bullet_color: str = "#2563eb") -> str:
        """Render bullet-style content using simple HTML supported by QTextDocument."""
        rows = []
        for item in items:
            rows.append(
                f"""
                <tr>
                    <td width="4%" valign="top"><font color="{bullet_color}" size="3"><b>&#8226;</b></font></td>
                    <td width="96%"><font color="#475569" size="3">{item}</font></td>
                </tr>
                """
            )
        return f'<table width="100%" cellpadding="3" cellspacing="0">{"".join(rows)}</table>'

    def _generate_html_content(self, metrics: Dict, anomalies: List[Dict],
                              suggestions: List[Dict], daily_summary: Optional[Dict],
                              include_processes: bool,
                              graph_data: Optional[Dict],
                              alerts: Optional[List[Dict]]) -> str:

        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        health_score = metrics.get('health_score', 0)
        health_status = metrics.get('health_status', 'Unknown')

        cpu = metrics.get('cpu', {}).get('usage', 0)
        cores = metrics.get('cpu', {}).get('cores', 0)
        mem = metrics.get('memory', {}).get('usage', 0)
        disk = metrics.get('disk', {}).get('usage', 0)
        procs = metrics.get('processes', {}).get('count', 0)

        mem_info = metrics.get('memory', {}).get('info', {})
        used_mb = mem_info.get('used_mb', 0) if mem_info else 0
        tot_mb = mem_info.get('total_mb', 0) if mem_info else 0

        h_color = '#10b981' if health_score >= 80 else '#f59e0b' if health_score >= 50 else '#ef4444'
        overview = PROJECT_OVERVIEW

        html = f"""
        <html>
        <body style="font-family: Arial, sans-serif;">
            <!-- Header -->
            <table width="100%" cellpadding="20" cellspacing="0" bgcolor="#1e40af">
                <tr>
                    <td align="center">
                        <font color="#ffffff" size="6"><b>Executive System Health Report</b></font><br>
                        <font color="#bfdbfe" size="3">System Snapshot Generated: {timestamp}</font>
                    </td>
                </tr>
            </table>
            <br><br>

            <!-- Project Overview -->
            <font color="#1e3a8a" size="5"><b>About The Project</b></font>
            <hr color="#e5e7eb" size="1">
            <table width="100%" cellpadding="12" cellspacing="0" style="border: 1px solid #cbd5e1;" bgcolor="#f8fafc">
                <tr>
                    <td>
                        <font color="#0f172a" size="5"><b>{overview['title']}</b></font><br><br>
                        <font color="#475569" size="3">{overview['description']}</font>
                    </td>
                </tr>
            </table>
            <br>

            <table width="100%" cellpadding="10" cellspacing="8">
                <tr>
                    <td width="50%" valign="top" style="border: 1px solid #cbd5e1;" bgcolor="#ffffff">
                        <font color="#1e3a8a" size="4"><b>Purpose</b></font><br><br>
                        {self._build_bullet_list(overview['purpose'])}
                    </td>
                    <td width="50%" valign="top" style="border: 1px solid #cbd5e1;" bgcolor="#ffffff">
                        <font color="#1e3a8a" size="4"><b>Problems Solved</b></font><br><br>
                        {self._build_bullet_list(overview['problems_solved'])}
                    </td>
                </tr>
                <tr>
                    <td width="50%" valign="top" style="border: 1px solid #cbd5e1;" bgcolor="#ffffff">
                        <font color="#1e3a8a" size="4"><b>Key Features</b></font><br><br>
                        {self._build_bullet_list(overview['key_features'])}
                    </td>
                    <td width="50%" valign="top" style="border: 1px solid #cbd5e1;" bgcolor="#ffffff">
                        <font color="#1e3a8a" size="4"><b>Core Modules</b></font><br><br>
                        {self._build_bullet_list(overview['modules'])}
                    </td>
                </tr>
            </table>
            <br>

            <table width="100%" cellpadding="10" cellspacing="8">
                <tr>
                    <td width="50%" valign="top" style="border: 1px solid #cbd5e1;" bgcolor="#ffffff">
                        <font color="#1e3a8a" size="4"><b>How The System Works</b></font><br><br>
                        {self._build_bullet_list(overview['workflow'])}
                    </td>
                    <td width="50%" valign="top" style="border: 1px solid #cbd5e1;" bgcolor="#ffffff">
                        <font color="#1e3a8a" size="4"><b>Technologies Used</b></font><br><br>
                        {self._build_bullet_list(overview['technologies'])}
                    </td>
                </tr>
            </table>
            <br>

            <table width="100%" cellpadding="12" cellspacing="0" style="border: 1px solid #cbd5e1;" bgcolor="#ffffff">
                <tr bgcolor="#eff6ff">
                    <td>
                        <font color="#1e3a8a" size="4"><b>Simple Architecture</b></font><br><br>
                        <font color="#475569" size="3">{' &rarr; '.join(overview['architecture'])}</font>
                    </td>
                </tr>
            </table>
            <br><br>

            <!-- 4 Metric Cards -->
            <table width="100%" cellpadding="15" cellspacing="5">
                <tr>
                    <td width="25%" bgcolor="#f8fafc" align="center" style="border: 1px solid #cbd5e1;">
                        <font color="#64748b" size="3"><b>SYSTEM HEALTH</b></font><br><br>
                        <font color="{h_color}" size="7"><b>{health_score:.0f}</b></font><font color="{h_color}" size="4">/100</font><br><br>
                        <font color="#94a3b8" size="2">Status: {health_status}</font>
                    </td>
                    <td width="25%" bgcolor="#f8fafc" align="center" style="border: 1px solid #cbd5e1;">
                        <font color="#64748b" size="3"><b>CPU USAGE</b></font><br><br>
                        <font color="#0f172a" size="7"><b>{cpu:.1f}%</b></font><br><br>
                        <font color="#94a3b8" size="2">{cores} Logical Cores</font>
                    </td>
                    <td width="25%" bgcolor="#f8fafc" align="center" style="border: 1px solid #cbd5e1;">
                        <font color="#64748b" size="3"><b>MEMORY USAGE</b></font><br><br>
                        <font color="#0f172a" size="7"><b>{mem:.1f}%</b></font><br><br>
                        <font color="#94a3b8" size="2">{used_mb:.0f} MB / {tot_mb:.0f} MB</font>
                    </td>
                    <td width="25%" bgcolor="#f8fafc" align="center" style="border: 1px solid #cbd5e1;">
                        <font color="#64748b" size="3"><b>DISK & TASKS</b></font><br><br>
                        <font color="#0f172a" size="7"><b>{disk:.1f}%</b></font><br><br>
                        <font color="#94a3b8" size="2">{procs} Active Procs</font>
                    </td>
                </tr>
            </table>
            <br>

            <!-- Horizontal Graphs (Progress Bars) -->
            <font color="#1e3a8a" size="5"><b>System Telemetry Capacity Graphs</b></font>
            <hr color="#e5e7eb" size="1">
            <table width="100%" cellpadding="0" cellspacing="0">
                <tr>
                    <td>
                        {self._build_metric_graph("CPU Load", cpu, "#ef4444")}
                        {self._build_metric_graph("Memory Load", mem, "#3b82f6")}
                        {self._build_metric_graph("System Health", health_score, "#10b981")}
                    </td>
                </tr>
            </table>
            <br><br><br><br><br><br><br>

            <!-- Anomalies -->
            <font color="#1e3a8a" size="5"><b>Diagnostic Events & Anomalies ({len(anomalies)})</b></font>
            <hr color="#e5e7eb" size="1">
        """

        if anomalies:
            html += """
            <table width="100%" cellpadding="10" cellspacing="0" style="border: 1px solid #cbd5e1;">
                <tr bgcolor="#f1f5f9">
                    <td width="20%" style="border-bottom: 2px solid #cbd5e1;"><font color="#334155" size="3"><b>Event Type</b></font></td>
                    <td width="20%" style="border-bottom: 2px solid #cbd5e1;"><font color="#334155" size="3"><b>Severity</b></font></td>
                    <td width="60%" style="border-bottom: 2px solid #cbd5e1;"><font color="#334155" size="3"><b>Details</b></font></td>
                </tr>
            """
            for i, a in enumerate(anomalies):
                bg = "#ffffff" if i % 2 == 0 else "#f8fafc"
                sev = a.get('severity', '')
                scolor = "#dc2626" if sev == 'Critical' else "#d97706" if sev == 'High' else "#059669"
                html += f"""
                <tr bgcolor="{bg}">
                    <td style="border-bottom: 1px solid #e2e8f0;"><font color="#475569" size="3">{a.get('type','')}</font></td>
                    <td style="border-bottom: 1px solid #e2e8f0;"><font color="{scolor}" size="3"><b>{sev}</b></font></td>
                    <td style="border-bottom: 1px solid #e2e8f0;"><font color="#475569" size="3">{a.get('description','')}</font></td>
                </tr>
                """
            html += "</table><br>"
        else:
            html += '<p><font color="#64748b" size="3"><i>System is operating normally. No anomalies detected.</i></font></p><br>'

        # Suggestions
        html += f"""
        <font color="#1e3a8a" size="5"><b>Optimization Suggestions ({len(suggestions)})</b></font>
        <hr color="#e5e7eb" size="1">
        """
        if suggestions:
            html += """
            <table width="100%" cellpadding="10" cellspacing="0" style="border: 1px solid #cbd5e1;">
                <tr bgcolor="#f1f5f9">
                    <td width="20%" style="border-bottom: 2px solid #cbd5e1;"><font color="#334155" size="3"><b>Severity</b></font></td>
                    <td width="30%" style="border-bottom: 2px solid #cbd5e1;"><font color="#334155" size="3"><b>Title</b></font></td>
                    <td width="50%" style="border-bottom: 2px solid #cbd5e1;"><font color="#334155" size="3"><b>Recommendation</b></font></td>
                </tr>
            """
            for i, suggestion in enumerate(suggestions):
                bg = "#ffffff" if i % 2 == 0 else "#f8fafc"
                severity = suggestion.get('severity', 'Low')
                severity_color = "#dc2626" if severity in ('Critical', 'High') else "#d97706" if severity == 'Medium' else "#059669"
                html += f"""
                <tr bgcolor="{bg}">
                    <td style="border-bottom: 1px solid #e2e8f0;"><font color="{severity_color}" size="3"><b>{severity}</b></font></td>
                    <td style="border-bottom: 1px solid #e2e8f0;"><font color="#0f172a" size="3"><b>{suggestion.get('title', 'Untitled suggestion')}</b></font></td>
                    <td style="border-bottom: 1px solid #e2e8f0;"><font color="#475569" size="3">{suggestion.get('description', suggestion.get('action', 'No recommendation provided.'))}</font></td>
                </tr>
                """
            html += "</table><br>"
        else:
            html += '<p><font color="#64748b" size="3"><i>No optimization suggestions were generated for this snapshot.</i></font></p><br>'

        # Alerts (DB)
        if alerts:
            html += f"""
            <font color="#1e3a8a" size="5"><b>Recent Administrative Alerts ({len(alerts)})</b></font>
            <hr color="#e5e7eb" size="1">
            <table width="100%" cellpadding="10" cellspacing="0" style="border: 1px solid #cbd5e1;">
                <tr bgcolor="#f1f5f9">
                    <td width="20%" style="border-bottom: 2px solid #cbd5e1;"><font color="#334155" size="3"><b>Time</b></font></td>
                    <td width="15%" style="border-bottom: 2px solid #cbd5e1;"><font color="#334155" size="3"><b>Severity</b></font></td>
                    <td width="50%" style="border-bottom: 2px solid #cbd5e1;"><font color="#334155" size="3"><b>Message</b></font></td>
                    <td width="15%" style="border-bottom: 2px solid #cbd5e1;"><font color="#334155" size="3"><b>Source</b></font></td>
                </tr>
            """
            for i, alert in enumerate(alerts):
                bg = "#ffffff" if i % 2 == 0 else "#f8fafc"
                sev = alert.get('severity', '')
                scolor = "#dc2626" if sev in ('Critical', 'High') else "#d97706" if sev == 'Medium' else "#059669"
                html += f"""
                <tr bgcolor="{bg}">
                    <td style="border-bottom: 1px solid #e2e8f0;"><font color="#475569" size="3">{alert.get('timestamp','')}</font></td>
                    <td style="border-bottom: 1px solid #e2e8f0;"><font color="{scolor}" size="3"><b>{sev}</b></font></td>
                    <td style="border-bottom: 1px solid #e2e8f0;"><font color="#475569" size="3">{alert.get('message','')}</font></td>
                    <td style="border-bottom: 1px solid #e2e8f0;"><font color="#475569" size="3">{alert.get('source','')}</font></td>
                </tr>
                """
            html += "</table><br>"

        # Processes
        if include_processes:
            top_cpu = metrics.get('processes', {}).get('top_cpu', [])
            html += """
            <font color="#1e3a8a" size="5"><b>Process Telemetry (Top 10)</b></font>
            <hr color="#e5e7eb" size="1">
            """
            if top_cpu:
                html += """
                <table width="100%" cellpadding="8" cellspacing="0" style="border: 1px solid #cbd5e1;">
                    <tr bgcolor="#f1f5f9">
                        <td width="15%" style="border-bottom: 2px solid #cbd5e1;"><font color="#334155" size="3"><b>PID</b></font></td>
                        <td width="45%" style="border-bottom: 2px solid #cbd5e1;"><font color="#334155" size="3"><b>Process Name</b></font></td>
                        <td width="20%" style="border-bottom: 2px solid #cbd5e1;"><font color="#334155" size="3"><b>CPU %</b></font></td>
                        <td width="20%" style="border-bottom: 2px solid #cbd5e1;"><font color="#334155" size="3"><b>Memory %</b></font></td>
                    </tr>
                """
                for i, p in enumerate(top_cpu[:10]):
                    bg = "#ffffff" if i % 2 == 0 else "#f8fafc"
                    html += f"""
                    <tr bgcolor="{bg}">
                        <td style="border-bottom: 1px solid #e2e8f0;"><font color="#475569" size="3">{p.get('pid', '')}</font></td>
                        <td style="border-bottom: 1px solid #e2e8f0;"><font color="#0f172a" size="3"><b>{p.get('name', '')}</b></font></td>
                        <td style="border-bottom: 1px solid #e2e8f0;"><font color="#475569" size="3">{p.get('cpu_percent', 0):.1f}%</font></td>
                        <td style="border-bottom: 1px solid #e2e8f0;"><font color="#475569" size="3">{p.get('memory_percent', 0):.1f}%</font></td>
                    </tr>
                    """
                html += "</table><br>"

        # Daily Summary
        if daily_summary:
            html += """
            <font color="#1e3a8a" size="5"><b>24-Hour Statistical Summary</b></font>
            <hr color="#e5e7eb" size="1">
            <table width="100%" cellpadding="10" cellspacing="0" style="border: 1px solid #cbd5e1;">
                <tr bgcolor="#f1f5f9">
                    <td width="50%" style="border-bottom: 2px solid #cbd5e1;"><font color="#334155" size="3"><b>Metric</b></font></td>
                    <td width="50%" style="border-bottom: 2px solid #cbd5e1;"><font color="#334155" size="3"><b>Measured Value</b></font></td>
                </tr>
            """
            rows = [
                ("Peak CPU Utilization", f"{daily_summary.get('peak_cpu', 0):.1f}%"),
                ("Peak Memory Pressure", f"{daily_summary.get('peak_memory', 0):.1f}%"),
                ("Sustained Average CPU", f"{daily_summary.get('avg_cpu', 0):.1f}%"),
                ("Sustained Average Memory", f"{daily_summary.get('avg_memory', 0):.1f}%"),
                ("Total Alerts Triggered", f"{daily_summary.get('alert_count', 0)}")
            ]
            for i, (key, val) in enumerate(rows):
                bg = "#ffffff" if i % 2 == 0 else "#f8fafc"
                html += f"""
                <tr bgcolor="{bg}">
                    <td style="border-bottom: 1px solid #e2e8f0;"><font color="#475569" size="3">{key}</font></td>
                    <td style="border-bottom: 1px solid #e2e8f0;"><font color="#0f172a" size="3"><b>{val}</b></font></td>
                </tr>
                """
            html += "</table><br>"

        html += f"""
            <font color="#1e3a8a" size="5"><b>Project Assessment</b></font>
            <hr color="#e5e7eb" size="1">
            <table width="100%" cellpadding="10" cellspacing="8">
                <tr>
                    <td width="33%" valign="top" style="border: 1px solid #cbd5e1;" bgcolor="#ffffff">
                        <font color="#1e3a8a" size="4"><b>Advantages</b></font><br><br>
                        {self._build_bullet_list(overview['advantages'])}
                    </td>
                    <td width="33%" valign="top" style="border: 1px solid #cbd5e1;" bgcolor="#ffffff">
                        <font color="#1e3a8a" size="4"><b>Limitations</b></font><br><br>
                        {self._build_bullet_list(overview['limitations'])}
                    </td>
                    <td width="34%" valign="top" style="border: 1px solid #cbd5e1;" bgcolor="#ffffff">
                        <font color="#1e3a8a" size="4"><b>Future Scope</b></font><br><br>
                        {self._build_bullet_list(overview['future_scope'])}
                    </td>
                </tr>
            </table>
            <br>
            <table width="100%" cellpadding="12" cellspacing="0" style="border: 1px solid #cbd5e1;" bgcolor="#f8fafc">
                <tr>
                    <td>
                        <font color="#1e3a8a" size="4"><b>Conclusion</b></font><br><br>
                        <font color="#475569" size="3">{overview['conclusion']}</font>
                    </td>
                </tr>
            </table>
        """

        html += f"""
            <br><br>
            <table width="100%" cellpadding="10" cellspacing="0" bgcolor="#f1f5f9">
                <tr>
                    <td align="center">
                        <font color="#94a3b8" size="2">
                            {config.APP_NAME} v{config.VERSION} &mdash; Report generated on {timestamp}<br>
                            Author: {config.AUTHOR} &bull; BCA Final Year Project 2026
                        </font>
                    </td>
                </tr>
            </table>
        </body>
        </html>
        """
        return html

    def get_reports_directory(self) -> str:
        return self.reports_dir

    def list_reports(self) -> List[Dict]:
        reports = []
        for filename in sorted(os.listdir(self.reports_dir), reverse=True):
            filepath = os.path.join(self.reports_dir, filename)
            if os.path.isfile(filepath):
                file_size = os.path.getsize(filepath)
                file_time = datetime.fromtimestamp(os.path.getmtime(filepath))
                reports.append({
                    'filename': filename,
                    'path': filepath,
                    'size_bytes': file_size,
                    'created': file_time,
                    'format': 'PDF' if filename.endswith('.pdf') else ('CSV' if filename.endswith('.csv') else 'TXT')
                })
        return reports

    def delete_old_reports(self, days: int = 7) -> int:
        from datetime import timedelta
        cutoff_date = datetime.now() - timedelta(days=days)
        deleted_count = 0
        for filename in os.listdir(self.reports_dir):
            filepath = os.path.join(self.reports_dir, filename)
            if os.path.isfile(filepath):
                file_time = datetime.fromtimestamp(os.path.getmtime(filepath))
                if file_time < cutoff_date:
                    os.remove(filepath)
                    deleted_count += 1
        return deleted_count

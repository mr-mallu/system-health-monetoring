"""
Report Generator Module
Generates comprehensive system diagnostic reports in TXT and CSV formats.
Includes system metrics, health score, anomalies, and suggestions.
"""

import os
from datetime import datetime
from typing import List, Dict, Optional
import csv


class ReportGenerator:
    """
    Generates comprehensive system diagnostic reports.
    Supports TXT and CSV output formats.
    """

    def __init__(self, reports_dir: str = None):
        """
        Initialize the report generator.

        Args:
            reports_dir: Directory to save reports (defaults to data/reports)
        """
        if reports_dir is None:
            base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            reports_dir = os.path.join(base_dir, 'data', 'reports')

        self.reports_dir = reports_dir
        os.makedirs(reports_dir, exist_ok=True)

    def generate_report(self, metrics: Dict, anomalies: List[Dict],
                       suggestions: List[Dict], daily_summary: Optional[Dict] = None,
                       include_processes: bool = False) -> Dict:
        """
        Generate a comprehensive system report.

        Args:
            metrics: Current system metrics
            anomalies: List of detected anomalies
            suggestions: List of suggestions
            daily_summary: Optional daily summary statistics
            include_processes: Whether to include detailed process list

        Returns:
            Dictionary with report paths and metadata
        """
        timestamp = datetime.now()
        report_filename = f"system_report_{timestamp.strftime('%Y%m%d_%H%M%S')}"

        # Generate TXT report
        txt_path = self._generate_txt_report(
            report_filename, metrics, anomalies, suggestions, daily_summary, include_processes
        )

        # Generate CSV report
        csv_path = self._generate_csv_report(report_filename, metrics)

        return {
            'txt_path': txt_path,
            'csv_path': csv_path,
            'timestamp': timestamp,
            'filename_base': report_filename,
            'metrics_snapshot': metrics
        }

    def _generate_txt_report(self, filename: str, metrics: Dict, anomalies: List[Dict],
                            suggestions: List[Dict], daily_summary: Optional[Dict],
                            include_processes: bool) -> str:
        """
        Generate a text report.

        Args:
            filename: Base filename for the report
            metrics: System metrics
            anomalies: Detected anomalies
            suggestions: System suggestions
            daily_summary: Daily statistics
            include_processes: Include process details

        Returns:
            Path to generated report
        """
        report_path = os.path.join(self.reports_dir, f"{filename}.txt")

        with open(report_path, 'w', encoding='utf-8') as f:
            # Header
            f.write("=" * 70 + "\n")
            f.write("SYSTEM HEALTH MONITORING - DIAGNOSTIC REPORT\n")
            f.write("=" * 70 + "\n\n")

            # Timestamp
            timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            f.write(f"Report Generated: {timestamp}\n\n")

            # SECTION 1: System Metrics
            f.write("1. SYSTEM METRICS\n")
            f.write("-" * 70 + "\n")
            self._write_metrics_section(f, metrics)
            f.write("\n")

            # SECTION 2: Health Score
            f.write("2. SYSTEM HEALTH\n")
            f.write("-" * 70 + "\n")
            health_score = metrics.get('health_score', 0)
            health_status = metrics.get('health_status', 'Unknown')
            f.write(f"Health Score: {health_score:.1f}/100\n")
            f.write(f"Health Status: {health_status}\n\n")

            # SECTION 3: Anomalies
            f.write("3. DETECTED ANOMALIES\n")
            f.write("-" * 70 + "\n")
            self._write_anomalies_section(f, anomalies)
            f.write("\n")

            # SECTION 4: Suggestions
            f.write("4. SYSTEM SUGGESTIONS\n")
            f.write("-" * 70 + "\n")
            self._write_suggestions_section(f, suggestions)
            f.write("\n")

            # SECTION 5: Daily Summary (if provided)
            if daily_summary:
                f.write("5. DAILY STATISTICS\n")
                f.write("-" * 70 + "\n")
                self._write_daily_summary_section(f, daily_summary)
                f.write("\n")

            # SECTION 6: Process Information (if requested)
            if include_processes:
                f.write("6. TOP PROCESSES\n")
                f.write("-" * 70 + "\n")
                self._write_processes_section(f, metrics)
                f.write("\n")

            # Footer
            f.write("=" * 70 + "\n")
            f.write("End of Report\n")
            f.write("=" * 70 + "\n")

        return report_path

    def _write_metrics_section(self, f, metrics: Dict):
        """Write metrics section to report."""
        cpu_usage = metrics.get('cpu', {}).get('usage', 0)
        cpu_cores = metrics.get('cpu', {}).get('cores', 0)
        cpu_avg = metrics.get('cpu', {}).get('average', 0)

        memory_usage = metrics.get('memory', {}).get('usage', 0)
        memory_info = metrics.get('memory', {}).get('info', {})
        disk_usage = metrics.get('disk', {}).get('usage', 0)

        f.write(f"CPU Usage:        {cpu_usage:.1f}%\n")
        f.write(f"CPU Cores:        {cpu_cores}\n")
        f.write(f"CPU Average:      {cpu_avg:.1f}%\n")
        f.write(f"\nMemory Usage:     {memory_usage:.1f}%\n")

        if memory_info:
            used_mb = memory_info.get('used_mb', 0)
            total_mb = memory_info.get('total_mb', 0)
            f.write(f"Memory (Used/Total): {used_mb:.0f} MB / {total_mb:.0f} MB\n")

        f.write(f"\nDisk Usage:       {disk_usage:.1f}%\n")

        process_count = metrics.get('processes', {}).get('count', 0)
        f.write(f"Running Processes: {process_count}\n")

    def _write_anomalies_section(self, f, anomalies: List[Dict]):
        """Write anomalies section to report."""
        if not anomalies:
            f.write("No anomalies detected.\n")
            return

        f.write(f"Total Anomalies: {len(anomalies)}\n\n")

        for idx, anomaly in enumerate(anomalies, 1):
            f.write(f"Anomaly #{idx}:\n")
            f.write(f"  Type:        {anomaly.get('type', 'Unknown')}\n")
            f.write(f"  Severity:    {anomaly.get('severity', 'Unknown')}\n")
            f.write(f"  Description: {anomaly.get('description', 'N/A')}\n")
            f.write("\n")

    def _write_suggestions_section(self, f, suggestions: List[Dict]):
        """Write suggestions section to report."""
        if not suggestions:
            f.write("No suggestions at this time.\n")
            return

        f.write(f"Total Suggestions: {len(suggestions)}\n\n")

        # Group by severity
        critical = [s for s in suggestions if s.get('severity') == 'Critical']
        high = [s for s in suggestions if s.get('severity') == 'High']
        medium = [s for s in suggestions if s.get('severity') == 'Medium']
        low = [s for s in suggestions if s.get('severity') == 'Low']

        self._write_suggestion_group(f, critical, "Critical")
        self._write_suggestion_group(f, high, "High")
        self._write_suggestion_group(f, medium, "Medium")
        self._write_suggestion_group(f, low, "Low")

    def _write_suggestion_group(self, f, suggestions: List[Dict], severity: str):
        """Write a group of suggestions with same severity."""
        if not suggestions:
            return

        f.write(f"\n{severity} Priority:\n")
        for idx, suggestion in enumerate(suggestions, 1):
            f.write(f"  {idx}. {suggestion.get('title', 'N/A')}\n")
            f.write(f"     {suggestion.get('message', 'N/A')}\n")

    def _write_daily_summary_section(self, f, daily_summary: Dict):
        """Write daily summary section to report."""
        f.write(f"Peak CPU Usage:    {daily_summary.get('peak_cpu', 0):.1f}%\n")
        f.write(f"Peak Memory Usage: {daily_summary.get('peak_memory', 0):.1f}%\n")
        f.write(f"Average CPU:       {daily_summary.get('avg_cpu', 0):.1f}%\n")
        f.write(f"Average Memory:    {daily_summary.get('avg_memory', 0):.1f}%\n")
        f.write(f"Alert Count:       {daily_summary.get('alert_count', 0)}\n")
        f.write(f"Avg Health Score:  {daily_summary.get('avg_health_score', 0):.1f}\n")

    def _write_processes_section(self, f, metrics: Dict):
        """Write processes section to report."""
        top_cpu = metrics.get('processes', {}).get('top_cpu', [])
        top_memory = metrics.get('processes', {}).get('top_memory', [])

        f.write("Top CPU Processes:\n")
        if top_cpu:
            for idx, process in enumerate(top_cpu, 1):
                f.write(f"  {idx}. {process.get('name', 'Unknown')} - "
                       f"{process.get('cpu_percent', 0):.1f}% CPU (PID: {process.get('pid', 'N/A')})\n")
        else:
            f.write("  No data available\n")

        f.write("\nTop Memory Processes:\n")
        if top_memory:
            for idx, process in enumerate(top_memory, 1):
                f.write(f"  {idx}. {process.get('name', 'Unknown')} - "
                       f"{process.get('memory_mb', 0):.0f} MB ({process.get('memory_percent', 0):.1f}%)\n")
        else:
            f.write("  No data available\n")

    def _generate_csv_report(self, filename: str, metrics: Dict) -> str:
        """
        Generate a CSV report with metrics data.

        Args:
            filename: Base filename for the report
            metrics: System metrics

        Returns:
            Path to generated CSV report
        """
        report_path = os.path.join(self.reports_dir, f"{filename}.csv")

        with open(report_path, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)

            # Header row
            writer.writerow(['Metric', 'Value', 'Unit'])

            # Write metrics
            writer.writerow(['CPU Usage', f"{metrics.get('cpu', {}).get('usage', 0):.1f}", '%'])
            writer.writerow(['CPU Cores', metrics.get('cpu', {}).get('cores', 0), 'cores'])
            writer.writerow(['CPU Average', f"{metrics.get('cpu', {}).get('average', 0):.1f}", '%'])

            writer.writerow(['Memory Usage', f"{metrics.get('memory', {}).get('usage', 0):.1f}", '%'])

            memory_info = metrics.get('memory', {}).get('info', {})
            if memory_info:
                writer.writerow(['Memory Used', f"{memory_info.get('used_mb', 0):.0f}", 'MB'])
                writer.writerow(['Memory Total', f"{memory_info.get('total_mb', 0):.0f}", 'MB'])

            writer.writerow(['Disk Usage', f"{metrics.get('disk', {}).get('usage', 0):.1f}", '%'])

            writer.writerow(['Process Count', metrics.get('processes', {}).get('count', 0), 'processes'])

            writer.writerow(['Health Score', f"{metrics.get('health_score', 0):.1f}", '/100'])
            writer.writerow(['Health Status', metrics.get('health_status', 'Unknown'), 'status'])
            writer.writerow(['Timestamp', datetime.now().strftime('%Y-%m-%d %H:%M:%S'), 'datetime'])

        return report_path

    def get_reports_directory(self) -> str:
        """Get the reports directory path."""
        return self.reports_dir

    def list_reports(self) -> List[Dict]:
        """
        List all generated reports.

        Returns:
            List of report metadata dictionaries
        """
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
                    'format': 'CSV' if filename.endswith('.csv') else 'TXT'
                })

        return reports

    def delete_old_reports(self, days: int = 7) -> int:
        """
        Delete reports older than specified days.

        Args:
            days: Number of days to keep

        Returns:
            Number of reports deleted
        """
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

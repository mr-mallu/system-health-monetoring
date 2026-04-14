"""
Daily Summary Module
Calculates daily system statistics from database records.
Provides peak usage, average values, alert counts, and health trends.
"""

from typing import Dict, Optional, List
from datetime import datetime, timedelta
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.database import get_database


class DailySummary:
    """
    Calculates daily system summary statistics.
    Uses database records to compute peak, average, and trend metrics.
    """

    def __init__(self):
        """Initialize the daily summary calculator."""
        self.db = get_database()

    def calculate_daily_stats(self, date: Optional[datetime] = None) -> Dict:
        """
        Calculate all daily statistics.

        Args:
            date: Date to calculate stats for (defaults to today)

        Returns:
            Dictionary with daily statistics
        """
        if date is None:
            date = datetime.now()

        # Get start and end of day
        start_of_day = datetime(date.year, date.month, date.day, 0, 0, 0)
        end_of_day = datetime(date.year, date.month, date.day, 23, 59, 59)

        stats = {
            'date': date.date().isoformat(),
            'peak_cpu': self._get_peak_cpu(start_of_day, end_of_day),
            'peak_memory': self._get_peak_memory(start_of_day, end_of_day),
            'avg_cpu': self._get_average_cpu(start_of_day, end_of_day),
            'avg_memory': self._get_average_memory(start_of_day, end_of_day),
            'peak_disk': self._get_peak_disk(start_of_day, end_of_day),
            'avg_disk': self._get_average_disk(start_of_day, end_of_day),
            'alert_count': self._get_alert_count(start_of_day, end_of_day),
            'alert_count_by_severity': self._get_alert_count_by_severity(start_of_day, end_of_day),
            'avg_health_score': self._calculate_average_health_score(start_of_day, end_of_day),
            'uptime_hours': 24,
            'metrics_collected': self._get_metrics_count(start_of_day, end_of_day)
        }

        return stats

    def _get_peak_cpu(self, start_time: datetime, end_time: datetime) -> float:
        """Get peak CPU usage for the day."""
        cursor = self.db.conn.cursor()
        cursor.execute("""
            SELECT MAX(cpu_usage) as peak
            FROM system_metrics
            WHERE datetime(timestamp) >= datetime(?) AND datetime(timestamp) <= datetime(?)
        """, (start_time.isoformat(), end_time.isoformat()))

        result = cursor.fetchone()
        return result['peak'] if result and result['peak'] is not None else 0.0

    def _get_peak_memory(self, start_time: datetime, end_time: datetime) -> float:
        """Get peak memory usage for the day."""
        cursor = self.db.conn.cursor()
        cursor.execute("""
            SELECT MAX(memory_usage) as peak
            FROM system_metrics
            WHERE datetime(timestamp) >= datetime(?) AND datetime(timestamp) <= datetime(?)
        """, (start_time.isoformat(), end_time.isoformat()))

        result = cursor.fetchone()
        return result['peak'] if result and result['peak'] is not None else 0.0

    def _get_peak_disk(self, start_time: datetime, end_time: datetime) -> float:
        """Get peak disk usage for the day."""
        cursor = self.db.conn.cursor()
        cursor.execute("""
            SELECT MAX(disk_usage) as peak
            FROM system_metrics
            WHERE datetime(timestamp) >= datetime(?) AND datetime(timestamp) <= datetime(?)
        """, (start_time.isoformat(), end_time.isoformat()))

        result = cursor.fetchone()
        return result['peak'] if result and result['peak'] is not None else 0.0

    def _get_average_cpu(self, start_time: datetime, end_time: datetime) -> float:
        """Get average CPU usage for the day."""
        cursor = self.db.conn.cursor()
        cursor.execute("""
            SELECT AVG(cpu_usage) as avg
            FROM system_metrics
            WHERE datetime(timestamp) >= datetime(?) AND datetime(timestamp) <= datetime(?)
        """, (start_time.isoformat(), end_time.isoformat()))

        result = cursor.fetchone()
        return result['avg'] if result and result['avg'] is not None else 0.0

    def _get_average_memory(self, start_time: datetime, end_time: datetime) -> float:
        """Get average memory usage for the day."""
        cursor = self.db.conn.cursor()
        cursor.execute("""
            SELECT AVG(memory_usage) as avg
            FROM system_metrics
            WHERE datetime(timestamp) >= datetime(?) AND datetime(timestamp) <= datetime(?)
        """, (start_time.isoformat(), end_time.isoformat()))

        result = cursor.fetchone()
        return result['avg'] if result and result['avg'] is not None else 0.0

    def _get_average_disk(self, start_time: datetime, end_time: datetime) -> float:
        """Get average disk usage for the day."""
        cursor = self.db.conn.cursor()
        cursor.execute("""
            SELECT AVG(disk_usage) as avg
            FROM system_metrics
            WHERE datetime(timestamp) >= datetime(?) AND datetime(timestamp) <= datetime(?)
        """, (start_time.isoformat(), end_time.isoformat()))

        result = cursor.fetchone()
        return result['avg'] if result and result['avg'] is not None else 0.0

    def _get_alert_count(self, start_time: datetime, end_time: datetime) -> int:
        """Get total alert count for the day."""
        cursor = self.db.conn.cursor()
        cursor.execute("""
            SELECT COUNT(*) as count
            FROM alerts
            WHERE datetime(timestamp) >= datetime(?) AND datetime(timestamp) <= datetime(?)
        """, (start_time.isoformat(), end_time.isoformat()))

        result = cursor.fetchone()
        return result['count'] if result is not None else 0

    def _get_alert_count_by_severity(self, start_time: datetime, end_time: datetime) -> Dict:
        """Get alert counts grouped by severity."""
        cursor = self.db.conn.cursor()
        cursor.execute("""
            SELECT severity, COUNT(*) as count
            FROM alerts
            WHERE datetime(timestamp) >= datetime(?) AND datetime(timestamp) <= datetime(?)
            GROUP BY severity
        """, (start_time.isoformat(), end_time.isoformat()))

        result = {'Low': 0, 'Medium': 0, 'High': 0, 'Critical': 0}
        for row in cursor.fetchall():
            severity = row['severity']
            if severity in result:
                result[severity] = row['count']

        return result

    def _get_metrics_count(self, start_time: datetime, end_time: datetime) -> int:
        """Get number of metrics records collected."""
        cursor = self.db.conn.cursor()
        cursor.execute("""
            SELECT COUNT(*) as count
            FROM system_metrics
            WHERE datetime(timestamp) >= datetime(?) AND datetime(timestamp) <= datetime(?)
        """, (start_time.isoformat(), end_time.isoformat()))

        result = cursor.fetchone()
        return result['count'] if result is not None else 0

    def _calculate_average_health_score(self, start_time: datetime, end_time: datetime) -> float:
        """
        Calculate average health score.
        This is a synthetic calculation based on CPU, memory, and process count.
        """
        avg_cpu = self._get_average_cpu(start_time, end_time)
        avg_memory = self._get_average_memory(start_time, end_time)

        # Simple health score calculation
        # 100 = excellent, lower is worse
        cpu_score = max(0, 100 - avg_cpu * 0.6)
        memory_score = max(0, 100 - avg_memory * 0.6)
        health_score = (cpu_score + memory_score) / 2

        return round(health_score, 1)

    def get_weekly_summary(self) -> List[Dict]:
        """
        Get daily summaries for the past 7 days.

        Returns:
            List of daily summary dictionaries
        """
        summaries = []

        for i in range(6, -1, -1):  # Last 7 days
            date = datetime.now() - timedelta(days=i)
            summary = self.calculate_daily_stats(date)
            summaries.append(summary)

        return summaries

    def get_monthly_summary(self) -> Dict:
        """
        Get current month summary.

        Returns:
            Dictionary with monthly statistics
        """
        now = datetime.now()
        start_of_month = datetime(now.year, now.month, 1)

        # Calculate end of month
        if now.month == 12:
            end_of_month = datetime(now.year + 1, 1, 1) - timedelta(seconds=1)
        else:
            end_of_month = datetime(now.year, now.month + 1, 1) - timedelta(seconds=1)

        return {
            'month': now.strftime('%B %Y'),
            'peak_cpu': self._get_peak_cpu(start_of_month, end_of_month),
            'peak_memory': self._get_peak_memory(start_of_month, end_of_month),
            'avg_cpu': self._get_average_cpu(start_of_month, end_of_month),
            'avg_memory': self._get_average_memory(start_of_month, end_of_month),
            'total_alerts': self._get_alert_count(start_of_month, end_of_month),
            'alert_severity_breakdown': self._get_alert_count_by_severity(start_of_month, end_of_month),
            'avg_health_score': self._calculate_average_health_score(start_of_month, end_of_month),
            'days_with_data': len([d for d in self.get_weekly_summary() if d['metrics_collected'] > 0])
        }

    def format_summary_for_display(self, stats: Dict) -> str:
        """
        Format summary statistics for display.

        Args:
            stats: Summary statistics dictionary

        Returns:
            Formatted string representation
        """
        lines = []
        lines.append(f"Date: {stats['date']}")
        lines.append("")
        lines.append("Peak Performance:")
        lines.append(f"  CPU Peak:      {stats['peak_cpu']:.1f}%")
        lines.append(f"  Memory Peak:   {stats['peak_memory']:.1f}%")
        lines.append(f"  Disk Peak:     {stats['peak_disk']:.1f}%")
        lines.append("")
        lines.append("Average Performance:")
        lines.append(f"  CPU Average:   {stats['avg_cpu']:.1f}%")
        lines.append(f"  Memory Average: {stats['avg_memory']:.1f}%")
        lines.append(f"  Disk Average:  {stats['avg_disk']:.1f}%")
        lines.append("")
        lines.append("System Events:")
        lines.append(f"  Total Alerts:  {stats['alert_count']}")
        lines.append(f"  Critical:      {stats['alert_count_by_severity']['Critical']}")
        lines.append(f"  High:          {stats['alert_count_by_severity']['High']}")
        lines.append(f"  Medium:        {stats['alert_count_by_severity']['Medium']}")
        lines.append(f"  Low:           {stats['alert_count_by_severity']['Low']}")
        lines.append("")
        lines.append(f"Average Health Score: {stats['avg_health_score']:.1f}/100")
        lines.append(f"Metrics Collected: {stats['metrics_collected']}")

        return "\n".join(lines)

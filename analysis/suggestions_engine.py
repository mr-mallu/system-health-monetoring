"""
Smart Suggestions Engine Module
Generates proactive system maintenance suggestions based on current metrics and historical data.
Provides context-aware recommendations for optimizing system performance.
"""

from typing import List, Dict, Optional
from datetime import datetime, timedelta
import psutil


class SuggestionsEngine:
    """
    Intelligent suggestion generator based on system metrics.
    Detects patterns and provides actionable recommendations.
    """

    def __init__(self):
        """Initialize the suggestions engine."""
        self.suggestion_cooldown = {}  # Track last suggestion timestamp per type
        self.cooldown_minutes = 30  # Don't repeat same suggestion for 30 minutes

    def generate_suggestions(self, metrics: Dict, process_list: List[Dict],
                            historical_data: Optional[Dict] = None) -> List[Dict]:
        """
        Generate smart suggestions based on current system state.

        Args:
            metrics: Current system metrics dictionary
            process_list: List of running processes
            historical_data: Optional historical data for trends

        Returns:
            List of suggestion dictionaries
        """
        suggestions = []

        # Get metric values
        cpu_usage = metrics.get('cpu', {}).get('usage', 0)
        memory_usage = metrics.get('memory', {}).get('usage', 0)
        disk_usage = metrics.get('disk', {}).get('usage', 0)
        process_count = metrics.get('processes', {}).get('count', 0)

        # Generate suggestions based on current state
        suggestions.extend(self._suggest_for_cpu(cpu_usage, process_list))
        suggestions.extend(self._suggest_for_memory(memory_usage, process_list))
        suggestions.extend(self._suggest_for_disk(disk_usage))
        suggestions.extend(self._suggest_for_processes(process_count, process_list))

        if historical_data:
            suggestions.extend(self._suggest_from_trends(historical_data))

        # Filter by cooldown to avoid repetitive suggestions
        suggestions = self._apply_cooldown_filter(suggestions)

        return suggestions

    def _suggest_for_cpu(self, cpu_usage: float, process_list: List[Dict]) -> List[Dict]:
        """
        Generate CPU-related suggestions.

        Args:
            cpu_usage: Current CPU usage percentage
            process_list: List of running processes

        Returns:
            List of CPU suggestions
        """
        suggestions = []

        if cpu_usage > 80:
            suggestions.append({
                'type': 'CPU_HIGH',
                'severity': 'High',
                'title': 'High CPU Usage Detected',
                'message': f'CPU usage is at {cpu_usage:.1f}%. Consider closing unnecessary applications.',
                'action': 'review_processes',
                'timestamp': datetime.now()
            })

        elif cpu_usage > 60 and cpu_usage <= 80:
            suggestions.append({
                'type': 'CPU_MODERATE',
                'severity': 'Medium',
                'title': 'Moderate CPU Usage',
                'message': f'CPU is running at {cpu_usage:.1f}%. Monitor performance and close heavy applications if needed.',
                'action': 'monitor',
                'timestamp': datetime.now()
            })

        # Check for heavy processes
        if process_list:
            heavy_processes = [p for p in process_list if p.get('cpu_percent', 0) > 20]
            if heavy_processes:
                top_process = heavy_processes[0]
                if cpu_usage > 70:
                    suggestions.append({
                        'type': 'HEAVY_CPU_PROCESS',
                        'severity': 'High',
                        'title': f'Heavy CPU Process: {top_process.get("name", "Unknown")}',
                        'message': f'{top_process.get("name", "Unknown")} is consuming {top_process.get("cpu_percent", 0):.1f}% CPU. Consider closing it.',
                        'action': 'close_process',
                        'pid': top_process.get('pid'),
                        'process_name': top_process.get('name'),
                        'timestamp': datetime.now()
                    })

        return suggestions

    def _suggest_for_memory(self, memory_usage: float, process_list: List[Dict]) -> List[Dict]:
        """
        Generate memory-related suggestions.

        Args:
            memory_usage: Current memory usage percentage
            process_list: List of running processes

        Returns:
            List of memory suggestions
        """
        suggestions = []

        if memory_usage > 85:
            suggestions.append({
                'type': 'MEMORY_CRITICAL',
                'severity': 'Critical',
                'title': 'Critical Memory Usage',
                'message': f'Memory usage is at {memory_usage:.1f}%. Close applications or restart your system.',
                'action': 'urgent_review',
                'timestamp': datetime.now()
            })

        elif memory_usage > 75:
            suggestions.append({
                'type': 'MEMORY_HIGH',
                'severity': 'High',
                'title': 'High Memory Usage',
                'message': f'Memory is running at {memory_usage:.1f}%. Consider closing unused applications.',
                'action': 'review_processes',
                'timestamp': datetime.now()
            })

        elif memory_usage > 60 and memory_usage <= 75:
            suggestions.append({
                'type': 'MEMORY_MODERATE',
                'severity': 'Medium',
                'title': 'Moderate Memory Usage',
                'message': f'Memory usage is at {memory_usage:.1f}%. Monitor to prevent slowdown.',
                'action': 'monitor',
                'timestamp': datetime.now()
            })

        # Check for memory leaks or heavy processes
        if process_list:
            memory_heavy = sorted(
                process_list,
                key=lambda p: p.get('memory_percent', 0),
                reverse=True
            )[:3]

            for process in memory_heavy:
                if process.get('memory_percent', 0) > 15:
                    suggestions.append({
                        'type': 'HEAVY_MEMORY_PROCESS',
                        'severity': 'Medium',
                        'title': f'High Memory Process: {process.get("name", "Unknown")}',
                        'message': f'{process.get("name", "Unknown")} is using {process.get("memory_mb", 0):.0f} MB ({process.get("memory_percent", 0):.1f}%).',
                        'action': 'close_process',
                        'pid': process.get('pid'),
                        'process_name': process.get('name'),
                        'timestamp': datetime.now()
                    })

        return suggestions

    def _suggest_for_disk(self, disk_usage: float) -> List[Dict]:
        """
        Generate disk-related suggestions.

        Args:
            disk_usage: Current disk usage percentage

        Returns:
            List of disk suggestions
        """
        suggestions = []

        if disk_usage > 95:
            suggestions.append({
                'type': 'DISK_CRITICAL',
                'severity': 'Critical',
                'title': 'Critical Disk Space',
                'message': 'Disk is almost full (>95%). Delete unnecessary files immediately.',
                'action': 'cleanup_disk',
                'timestamp': datetime.now()
            })

        elif disk_usage > 90:
            suggestions.append({
                'type': 'DISK_WARNING',
                'severity': 'High',
                'title': 'Low Disk Space',
                'message': f'Disk usage is at {disk_usage:.1f}%. Clean up temporary files and old downloads.',
                'action': 'cleanup_disk',
                'timestamp': datetime.now()
            })

        elif disk_usage > 80:
            suggestions.append({
                'type': 'DISK_WATCH',
                'severity': 'Medium',
                'title': 'Disk Space Monitor',
                'message': f'Disk usage is at {disk_usage:.1f}%. Consider cleaning up old files.',
                'action': 'monitor',
                'timestamp': datetime.now()
            })

        return suggestions

    def _suggest_for_processes(self, process_count: int, process_list: List[Dict]) -> List[Dict]:
        """
        Generate process-related suggestions.

        Args:
            process_count: Total number of running processes
            process_list: List of running processes

        Returns:
            List of process suggestions
        """
        suggestions = []

        if process_count > 250:
            suggestions.append({
                'type': 'TOO_MANY_PROCESSES',
                'severity': 'Medium',
                'title': 'Too Many Processes Running',
                'message': f'You have {process_count} processes running. Consider closing unnecessary applications.',
                'action': 'review_processes',
                'timestamp': datetime.now()
            })

        # Check for browser processes
        browser_processes = [p for p in process_list
                            if any(x in (p.get('name') or '').lower() for x in
                                   ['chrome', 'firefox', 'edge', 'brave', 'safari'])]

        if len(browser_processes) > 5:
            total_memory = sum(p.get('memory_mb', 0) for p in browser_processes)
            suggestions.append({
                'type': 'MANY_BROWSER_TABS',
                'severity': 'Medium',
                'title': 'Many Browser Instances',
                'message': f'Multiple browser processes ({len(browser_processes)}) using {total_memory:.0f} MB. Consider closing unused tabs.',
                'action': 'browser_cleanup',
                'timestamp': datetime.now()
            })

        return suggestions

    def _suggest_from_trends(self, historical_data: Dict) -> List[Dict]:
        """
        Generate suggestions based on historical trends.

        Args:
            historical_data: Historical metrics data

        Returns:
            List of trend-based suggestions
        """
        suggestions = []

        # Analyze peak CPU times
        if 'peak_cpu' in historical_data and historical_data['peak_cpu'] > 85:
            suggestions.append({
                'type': 'PEAK_CPU_PATTERN',
                'severity': 'Low',
                'title': 'High CPU Peak Detected',
                'message': f"Peak CPU reached {historical_data['peak_cpu']:.1f}% today. Check for resource-intensive tasks.",
                'action': 'monitor',
                'timestamp': datetime.now()
            })

        return suggestions

    def _apply_cooldown_filter(self, suggestions: List[Dict]) -> List[Dict]:
        """
        Filter suggestions to avoid repeating same type too frequently.

        Args:
            suggestions: List of suggestions

        Returns:
            Filtered suggestions list
        """
        now = datetime.now()
        filtered = []

        for suggestion in suggestions:
            suggestion_type = suggestion.get('type')

            if suggestion_type not in self.suggestion_cooldown:
                filtered.append(suggestion)
                self.suggestion_cooldown[suggestion_type] = now
            else:
                last_time = self.suggestion_cooldown[suggestion_type]
                if now - last_time > timedelta(minutes=self.cooldown_minutes):
                    filtered.append(suggestion)
                    self.suggestion_cooldown[suggestion_type] = now

        return filtered

    def get_suggestion_count_by_severity(self, suggestions: List[Dict]) -> Dict:
        """
        Count suggestions by severity level.

        Args:
            suggestions: List of suggestions

        Returns:
            Dictionary with severity counts
        """
        counts = {'Critical': 0, 'High': 0, 'Medium': 0, 'Low': 0}

        for suggestion in suggestions:
            severity = suggestion.get('severity', 'Low')
            if severity in counts:
                counts[severity] += 1

        return counts

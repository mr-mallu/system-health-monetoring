"""
Performance Analyzer Module
Identifies which processes are primarily responsible for system slowdown.
Provides detailed impact analysis and explanations.
"""

from typing import List, Dict, Optional, Tuple
from collections import defaultdict
import psutil


class PerformanceAnalyzer:
    """
    Analyzes system performance and identifies root causes.
    Ranks processes by their impact on system slowdown.
    """

    def __init__(self):
        """Initialize the performance analyzer."""
        pass

    def analyze_process_impact(self, top_cpu_processes: List[Dict],
                               top_memory_processes: List[Dict],
                               current_cpu: float,
                               current_memory: float) -> Dict:
        """
        Analyze which processes are responsible for system slowdown.

        Args:
            top_cpu_processes: List of top CPU consuming processes
            top_memory_processes: List of top memory consuming processes
            current_cpu: Current overall CPU usage percentage
            current_memory: Current overall memory usage percentage

        Returns:
            Dictionary with impact analysis and explanation
        """
        impact_analysis = {
            'primary_cause': None,
            'cpu_culprit': None,
            'memory_culprit': None,
            'explanation': '',
            'recommendation': '',
            'risk_level': 'Low'
        }

        # Analyze CPU impact
        if current_cpu > 70:  # High CPU usage
            if top_cpu_processes:
                top_process = top_cpu_processes[0]
                cpu_culprit = {
                    'name': top_process.get('name', 'Unknown'),
                    'pid': top_process.get('pid'),
                    'usage': top_process.get('cpu_percent', 0),
                    'impact': self._calculate_cpu_impact(top_process.get('cpu_percent', 0))
                }
                impact_analysis['cpu_culprit'] = cpu_culprit

                if len(top_cpu_processes) > 1:
                    second_process = top_cpu_processes[1]
                    impact_analysis['secondary_cpu'] = {
                        'name': second_process.get('name', 'Unknown'),
                        'usage': second_process.get('cpu_percent', 0)
                    }

        # Analyze memory impact
        if current_memory > 70:  # High memory usage
            if top_memory_processes:
                top_process = top_memory_processes[0]
                memory_culprit = {
                    'name': top_process.get('name', 'Unknown'),
                    'pid': top_process.get('pid'),
                    'memory_mb': top_process.get('memory_mb', 0),
                    'memory_percent': top_process.get('memory_percent', 0),
                    'impact': self._calculate_memory_impact(top_process.get('memory_percent', 0))
                }
                impact_analysis['memory_culprit'] = memory_culprit

        # Determine primary cause
        impact_analysis['primary_cause'] = self._determine_primary_cause(
            impact_analysis['cpu_culprit'],
            current_cpu,
            impact_analysis['memory_culprit'],
            current_memory
        )

        # Generate explanation
        impact_analysis['explanation'] = self._generate_explanation(impact_analysis)

        # Generate recommendation
        impact_analysis['recommendation'] = self._generate_recommendation(impact_analysis)

        # Determine risk level
        impact_analysis['risk_level'] = self._assess_risk_level(
            current_cpu, current_memory, impact_analysis['primary_cause']
        )

        return impact_analysis

    def _calculate_cpu_impact(self, cpu_percent: float) -> str:
        """
        Calculate the impact level of CPU usage.

        Args:
            cpu_percent: CPU usage percentage

        Returns:
            Impact level string
        """
        if cpu_percent > 80:
            return 'Critical'
        elif cpu_percent > 50:
            return 'High'
        elif cpu_percent > 25:
            return 'Medium'
        else:
            return 'Low'

    def _calculate_memory_impact(self, memory_percent: float) -> str:
        """
        Calculate the impact level of memory usage.

        Args:
            memory_percent: Memory usage percentage

        Returns:
            Impact level string
        """
        if memory_percent > 30:
            return 'Critical'
        elif memory_percent > 20:
            return 'High'
        elif memory_percent > 10:
            return 'Medium'
        else:
            return 'Low'

    def _determine_primary_cause(self, cpu_culprit: Optional[Dict],
                                cpu_usage: float,
                                memory_culprit: Optional[Dict],
                                memory_usage: float) -> Optional[str]:
        """
        Determine the primary cause of slowdown.

        Args:
            cpu_culprit: Top CPU consuming process
            cpu_usage: Overall CPU usage
            memory_culprit: Top memory consuming process
            memory_usage: Overall memory usage

        Returns:
            Primary cause identifier
        """
        if cpu_usage > memory_usage and cpu_culprit:
            return 'CPU'
        elif memory_usage > cpu_usage and memory_culprit:
            return 'Memory'
        elif cpu_culprit:
            return 'CPU'
        elif memory_culprit:
            return 'Memory'
        return None

    def _generate_explanation(self, impact_analysis: Dict) -> str:
        """
        Generate a human-readable explanation of the slowdown.

        Args:
            impact_analysis: Impact analysis dictionary

        Returns:
            Explanation string
        """
        explanation_parts = []

        if impact_analysis['primary_cause'] == 'CPU':
            if impact_analysis['cpu_culprit']:
                process = impact_analysis['cpu_culprit']
                explanation_parts.append(
                    f"System performance degraded. Top CPU consumer: "
                    f"{process['name']} ({process['usage']:.1f}%)."
                )
                if 'secondary_cpu' in impact_analysis:
                    secondary = impact_analysis['secondary_cpu']
                    explanation_parts.append(
                        f"Secondary CPU user: {secondary['name']} ({secondary['usage']:.1f}%)."
                    )

        elif impact_analysis['primary_cause'] == 'Memory':
            if impact_analysis['memory_culprit']:
                process = impact_analysis['memory_culprit']
                explanation_parts.append(
                    f"System experiencing high memory pressure. Top memory consumer: "
                    f"{process['name']} ({process['memory_percent']:.1f}%, "
                    f"{process['memory_mb']:.0f} MB)."
                )

        if not explanation_parts:
            explanation_parts.append("System performance is currently healthy.")

        return " ".join(explanation_parts)

    def _generate_recommendation(self, impact_analysis: Dict) -> str:
        """
        Generate recommendations for resolving the issue.

        Args:
            impact_analysis: Impact analysis dictionary

        Returns:
            Recommendation string
        """
        recommendations = []

        if impact_analysis['primary_cause'] == 'CPU':
            if impact_analysis['cpu_culprit']:
                process = impact_analysis['cpu_culprit']
                recommendations.append(
                    f"Consider closing or restarting {process['name']} to reduce CPU usage."
                )
                recommendations.append(
                    "If this is a necessary application, check for updates or upgrades."
                )

        elif impact_analysis['primary_cause'] == 'Memory':
            if impact_analysis['memory_culprit']:
                process = impact_analysis['memory_culprit']
                recommendations.append(
                    f"Try closing {process['name']} to free up memory."
                )
                recommendations.append(
                    "Alternatively, increase your system RAM or enable virtual memory."
                )

        if not recommendations:
            recommendations.append("System is running normally. No action needed.")

        return " ".join(recommendations)

    def _assess_risk_level(self, cpu_usage: float, memory_usage: float,
                          primary_cause: Optional[str]) -> str:
        """
        Assess the risk level of current system state.

        Args:
            cpu_usage: Overall CPU usage
            memory_usage: Overall memory usage
            primary_cause: Primary cause of slowdown

        Returns:
            Risk level string
        """
        if cpu_usage > 90 or memory_usage > 90:
            return 'Critical'
        elif cpu_usage > 75 or memory_usage > 75:
            return 'High'
        elif cpu_usage > 50 or memory_usage > 50:
            return 'Medium'
        else:
            return 'Low'

    def get_process_summary(self, processes: List[Dict]) -> Dict:
        """
        Get a summary of process categories and their resource usage.

        Args:
            processes: List of process dictionaries

        Returns:
            Dictionary with process category summary
        """
        summary = {
            'browsers': {'count': 0, 'total_cpu': 0, 'total_memory': 0},
            'office': {'count': 0, 'total_cpu': 0, 'total_memory': 0},
            'development': {'count': 0, 'total_cpu': 0, 'total_memory': 0},
            'system': {'count': 0, 'total_cpu': 0, 'total_memory': 0},
            'other': {'count': 0, 'total_cpu': 0, 'total_memory': 0}
        }

        for process in processes:
            name = process.get('name', '').lower()
            cpu = process.get('cpu_percent', 0)
            memory = process.get('memory_mb', 0)

            category = 'other'

            if any(x in name for x in ['chrome', 'firefox', 'edge', 'safari', 'explorer']):
                category = 'browsers'
            elif any(x in name for x in ['word', 'excel', 'powerpoint', 'outlook']):
                category = 'office'
            elif any(x in name for x in ['python', 'java', 'node', 'vscode', 'code', 'ide']):
                category = 'development'
            elif any(x in name for x in ['svchost', 'system', 'dwm', 'registry', 'csrss']):
                category = 'system'

            summary[category]['count'] += 1
            summary[category]['total_cpu'] += cpu
            summary[category]['total_memory'] += memory

        return summary

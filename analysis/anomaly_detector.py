"""
Anomaly Detector Module
Uses rule-based logic to detect system anomalies with optional ML enhancement.
Hybrid approach: rule-based triggers suspicion, ML confirms anomaly.
"""

import time
from collections import deque
import config
from constants import SYSTEM_PROCESSES_TO_IGNORE


class AnomalyDetector:
    """
    Rule-based anomaly detector for system monitoring.
    Detects abnormal behavior based on predefined thresholds and patterns.
    Supports a hybrid approach with optional ML confirmation.
    """

    def __init__(self):
        """Initialize the anomaly detector with default settings."""
        self.cpu_history = deque(maxlen=config.HISTORY_SIZE)
        self.memory_history = deque(maxlen=config.HISTORY_SIZE)
        self.last_anomalies = []

        # Optional ML detector reference (set via set_ml_detector)
        self.ml_detector = None

    def set_ml_detector(self, ml_detector):
        """
        Attach an ML detector for hybrid analysis.

        Args:
            ml_detector: MLDetector instance
        """
        self.ml_detector = ml_detector

    def update_history(self, cpu_usage, memory_usage):
        """
        Append current readings to the history buffers.

        Args:
            cpu_usage: Current CPU usage percentage
            memory_usage: Current memory usage percentage
        """
        timestamp = time.time()
        self.cpu_history.append({'timestamp': timestamp, 'value': cpu_usage})
        self.memory_history.append({'timestamp': timestamp, 'value': memory_usage})

    # ------------------------------------------------------------------
    # System-level detectors
    # ------------------------------------------------------------------

    def detect_cpu_spike(self):
        """Detect a sustained CPU spike using rolling averages."""
        if len(self.cpu_history) < 10:
            return None

        history_list = list(self.cpu_history)
        recent_avg = sum(h['value'] for h in history_list[-5:]) / 5
        previous_avg = sum(h['value'] for h in history_list[-10:-5]) / 5
        current = history_list[-1]['value']

        if current - previous_avg >= config.CPU_SPIKE_THRESHOLD:
            recent_high_count = sum(1 for h in history_list[-5:]
                                    if h['value'] >= config.CPU_WARNING_THRESHOLD)
            if recent_high_count >= 3:
                return {
                    'type': 'CPU Spike',
                    'severity': config.SEVERITY_HIGH,
                    'description': (
                        f"CPU usage significantly increased from "
                        f"{previous_avg:.1f}% to {current:.1f}% (sustained)"
                    ),
                    'value': current,
                    'previous_value': previous_avg
                }
        return None

    def detect_sustained_high_cpu(self):
        """Detect sustained high CPU usage."""
        if len(self.cpu_history) < config.SUSTAINED_HIGH_COUNT:
            return None

        recent = list(self.cpu_history)[-config.SUSTAINED_HIGH_COUNT:]
        high_count = sum(1 for r in recent if r['value'] >= config.CPU_WARNING_THRESHOLD)

        if high_count >= config.SUSTAINED_HIGH_COUNT:
            avg_usage = sum(r['value'] for r in recent) / len(recent)
            return {
                'type': 'Sustained High CPU',
                'severity': config.SEVERITY_MEDIUM,
                'description': (
                    f"CPU usage has been above {config.CPU_WARNING_THRESHOLD}% "
                    f"for {config.SUSTAINED_HIGH_COUNT} seconds (avg: {avg_usage:.1f}%)"
                ),
                'value': avg_usage
            }
        return None

    def detect_memory_spike(self):
        """Detect a sudden memory spike."""
        if len(self.memory_history) < 2:
            return None

        history_list = list(self.memory_history)
        previous = history_list[-2]['value']
        current = history_list[-1]['value']

        if current - previous >= 20.0:
            return {
                'type': 'Memory Spike',
                'severity': config.SEVERITY_HIGH,
                'description': (
                    f"Memory usage suddenly increased from "
                    f"{previous:.1f}% to {current:.1f}%"
                ),
                'value': current,
                'previous_value': previous
            }
        return None

    def detect_sustained_high_memory(self):
        """Detect sustained high memory usage."""
        if len(self.memory_history) < config.SUSTAINED_HIGH_COUNT:
            return None

        recent = list(self.memory_history)[-config.SUSTAINED_HIGH_COUNT:]
        high_count = sum(1 for r in recent if r['value'] >= config.MEMORY_WARNING_THRESHOLD)

        if high_count >= config.SUSTAINED_HIGH_COUNT:
            avg_usage = sum(r['value'] for r in recent) / len(recent)
            return {
                'type': 'Sustained High Memory',
                'severity': config.SEVERITY_MEDIUM,
                'description': (
                    f"Memory usage has been above {config.MEMORY_WARNING_THRESHOLD}% "
                    f"for {config.SUSTAINED_HIGH_COUNT} seconds (avg: {avg_usage:.1f}%)"
                ),
                'value': avg_usage
            }
        return None

    def detect_critical_cpu(self):
        """Detect critical CPU usage level."""
        if not self.cpu_history:
            return None

        current = self.cpu_history[-1]['value']
        if current >= config.CPU_CRITICAL_THRESHOLD:
            return {
                'type': 'Critical CPU Usage',
                'severity': config.SEVERITY_CRITICAL,
                'description': f"CPU usage is critically high at {current:.1f}%",
                'value': current
            }
        return None

    def detect_critical_memory(self):
        """Detect critical memory usage level."""
        if not self.memory_history:
            return None

        current = self.memory_history[-1]['value']
        if current >= config.MEMORY_CRITICAL_THRESHOLD:
            return {
                'type': 'Critical Memory Usage',
                'severity': config.SEVERITY_CRITICAL,
                'description': f"Memory usage is critically high at {current:.1f}%",
                'value': current
            }
        return None

    # ------------------------------------------------------------------
    # Process-level detector
    # ------------------------------------------------------------------

    def detect_process_anomaly(self, process_info):
        """
        Detect if a specific process is behaving anomalously.

        Returns:
            list or None: List of anomaly dicts, or None if normal
        """
        process_name = process_info.get('name', '')
        pid = process_info.get('pid', -1)

        # Skip system processes and known PIDs
        if process_name in SYSTEM_PROCESSES_TO_IGNORE or pid in (0, 4):
            return None

        cpu_percent = process_info.get('cpu_percent', 0)
        if cpu_percent > 100.0:
            return None

        anomalies = []

        # High CPU
        if cpu_percent >= config.PROCESS_HIGH_CPU_THRESHOLD:
            anomalies.append({
                'type': 'High CPU Process',
                'severity': config.SEVERITY_HIGH,
                'description': (
                    f"Process '{process_name}' (PID: {pid}) "
                    f"using high CPU: {cpu_percent:.1f}%"
                ),
                'process': process_info
            })

        # High memory
        memory_mb = process_info.get('memory_mb', 0)
        if memory_mb >= config.PROCESS_HIGH_MEMORY_THRESHOLD:
            anomalies.append({
                'type': 'High Memory Process',
                'severity': config.SEVERITY_HIGH,
                'description': (
                    f"Process '{process_name}' (PID: {pid}) "
                    f"using high memory: {memory_mb:.1f} MB"
                ),
                'process': process_info
            })

        # Long-running AND resource-intensive
        uptime_hours = process_info.get('uptime_hours', 0)
        if uptime_hours >= config.PROCESS_LONG_RUNNING_HOURS and (cpu_percent >= 10 or memory_mb >= 200):
            anomalies.append({
                'type': 'Long-running Resource-intensive Process',
                'severity': config.SEVERITY_MEDIUM,
                'description': (
                    f"Process '{process_name}' (PID: {pid}) "
                    f"running for {uptime_hours:.1f} hours"
                ),
                'process': process_info
            })

        return anomalies if anomalies else None

    # ------------------------------------------------------------------
    # ML hybrid integration
    # ------------------------------------------------------------------

    def _apply_ml_confirmation(self, anomaly, disk_usage, process_count):
        """Apply ML confirmation to a rule-based anomaly (hybrid approach)."""
        if self.ml_detector is None or not self.ml_detector.can_predict():
            return anomaly

        cpu_std = self._calculate_std([h['value'] for h in self.cpu_history]) if len(self.cpu_history) > 1 else 0
        memory_std = self._calculate_std([h['value'] for h in self.memory_history]) if len(self.memory_history) > 1 else 0

        cpu_usage = self.cpu_history[-1]['value'] if self.cpu_history else 0
        memory_usage = self.memory_history[-1]['value'] if self.memory_history else 0

        ml_anomaly, ml_score, ml_explanation = self.ml_detector.predict(
            cpu_usage, memory_usage, disk_usage, process_count, cpu_std, memory_std
        )

        anomaly['ml_confirmed'] = ml_anomaly
        anomaly['ml_score'] = ml_score
        anomaly['ml_explanation'] = ml_explanation

        # Severity adjustment based on ML agreement
        severity = anomaly.get('severity')
        if severity == config.SEVERITY_HIGH:
            if not ml_anomaly:
                anomaly['severity'] = config.SEVERITY_MEDIUM
                anomaly['description'] += " (ML: pattern appears normal)"
            elif ml_score > 70:
                anomaly['description'] += " (ML confirmed)"
        elif severity == config.SEVERITY_MEDIUM:
            if ml_anomaly and ml_score > 75:
                anomaly['severity'] = config.SEVERITY_HIGH
                anomaly['description'] += " (ML confirmed)"

        return anomaly

    @staticmethod
    def _calculate_std(values):
        """Calculate population standard deviation."""
        if len(values) < 2:
            return 0.0
        mean = sum(values) / len(values)
        variance = sum((x - mean) ** 2 for x in values) / len(values)
        return variance ** 0.5

    # ------------------------------------------------------------------
    # Comprehensive analysis entry point
    # ------------------------------------------------------------------

    def analyze_all(self, cpu_usage, memory_usage, process_list, disk_usage=0, process_count=None):
        """
        Perform comprehensive anomaly analysis on all metrics.

        Args:
            cpu_usage: Current CPU usage percentage
            memory_usage: Current memory usage percentage
            process_list: List of process dicts
            disk_usage: Current disk usage percentage
            process_count: Total process count (auto-derived if None)

        Returns:
            list: Detected anomaly dictionaries
        """
        self.update_history(cpu_usage, memory_usage)

        if process_count is None:
            process_count = len(process_list) if process_list else 0

        anomalies = []

        # Critical checks first
        for detector in (self.detect_critical_cpu, self.detect_critical_memory):
            result = detector()
            if result:
                anomalies.append(self._apply_ml_confirmation(result, disk_usage, process_count))

        # Spike checks
        for detector in (self.detect_cpu_spike, self.detect_memory_spike):
            result = detector()
            if result:
                anomalies.append(self._apply_ml_confirmation(result, disk_usage, process_count))

        # Sustained high checks
        for detector in (self.detect_sustained_high_cpu, self.detect_sustained_high_memory):
            result = detector()
            if result:
                anomalies.append(self._apply_ml_confirmation(result, disk_usage, process_count))

        # Process-level detection
        for process in process_list:
            if process.get('pid', 0) == 0:
                continue
            if process.get('name', '') in SYSTEM_PROCESSES_TO_IGNORE:
                continue

            process_anomaly = self.detect_process_anomaly(process)
            if process_anomaly:
                anomalies.extend(process_anomaly)

        self.last_anomalies = anomalies
        return anomalies

    # ------------------------------------------------------------------
    # Health score
    # ------------------------------------------------------------------

    def calculate_health_score(self, cpu_usage, memory_usage, anomaly_count):
        """
        Calculate overall system health score (0–100).

        The score is a weighted blend of inverted CPU/memory percentages
        minus an anomaly penalty.
        """
        cpu_score = 100 - cpu_usage
        memory_score = 100 - memory_usage
        anomaly_penalty = min(anomaly_count * 10, 30)

        health_score = (
            (cpu_score * config.CPU_WEIGHT) +
            (memory_score * config.MEMORY_WEIGHT) +
            ((100 - anomaly_penalty) * config.ANOMALY_WEIGHT)
        )

        return max(0, min(100, health_score))

    def get_health_status(self, health_score):
        """Map a numeric health score to a human-readable label."""
        if health_score >= 80:
            return "Excellent"
        elif health_score >= 60:
            return "Good"
        elif health_score >= 40:
            return "Fair"
        elif health_score >= 20:
            return "Poor"
        else:
            return "Critical"

    def get_last_anomalies(self):
        """Get the last set of detected anomalies."""
        return self.last_anomalies

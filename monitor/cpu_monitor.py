"""
CPU Monitor Module
Monitors CPU usage and provides utilities for CPU-related analysis.
"""

import psutil
from collections import deque
import time


class CPUMonitor:
    """Monitor CPU usage with history tracking."""

    def __init__(self, history_size=60):
        """
        Initialize CPU monitor.

        Args:
            history_size: Number of historical readings to keep
        """
        self.history_size = history_size
        self.history = deque(maxlen=history_size)
        self.last_reading = None

        # Prime the internal counter so the next call returns a real delta
        psutil.cpu_percent(interval=None)

    def get_current_usage(self):
        """
        Get current CPU usage percentage.

        Returns:
            float: CPU usage percentage clamped to 0–100
        """
        cpu_percent = psutil.cpu_percent(interval=0.1)
        return min(100.0, max(0.0, cpu_percent))

    def get_per_cpu_usage(self):
        """
        Get usage for each CPU core.

        Returns:
            list: Per-core usage percentages, each clamped to 0–100
        """
        per_cpu = psutil.cpu_percent(interval=0.1, percpu=True)
        return [min(100.0, max(0.0, c)) for c in per_cpu]

    def get_cpu_count(self):
        """
        Get number of CPU cores.

        Returns:
            int: Number of CPU cores (at least 1)
        """
        return psutil.cpu_count() or 1

    def get_cpu_freq(self):
        """
        Get current CPU frequency.

        Returns:
            dict or None: Dictionary with current, min, and max frequency
        """
        cpu_freq = psutil.cpu_freq()
        if cpu_freq:
            return {
                'current': cpu_freq.current,
                'min': cpu_freq.min,
                'max': cpu_freq.max
            }
        return None

    def record_reading(self):
        """
        Record current CPU reading to history.

        Returns:
            float: Current CPU usage (0–100)
        """
        current = self.get_current_usage()
        self.history.append({
            'timestamp': time.time(),
            'usage': current
        })
        self.last_reading = current
        return current

    def get_history(self):
        """
        Get CPU usage history.

        Returns:
            deque: History of CPU readings
        """
        return self.history

    def get_average_usage(self, last_n=None):
        """
        Calculate average CPU usage over the last N readings.

        Args:
            last_n: Number of recent readings to average (None for all)

        Returns:
            float: Average CPU usage (0–100)
        """
        if not self.history:
            return 0.0

        readings = list(self.history) if last_n is None else list(self.history)[-last_n:]

        if not readings:
            return 0.0

        return sum(r['usage'] for r in readings) / len(readings)

    def detect_spike(self, threshold=30.0):
        """
        Detect a sudden CPU spike that is also sustained.

        A spike is reported only when the current reading exceeds the
        previous one by at least *threshold* percentage points AND the
        high state persists across several consecutive readings.

        Args:
            threshold: Minimum increase to consider as a spike

        Returns:
            bool: True if a sustained spike is detected
        """
        if self.last_reading is None or len(self.history) < 2:
            return False

        history_list = list(self.history)
        previous = history_list[-2]['usage']
        current = self.last_reading

        if current - previous >= threshold:
            return self.is_sustained_high(threshold - 10, 3)

        return False

    def is_sustained_high(self, threshold=70.0, count=10):
        """
        Check if CPU has been consistently above *threshold*.

        Args:
            threshold: Usage percentage to consider as high
            count: Number of consecutive high readings required

        Returns:
            bool: True if sustained high usage is detected
        """
        if len(self.history) < count:
            return False

        recent = list(self.history)[-count:]
        high_count = sum(1 for r in recent if r['usage'] >= threshold)

        return high_count >= count

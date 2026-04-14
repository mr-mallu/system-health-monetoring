"""
CPU Monitor Module
Monitors CPU usage and provides utilities for CPU-related analysis.

FIXED: CPU calculation now properly normalized to 0-100% range.
Uses psutil.cpu_percent() correctly with initialization for accurate readings.
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
        
        # FIX: Initialize CPU measurement for accurate first reading
        # Call once to initialize, then subsequent calls will be accurate
        psutil.cpu_percent(interval=None)
        self._initialized = True
    
    def get_current_usage(self):
        """
        Get current CPU usage percentage.
        FIXED: Now properly normalized to 0-100% range.
        
        Returns:
            float: CPU usage percentage (0-100), never exceeds 100%
        """
        # FIX: Use correct psutil CPU measurement:
        # 1. First call with interval=None initializes measurement
        # 2. Small sleep allows accumulation of CPU stats
        # 3. Second call returns accurate percentage normalized to 0-100%
        
        # Get CPU usage with interval for accurate reading
        # psutil.cpu_percent() already returns 0-100% regardless of core count
        cpu_percent = psutil.cpu_percent(interval=0.1)
        
        # FIX: Clamp to valid range (0-100) as safety measure
        return min(100.0, max(0.0, cpu_percent))
    
    def get_per_cpu_usage(self):
        """
        Get usage for each CPU core.
        
        Returns:
            list: List of CPU usage percentages for each core (each 0-100)
        """
        per_cpu = psutil.cpu_percent(interval=0.1, percpu=True)
        # Normalize each core to 0-100%
        return [min(100.0, max(0.0, c)) for c in per_cpu]
    
    def get_cpu_count(self):
        """
        Get number of CPU cores.
        
        Returns:
            int: Number of CPU cores
        """
        return psutil.cpu_count() or 1
    
    def get_cpu_freq(self):
        """
        Get current CPU frequency.
        
        Returns:
            dict: Dictionary with current, min, and max frequency
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
            float: Current CPU usage (0-100)
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
        Calculate average CPU usage over last N readings.
        
        Args:
            last_n: Number of recent readings to average (None for all)
            
        Returns:
            float: Average CPU usage (0-100)
        """
        if not self.history:
            return 0.0
        
        if last_n is None:
            readings = list(self.history)
        else:
            readings = list(self.history)[-last_n:]
        
        if not readings:
            return 0.0
        
        return sum(r['usage'] for r in readings) / len(readings)
    
    def detect_spike(self, threshold=30.0):
        """
        Detect sudden CPU spike.
        FIXED: Now requires sustained high for alert, not single spike.
        
        Args:
            threshold: Minimum increase to consider as spike
            
        Returns:
            bool: True if spike detected AND sustained
        """
        # FIX: Need at least 2 readings to detect spike
        if self.last_reading is None or len(self.history) < 2:
            return False
        
        # Get previous reading
        history_list = list(self.history)
        if len(history_list) >= 2:
            previous = history_list[-2]['usage']
            current = self.last_reading
            
            # FIX: Check if current is significantly higher than previous
            # AND if this is a sustained condition (not just a momentary spike)
            if current - previous >= threshold:
                # FIX: Check if this high state persists
                return self.is_sustained_high(threshold - 10, 3)
        
        return False
    
    def is_sustained_high(self, threshold=70.0, count=10):
        """
        Check if CPU has been consistently high.
        
        Args:
            threshold: Threshold percentage to consider as high
            count: Number of consecutive high readings
            
        Returns:
            bool: True if sustained high usage detected
        """
        if len(self.history) < count:
            return False
        
        recent = list(self.history)[-count:]
        high_count = sum(1 for r in recent if r['usage'] >= threshold)
        
        return high_count >= count

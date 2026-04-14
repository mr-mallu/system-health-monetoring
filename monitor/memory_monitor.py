"""
Memory Monitor Module
Monitors RAM usage and provides utilities for memory-related analysis.
"""

import psutil
from collections import deque
import time


class MemoryMonitor:
    """Monitor memory (RAM) usage with history tracking."""
    
    def __init__(self, history_size=60):
        """
        Initialize memory monitor.
        
        Args:
            history_size: Number of historical readings to keep
        """
        self.history_size = history_size
        self.history = deque(maxlen=history_size)
        self.last_reading = None
    
    def get_current_usage(self):
        """
        Get current memory usage percentage.
        
        Returns:
            float: Memory usage percentage (0-100)
        """
        memory = psutil.virtual_memory()
        return memory.percent
    
    def get_memory_info(self):
        """
        Get detailed memory information.
        
        Returns:
            dict: Dictionary with memory details
        """
        memory = psutil.virtual_memory()
        return {
            'total': memory.total,  # Total physical memory in bytes
            'available': memory.available,  # Available memory in bytes
            'used': memory.used,  # Used memory in bytes
            'percent': memory.percent,  # Usage percentage
            'free': memory.free  # Free memory in bytes
        }
    
    def get_memory_in_mb(self):
        """
        Get memory usage in MB.
        
        Returns:
            dict: Dictionary with memory in MB
        """
        memory = psutil.virtual_memory()
        return {
            'total': memory.total / (1024 * 1024),
            'available': memory.available / (1024 * 1024),
            'used': memory.used / (1024 * 1024),
            'free': memory.free / (1024 * 1024)
        }
    
    def record_reading(self):
        """
        Record current memory reading to history.
        
        Returns:
            float: Current memory usage
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
        Get memory usage history.
        
        Returns:
            deque: History of memory readings
        """
        return self.history
    
    def get_average_usage(self, last_n=None):
        """
        Calculate average memory usage over last N readings.
        
        Args:
            last_n: Number of recent readings to average (None for all)
            
        Returns:
            float: Average memory usage
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
    
    def detect_spike(self, threshold=20.0):
        """
        Detect sudden memory spike.
        
        Args:
            threshold: Minimum increase to consider as spike
            
        Returns:
            bool: True if spike detected
        """
        if self.last_reading is None or len(self.history) < 2:
            return False
        
        history_list = list(self.history)
        if len(history_list) >= 2:
            previous = history_list[-2]['usage']
            current = self.last_reading
            
            # Check if current is significantly higher than previous
            if current - previous >= threshold:
                return True
        
        return False
    
    def is_sustained_high(self, threshold=70.0, count=10):
        """
        Check if memory has been consistently high.
        
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

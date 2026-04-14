"""
Disk Monitor Module
Monitors disk usage and provides utilities for disk-related analysis.
"""

import psutil
from collections import deque
import time


class DiskMonitor:
    """Monitor disk usage with history tracking."""
    
    def __init__(self, history_size=60):
        """
        Initialize disk monitor.
        
        Args:
            history_size: Number of historical readings to keep
        """
        self.history_size = history_size
        self.history = deque(maxlen=history_size)
        self.last_reading = None
    
    def get_current_usage(self, drive='C:'):
        """
        Get current disk usage for a specific drive.
        
        Args:
            drive: Drive letter to monitor (default: C:)
            
        Returns:
            float: Disk usage percentage (0-100)
        """
        try:
            disk = psutil.disk_usage(drive)
            return disk.percent
        except Exception as e:
            print(f"Error getting disk usage for {drive}: {e}")
            return 0.0
    
    def get_disk_info(self, drive='C:'):
        """
        Get detailed disk information.
        
        Args:
            drive: Drive letter to monitor
            
        Returns:
            dict: Dictionary with disk details
        """
        try:
            disk = psutil.disk_usage(drive)
            return {
                'total': disk.total,  # Total disk space in bytes
                'used': disk.used,  # Used disk space in bytes
                'free': disk.free,  # Free disk space in bytes
                'percent': disk.percent  # Usage percentage
            }
        except Exception as e:
            print(f"Error getting disk info for {drive}: {e}")
            return {
                'total': 0,
                'used': 0,
                'free': 0,
                'percent': 0
            }
    
    def get_disk_in_gb(self, drive='C:'):
        """
        Get disk usage in GB.
        
        Args:
            drive: Drive letter to monitor
            
        Returns:
            dict: Dictionary with disk in GB
        """
        try:
            disk = psutil.disk_usage(drive)
            gb_factor = 1024 * 1024 * 1024
            return {
                'total': disk.total / gb_factor,
                'used': disk.used / gb_factor,
                'free': disk.free / gb_factor
            }
        except Exception as e:
            print(f"Error getting disk in GB for {drive}: {e}")
            return {
                'total': 0,
                'used': 0,
                'free': 0
            }
    
    def get_all_partitions(self):
        """
        Get information about all disk partitions.
        
        Returns:
            list: List of dictionaries with partition information
        """
        partitions = []
        for partition in psutil.disk_partitions():
            try:
                usage = psutil.disk_usage(partition.mountpoint)
                partitions.append({
                    'device': partition.device,
                    'mountpoint': partition.mountpoint,
                    'fstype': partition.fstype,
                    'total': usage.total,
                    'used': usage.used,
                    'free': usage.free,
                    'percent': usage.percent
                })
            except Exception:
                pass
        return partitions
    
    def record_reading(self, drive='C:'):
        """
        Record current disk reading to history.
        
        Args:
            drive: Drive letter to monitor
            
        Returns:
            float: Current disk usage
        """
        current = self.get_current_usage(drive)
        self.history.append({
            'timestamp': time.time(),
            'usage': current,
            'drive': drive
        })
        self.last_reading = current
        return current
    
    def get_history(self):
        """
        Get disk usage history.
        
        Returns:
            deque: History of disk readings
        """
        return self.history
    
    def get_average_usage(self, last_n=None):
        """
        Calculate average disk usage over last N readings.
        
        Args:
            last_n: Number of recent readings to average (None for all)
            
        Returns:
            float: Average disk usage
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

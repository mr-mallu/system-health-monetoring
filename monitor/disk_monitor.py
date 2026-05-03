"""
Disk Monitor Module
Monitors disk usage and provides utilities for disk-related analysis.
"""

import logging
import psutil
from collections import deque
import time

logger = logging.getLogger(__name__)


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
            float: Disk usage percentage (0–100)
        """
        try:
            return psutil.disk_usage(drive).percent
        except (FileNotFoundError, PermissionError, OSError) as e:
            logger.warning("Cannot read disk usage for %s: %s", drive, e)
            return 0.0

    def get_disk_info(self, drive='C:'):
        """
        Get detailed disk information in bytes.

        Args:
            drive: Drive letter to monitor

        Returns:
            dict: total, used, free, and percent disk usage
        """
        try:
            disk = psutil.disk_usage(drive)
            return {
                'total': disk.total,
                'used': disk.used,
                'free': disk.free,
                'percent': disk.percent
            }
        except (FileNotFoundError, PermissionError, OSError) as e:
            logger.warning("Cannot read disk info for %s: %s", drive, e)
            return {'total': 0, 'used': 0, 'free': 0, 'percent': 0}

    def get_disk_in_gb(self, drive='C:'):
        """
        Get disk usage in gigabytes.

        Args:
            drive: Drive letter to monitor

        Returns:
            dict: total, used, and free disk space in GB
        """
        try:
            disk = psutil.disk_usage(drive)
            gb = 1024 ** 3
            return {
                'total': disk.total / gb,
                'used': disk.used / gb,
                'free': disk.free / gb
            }
        except (FileNotFoundError, PermissionError, OSError) as e:
            logger.warning("Cannot read disk in GB for %s: %s", drive, e)
            return {'total': 0, 'used': 0, 'free': 0}

    def get_all_partitions(self):
        """
        Get information about all disk partitions.

        Returns:
            list: Partition information dictionaries
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
            except (PermissionError, OSError):
                # Some partitions (e.g. recovery) are not accessible
                pass
        return partitions

    def record_reading(self, drive='C:'):
        """
        Record current disk reading to history.

        Args:
            drive: Drive letter to monitor

        Returns:
            float: Current disk usage percentage
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
        Calculate average disk usage over the last N readings.

        Args:
            last_n: Number of recent readings to average (None for all)

        Returns:
            float: Average disk usage
        """
        if not self.history:
            return 0.0

        readings = list(self.history) if last_n is None else list(self.history)[-last_n:]

        if not readings:
            return 0.0

        return sum(r['usage'] for r in readings) / len(readings)

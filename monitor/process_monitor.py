"""
Process Monitor Module
Monitors running processes and provides process intelligence.
"""

import logging
import psutil
from collections import deque
import time

from constants import SYSTEM_PROCESSES_TO_IGNORE

logger = logging.getLogger(__name__)


class ProcessMonitor:
    """Monitor running processes with intelligence capabilities."""

    def __init__(self, high_cpu_threshold=50.0, high_memory_threshold_mb=500, long_running_hours=24):
        """
        Initialize process monitor.

        Args:
            high_cpu_threshold: CPU usage threshold to flag as high (percentage)
            high_memory_threshold_mb: Memory threshold to flag as high (MB)
            long_running_hours: Hours to consider a process as long-running
        """
        self.high_cpu_threshold = high_cpu_threshold
        self.high_memory_threshold_mb = high_memory_threshold_mb
        self.long_running_hours = long_running_hours
        self.process_start_times = {}
        self.process_memory_history = deque(maxlen=30)

    def _is_system_process(self, process_name):
        """Check if a process should be excluded from alerts."""
        return process_name in SYSTEM_PROCESSES_TO_IGNORE

    def get_all_processes(self):
        """
        Get list of all running user processes with details.

        System processes (PID 0, known OS services) are filtered out.
        CPU percentages are normalized per-core to stay within 0–100%.

        Returns:
            list: Process information dictionaries
        """
        processes = []

        for proc in psutil.process_iter(['pid', 'name', 'cpu_percent', 'memory_percent', 'create_time']):
            try:
                pinfo = proc.info
                pid = pinfo.get('pid', 0)
                name = pinfo.get('name', '')

                # Skip System Idle Process and known system services
                if pid == 0:
                    continue
                if not name or name.strip() == '':
                    name = f"PID_{pid}"
                if self._is_system_process(name):
                    continue

                # Memory in MB
                try:
                    memory_mb = proc.memory_info().rss / (1024 * 1024)
                except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                    memory_mb = 0

                # Normalize CPU: process_iter's cached cpu_percent is an
                # aggregate across all cores, so divide by core count.
                try:
                    cpu_percent = (pinfo.get('cpu_percent', 0) or 0) / (psutil.cpu_count() or 1)
                    cpu_percent = min(100.0, max(0.0, cpu_percent))
                except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                    cpu_percent = 0

                # Uptime calculation
                try:
                    create_time = pinfo.get('create_time')
                    uptime_hours = (time.time() - create_time) / 3600 if create_time else 0
                except Exception:
                    create_time = None
                    uptime_hours = 0

                if pid not in self.process_start_times and create_time:
                    self.process_start_times[pid] = create_time

                processes.append({
                    'pid': pid,
                    'name': name,
                    'cpu_percent': cpu_percent,
                    'memory_percent': pinfo.get('memory_percent', 0),
                    'memory_mb': memory_mb,
                    'uptime_hours': uptime_hours,
                    'create_time': create_time,
                    'is_system_process': False
                })

            except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                pass
            except Exception as e:
                logger.debug("Unexpected error reading process: %s", e)

        return processes

    def get_top_processes_by_cpu(self, limit=10):
        """
        Get top processes by CPU usage.

        Args:
            limit: Number of top processes to return

        Returns:
            list: Top processes sorted by CPU usage (descending)
        """
        processes = self.get_all_processes()
        return sorted(processes, key=lambda x: x['cpu_percent'], reverse=True)[:limit]

    def get_top_processes_by_memory(self, limit=10):
        """
        Get top processes by memory usage.

        Args:
            limit: Number of top processes to return

        Returns:
            list: Top processes sorted by memory usage (descending)
        """
        processes = self.get_all_processes()
        return sorted(processes, key=lambda x: x['memory_mb'], reverse=True)[:limit]

    def get_high_cpu_processes(self):
        """Get processes exceeding the CPU threshold."""
        return [p for p in self.get_all_processes()
                if p['cpu_percent'] >= self.high_cpu_threshold]

    def get_high_memory_processes(self):
        """Get processes exceeding the memory threshold."""
        return [p for p in self.get_all_processes()
                if p['memory_mb'] >= self.high_memory_threshold_mb]

    def get_long_running_processes(self):
        """Get processes running longer than the configured threshold."""
        return [p for p in self.get_all_processes()
                if p['uptime_hours'] >= self.long_running_hours]

    def get_anomalous_processes(self):
        """
        Get all processes flagged as potentially anomalous.

        Returns:
            dict: Categorised anomalous processes
        """
        return {
            'high_cpu': self.get_high_cpu_processes(),
            'high_memory': self.get_high_memory_processes(),
            'long_running': self.get_long_running_processes()
        }

    def get_process_by_pid(self, pid):
        """
        Get detailed information about a specific process.

        Args:
            pid: Process ID

        Returns:
            dict or None: Process information
        """
        try:
            proc = psutil.Process(pid)
            return {
                'pid': proc.pid,
                'name': proc.name(),
                'status': proc.status(),
                'cpu_percent': proc.cpu_percent(interval=0.01),
                'memory_percent': proc.memory_percent(),
                'memory_info': proc.memory_info()._asdict(),
                'create_time': proc.create_time(),
                'num_threads': proc.num_threads(),
                'cmdline': proc.cmdline(),
                'exe': proc.exe()
            }
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            return None

    def terminate_process(self, pid, simulate=True):
        """
        Attempt to terminate a process.

        Args:
            pid: Process ID to terminate
            simulate: If True, only simulate the termination

        Returns:
            dict: Result of the termination attempt
        """
        result = {'success': False, 'message': '', 'simulated': simulate}

        try:
            proc = psutil.Process(pid)

            if simulate:
                result['success'] = True
                result['message'] = f"Simulated termination of process: {proc.name()} (PID: {pid})"
            else:
                proc.terminate()
                result['success'] = True
                result['message'] = f"Terminated process: {proc.name()} (PID: {pid})"

        except psutil.NoSuchProcess:
            result['message'] = f"Process with PID {pid} not found"
        except psutil.AccessDenied:
            result['message'] = f"Access denied to terminate process {pid}"
        except Exception as e:
            result['message'] = f"Error terminating process: {e}"

        return result

    def get_system_process_summary(self):
        """
        Get summary statistics of running processes.

        Returns:
            dict: Aggregate counts and totals
        """
        processes = self.get_all_processes()

        return {
            'total_count': len(processes),
            'total_cpu': sum(p['cpu_percent'] for p in processes),
            'total_memory_mb': sum(p['memory_mb'] for p in processes),
            'high_cpu_count': len(self.get_high_cpu_processes()),
            'high_memory_count': len(self.get_high_memory_processes()),
            'long_running_count': len(self.get_long_running_processes())
        }

"""
Process Monitor Module
Monitors running processes and provides process intelligence.

FIXED: 
- System Idle Process (PID 0) is now properly filtered
- Critical system processes are excluded from alerts
- Proper exception handling for AccessDenied and ZombieProcess
- CPU values use cached process_iter() attrs (no more 0.0 readings)
"""

import psutil
from collections import deque
import time
from datetime import datetime


# FIX: List of system process names to exclude from alerts
SYSTEM_PROCESSES_TO_IGNORE = {
    'System Idle Process', 'System', 'Registry', 'smss.exe',
    'csrss.exe', 'wininit.exe', 'services.exe', 'lsass.exe',
    'svchost.exe', 'Windows Terminal', 'conhost.exe', 'dwm.exe',
    'fontdrvhost.exe', 'sihost.exe', 'RuntimeBroker.exe',
    'SearchIndexer.exe', 'SecurityHealthService.exe', 'MsMpEng.exe',
    'NisSrv.exe', 'audiodg.exe', 'WmiPrvSE.exe', 'SearchHost.exe',
    'TextInputHost.exe', 'ShellExperienceHost.exe',
    'StartMenuExperienceHost.exe', 'MemCompression',
    'TiWorker.exe', 'WUDFHost.exe', 'MoUsoCoreWorker.exe',
    'McUICnt.exe', 'aswidsagent.exe', 'aswEngSrv.exe'
}


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
        """FIX: Check if a process is a system process to ignore."""
        return process_name in SYSTEM_PROCESSES_TO_IGNORE
    
    def get_all_processes(self):
        """
        Get list of all running processes with their details.
        FIXED: Now filters out PID 0 and system processes.
        FIXED: Uses cached cpu_percent from process_iter attrs.
        
        Returns:
            list: List of dictionaries containing process information
        """
        processes = []
        for proc in psutil.process_iter(['pid', 'name', 'cpu_percent', 'memory_percent', 'create_time']):
            try:
                pinfo = proc.info
                pid = pinfo.get('pid', 0)
                name = pinfo.get('name', '')
                
                # FIX: Skip System Idle Process (PID 0)
                if pid == 0:
                    continue
                
                # FIX: Handle blank/empty process names
                if not name or name.strip() == '':
                    name = f"PID_{pid}"
                
                # FIX: Skip known system processes
                if self._is_system_process(name):
                    continue
                
                # Get memory in MB
                try:
                    memory_info = proc.memory_info()
                    memory_mb = memory_info.rss / (1024 * 1024)
                except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                    memory_mb = 0
                
                # FIX: Use cached cpu_percent from process_iter() attrs list.
                # process_iter() with 'cpu_percent' in the attrs offers a
                # pre-computed, non-blocking value based on the delta since the
                # previous call.  Calling proc.cpu_percent() again resets the
                # measurement window and returns 0.0 for most processes.
                try:
                    cpu_percent = pinfo.get('cpu_percent', 0) or 0
                    num_cpus = psutil.cpu_count() or 1
                    cpu_percent = cpu_percent / num_cpus
                    cpu_percent = min(100.0, max(0.0, cpu_percent))
                except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                    cpu_percent = 0
                
                # Calculate uptime
                try:
                    create_time = pinfo.get('create_time')
                    if create_time:
                        uptime_seconds = time.time() - create_time
                        uptime_hours = uptime_seconds / 3600
                    else:
                        uptime_hours = 0
                except Exception:
                    uptime_hours = 0
                
                if pid not in self.process_start_times and create_time:
                    self.process_start_times[pid] = create_time
                
                process_info = {
                    'pid': pid,
                    'name': name,
                    'cpu_percent': cpu_percent,
                    'memory_percent': pinfo.get('memory_percent', 0),
                    'memory_mb': memory_mb,
                    'uptime_hours': uptime_hours,
                    'create_time': create_time,
                    'is_system_process': False
                }
                processes.append(process_info)
                
            except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                pass
            except Exception:
                pass
        
        return processes
    
    def get_top_processes_by_cpu(self, limit=10):
        """
        Get top processes by CPU usage.
        
        Args:
            limit: Number of top processes to return
            
        Returns:
            list: List of top processes by CPU usage
        """
        processes = self.get_all_processes()
        sorted_processes = sorted(processes, key=lambda x: x['cpu_percent'], reverse=True)
        return sorted_processes[:limit]
    
    def get_top_processes_by_memory(self, limit=10):
        """
        Get top processes by memory usage.
        
        Args:
            limit: Number of top processes to return
            
        Returns:
            list: List of top processes by memory usage
        """
        processes = self.get_all_processes()
        sorted_processes = sorted(processes, key=lambda x: x['memory_mb'], reverse=True)
        return sorted_processes[:limit]
    
    def get_high_cpu_processes(self):
        """
        Get processes with high CPU usage.
        
        Returns:
            list: List of processes exceeding CPU threshold
        """
        processes = self.get_all_processes()
        return [p for p in processes if p['cpu_percent'] >= self.high_cpu_threshold and p['pid'] != 0]
    
    def get_high_memory_processes(self):
        """
        Get processes with high memory usage.
        
        Returns:
            list: List of processes exceeding memory threshold
        """
        processes = self.get_all_processes()
        return [p for p in processes if p['memory_mb'] >= self.high_memory_threshold_mb]
    
    def get_long_running_processes(self):
        """
        Get processes that have been running for a long time.
        
        Returns:
            list: List of long-running processes
        """
        processes = self.get_all_processes()
        return [p for p in processes if p['uptime_hours'] >= self.long_running_hours]
    
    def get_anomalous_processes(self):
        """
        Get all processes that are flagged as potentially anomalous.
        
        Returns:
            dict: Dictionary with categorized anomalous processes
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
            dict: Process information or None if not found
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
        result = {
            'success': False,
            'message': '',
            'simulated': simulate
        }
        
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
            result['message'] = f"Error terminating process: {str(e)}"
        
        return result
    
    def get_system_process_summary(self):
        """
        Get summary of all processes.
        
        Returns:
            dict: Summary statistics of running processes
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

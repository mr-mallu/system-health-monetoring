"""
Anomaly Detector Module
Uses rule-based logic to detect system anomalies with optional ML enhancement.
Hybrid approach: Rule-based triggers suspicion, ML confirms anomaly.
"""

import time
from collections import deque
import config


# System processes to ignore for alerts - comprehensive list
SYSTEM_PROCESS_NAMES = {
    # Windows System Processes
    'System Idle Process', 'System', 'Registry', 'smss.exe',
    'csrss.exe', 'wininit.exe', 'services.exe', 'lsass.exe',
    'svchost.exe', 'dwm.exe', 'fontdrvhost.exe', 'MemCompression',
    'winlogon.exe', 'taskhostw.exe', 'dllhost.exe', 'conhost.exe',
    'ctfmon.exe', 'sihost.exe', 'winmgmt.exe',
    
    # Windows Services and Background Processes
    'WmiPrvSE.exe', 'WUDFHost.exe', 'sqlservr.exe', 'mongod.exe',
    'RemoteMouseService.exe', 'AVGSvc.exe', 'MoUsoCoreWorker.exe',
    'RuntimeBroker.exe', 'SearchIndexer.exe', 'SecurityHealthService.exe',
    'MsMpEng.exe', 'NisSrv.exe', 'audiodg.exe', 'SearchHost.exe',
    'TextInputHost.exe', 'ShellExperienceHost.exe', 'StartMenuExperienceHost.exe',
    'wmiprvse.exe', 'SgrmBroker.exe', 'SearchProtocolHost.exe',
    'SearchFilterHost.exe', 'SecurityHealthSystray.exe',
    
    # More Windows processes
    'EventLog.exe', 'PlugPlay.exe', 'SamSs.exe', 'LanmanServer.exe',
    'LanmanWorkstation.exe', 'NlaSvc.exe', 'nsi.exe', 'Schedule.exe',
    'Seclogon.exe', 'Themes.exe', 'UserManager.exe', 'ProfSvc.exe',
    'BITS.exe', 'ClipSVC.exe', 'ConsentUX.exe', 'CredentialManager.exe',
    'DeviceFlow.exe', 'DiagTrack.exe', 'DPS.exe', 'DsSvc.exe',
    'gpscript.exe', 'hidserv.exe', 'IKEEXT.exe', 'iphlpsvc.exe',
    'KeyIso.exe', 'KtmRm.exe', 'lfsvc.exe', 'LicenseManager.exe',
    'lmhsvc.exe', 'LSM.exe', 'MapsBroker.exe', 'msiexec.exe',
    'Netlogon.exe', 'Netman.exe', 'netprofm.exe', 'NgcCtnr.exe',
    'NgcSvc.exe', 'OneDrive.exe', 'PhoneSvc.exe', 'PowerMgr.exe',
    'PrintNotify.exe', 'QWAVE.exe', 'RpcEptMapper.exe', 'RpcLocator.exe',
    'SDWinJS.exe', 'SleepStudy.exe', 'Spooler.exe', 'spoolsv.exe',
    'SysMain.exe', 'SystemEventsBroker.exe', 'TabSvc.exe',
    'TapiSrv.exe', 'TermService.exe', 'TieringEngineService.exe',
    'TimeBrokerSvc.exe', 'TokenBroker.exe', 'TrustedInstaller.exe',
    'UI0Detect.exe', 'unsecapp.exe', 'VaultSvc.exe', 'vds.exe',
    'VSSVC.exe', 'W32Time.exe', 'WalletService.exe', 'wbengine.exe',
    'Wcmsvc.exe', 'wcncsvc.exe', 'wdi-host.exe', 'wdi-service.exe',
    'WerFault.exe', 'WerFaultSecure.exe', 'WinDefend.exe', 
    'WinHttpAutoProxySvc.exe', 'Winmgmt.exe', 'WinRM.exe',
    'wisvhsvc.exe', 'wlanext.exe', 'wlpasvc.exe', 'wlxss.exe',
    'wmpnetwk.exe', 'wsmsvc.exe', 'wuauserv.exe', 'wudfhost.exe',
    
    # Third-party Services
    'AVGIDSAgent.exe', 'AVGSEM08.exe', 'avgnsa.exe', 'avgnsx.exe',
    'avgwdsvc.exe', 'avp.exe', 'avpui.exe', 'McAfee.exe',
    'McUICnt.exe', 'mcapexe.exe', 'mpf.exe', 'mpfservice.exe',
    'mpftray.exe', 'Norton.exe', 'NortonLifeLock.exe', 'Kaspersky.exe',
    
    # Java and other common background processes
    'java.exe', 'javaw.exe', 'javafx.exe',
    'ApplicationFrameHost.exe', 'LockApp.exe', 'PeopleHub.exe',
    'DesktopBridge.exe'
}


class AnomalyDetector:
    """
    Rule-based anomaly detector for system monitoring.
    Detects abnormal behavior based on predefined thresholds and patterns.
    Now supports hybrid approach with ML confirmation.
    """
    
    def __init__(self):
        """Initialize the anomaly detector with default settings."""
        # History buffers for analysis
        self.cpu_history = deque(maxlen=config.HISTORY_SIZE)
        self.memory_history = deque(maxlen=config.HISTORY_SIZE)
        
        # Detection flags
        self.last_anomalies = []
        
        # ML detector reference (optional)
        self.ml_detector = None
    
    def set_ml_detector(self, ml_detector):
        """
        Set the ML detector for hybrid approach.
        
        Args:
            ml_detector: MLDetector instance
        """
        self.ml_detector = ml_detector
    
    def update_history(self, cpu_usage, memory_usage):
        """
        Update the history buffers with current readings.
        
        Args:
            cpu_usage: Current CPU usage percentage
            memory_usage: Current memory usage percentage
        """
        timestamp = time.time()
        self.cpu_history.append({
            'timestamp': timestamp,
            'value': cpu_usage
        })
        self.memory_history.append({
            'timestamp': timestamp,
            'value': memory_usage
        })
    
    def detect_cpu_spike(self):
        """Detect sudden CPU spike using rolling average."""
        if len(self.cpu_history) < 10:
            return None
        
        history_list = list(self.cpu_history)
        recent_avg = sum(h['value'] for h in history_list[-5:]) / 5
        previous_avg = sum(h['value'] for h in history_list[-10:-5]) / 5
        current = history_list[-1]['value']
        
        if current - previous_avg >= config.CPU_SPIKE_THRESHOLD:
            recent_high_count = sum(1 for h in history_list[-5:] if h['value'] >= config.CPU_WARNING_THRESHOLD)
            if recent_high_count >= 3:
                return {
                    'type': 'CPU Spike',
                    'severity': config.SEVERITY_HIGH,
                    'description': f"CPU usage significantly increased from {previous_avg:.1f}% to {current:.1f}% (sustained)",
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
                'description': f"CPU usage has been above {config.CPU_WARNING_THRESHOLD}% for {config.SUSTAINED_HIGH_COUNT} seconds (avg: {avg_usage:.1f}%)",
                'value': avg_usage
            }
        return None
    
    def detect_memory_spike(self):
        """Detect sudden memory spike."""
        if len(self.memory_history) < 2:
            return None
        
        history_list = list(self.memory_history)
        previous = history_list[-2]['value']
        current = history_list[-1]['value']
        
        if current - previous >= 20.0:
            return {
                'type': 'Memory Spike',
                'severity': config.SEVERITY_HIGH,
                'description': f"Memory usage suddenly increased from {previous:.1f}% to {current:.1f}%",
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
                'description': f"Memory usage has been above {config.MEMORY_WARNING_THRESHOLD}% for {config.SUSTAINED_HIGH_COUNT} seconds (avg: {avg_usage:.1f}%)",
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
    
    def detect_process_anomaly(self, process_info):
        """Detect if a specific process is behaving anomalously."""
        anomalies = []
        
        # Skip system processes
        process_name = process_info.get('name', '')
        if process_name in SYSTEM_PROCESS_NAMES:
            return None
        
        # Skip PID 0 (System Idle Process)
        if process_info.get('pid', -1) == 0:
            return None
        
        # Skip PID 4 (System process - shows aggregated CPU time)
        if process_info.get('pid', -1) == 4:
            return None
        
        # Skip processes with CPU > 100%
        cpu_percent = process_info.get('cpu_percent', 0)
        if cpu_percent > 100.0:
            return None
        
        # Check high CPU
        if cpu_percent >= config.PROCESS_HIGH_CPU_THRESHOLD:
            anomalies.append({
                'type': 'High CPU Process',
                'severity': config.SEVERITY_HIGH,
                'description': f"Process '{process_info['name']}' (PID: {process_info['pid']}) using high CPU: {cpu_percent:.1f}%",
                'process': process_info
            })
        
        # Check high memory
        memory_mb = process_info.get('memory_mb', 0)
        if memory_mb >= config.PROCESS_HIGH_MEMORY_THRESHOLD:
            anomalies.append({
                'type': 'High Memory Process',
                'severity': config.SEVERITY_HIGH,
                'description': f"Process '{process_info['name']}' (PID: {process_info['pid']}) using high memory: {memory_mb:.1f} MB",
                'process': process_info
            })
        
        # Check long-running high-resource process
        uptime_hours = process_info.get('uptime_hours', 0)
        if (uptime_hours >= config.PROCESS_LONG_RUNNING_HOURS and 
            (cpu_percent >= 10 or memory_mb >= 200)):
            anomalies.append({
                'type': 'Long-running Resource-intensive Process',
                'severity': config.SEVERITY_MEDIUM,
                'description': f"Process '{process_info['name']}' (PID: {process_info['pid']}) running for {uptime_hours:.1f} hours",
                'process': process_info
            })
        
        return anomalies if anomalies else None
    
    def _apply_ml_confirmation(self, anomaly: dict, disk_usage: float, process_count: int) -> dict:
        """Apply ML confirmation to an anomaly (hybrid approach)."""
        if self.ml_detector is None or not self.ml_detector.can_predict():
            return anomaly
        
        # Calculate std from history
        cpu_std = self._calculate_std(list(h['value'] for h in self.cpu_history)) if len(self.cpu_history) > 1 else 0
        memory_std = self._calculate_std(list(h['value'] for h in self.memory_history)) if len(self.memory_history) > 1 else 0
        
        # Get current values
        cpu_usage = self.cpu_history[-1]['value'] if self.cpu_history else 0
        memory_usage = self.memory_history[-1]['value'] if self.memory_history else 0
        
        # Get ML prediction
        ml_anomaly, ml_score, ml_explanation = self.ml_detector.predict(
            cpu_usage, memory_usage, disk_usage, process_count, cpu_std, memory_std
        )
        
        # Add ML info to anomaly
        anomaly['ml_confirmed'] = ml_anomaly
        anomaly['ml_score'] = ml_score
        anomaly['ml_explanation'] = ml_explanation
        
        # HYBRID LOGIC:
        if anomaly.get('severity') == config.SEVERITY_CRITICAL:
            pass  # Critical is always critical
        elif anomaly.get('severity') == config.SEVERITY_HIGH:
            if not ml_anomaly:
                anomaly['severity'] = config.SEVERITY_MEDIUM
                anomaly['description'] += " (ML: pattern appears normal)"
            elif ml_score > 70:
                anomaly['description'] += " (ML confirmed)"
        elif anomaly.get('severity') == config.SEVERITY_MEDIUM:
            if ml_anomaly and ml_score > 75:
                anomaly['severity'] = config.SEVERITY_HIGH
                anomaly['description'] += " (ML confirmed)"
        
        return anomaly
    
    def _calculate_std(self, values: list) -> float:
        """Calculate standard deviation."""
        if len(values) < 2:
            return 0.0
        mean = sum(values) / len(values)
        variance = sum((x - mean) ** 2 for x in values) / len(values)
        return variance ** 0.5
    
    def analyze_all(self, cpu_usage, memory_usage, process_list, disk_usage=0, process_count=None):
        """Perform comprehensive anomaly analysis on all metrics."""
        self.update_history(cpu_usage, memory_usage)
        
        if process_count is None:
            process_count = len(process_list) if process_list else 0
        
        anomalies = []
        
        # System-level detection - critical first
        critical = self.detect_critical_cpu()
        if critical:
            critical = self._apply_ml_confirmation(critical, disk_usage, process_count)
            anomalies.append(critical)
        
        critical = self.detect_critical_memory()
        if critical:
            critical = self._apply_ml_confirmation(critical, disk_usage, process_count)
            anomalies.append(critical)
        
        # Check for spikes
        spike = self.detect_cpu_spike()
        if spike:
            spike = self._apply_ml_confirmation(spike, disk_usage, process_count)
            anomalies.append(spike)
        
        spike = self.detect_memory_spike()
        if spike:
            spike = self._apply_ml_confirmation(spike, disk_usage, process_count)
            anomalies.append(spike)
        
        # Check for sustained high
        sustained = self.detect_sustained_high_cpu()
        if sustained:
            sustained = self._apply_ml_confirmation(sustained, disk_usage, process_count)
            anomalies.append(sustained)
        
        sustained = self.detect_sustained_high_memory()
        if sustained:
            sustained = self._apply_ml_confirmation(sustained, disk_usage, process_count)
            anomalies.append(sustained)
        
        # Process-level detection
        for process in process_list:
            if process.get('pid', 0) == 0:
                continue
            process_name = process.get('name', '')
            if process_name in SYSTEM_PROCESS_NAMES:
                continue
            
            process_anomaly = self.detect_process_anomaly(process)
            if process_anomaly:
                for pa in process_anomaly:
                    anomalies.append(pa)
        
        self.last_anomalies = anomalies
        return anomalies
    
    def calculate_health_score(self, cpu_usage, memory_usage, anomaly_count):
        """Calculate overall system health score (0-100)."""
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
        """Get health status label based on score."""
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
        """Get the last detected anomalies."""
        return self.last_anomalies

"""
Monitor Worker Module
Background thread for system monitoring to prevent UI blocking.
Uses QThread for Qt integration.
"""

from PySide6.QtCore import QThread, Signal
import time
import psutil
from datetime import datetime
import logging
import config

from monitor.cpu_monitor import CPUMonitor
from monitor.memory_monitor import MemoryMonitor
from monitor.disk_monitor import DiskMonitor
from monitor.process_monitor import ProcessMonitor
from analysis.anomaly_detector import AnomalyDetector
from analysis.ml_detector import get_ml_detector
from backend.database import get_database


class MonitorWorker(QThread):
    """
    Background worker thread for system monitoring.
    Emits signals with updated metrics to avoid UI blocking.
    """
    
    # Signals for UI updates
    metrics_updated = Signal(dict)  # Emits current metrics
    anomaly_detected = Signal(dict)  # Emits anomaly details
    error_occurred = Signal(str)  # Emits error message
    
    def __init__(self, refresh_interval=3):
        """
        Initialize the monitor worker.
        
        Args:
            refresh_interval: Seconds between metric updates
        """
        super().__init__()
        
        self.refresh_interval = refresh_interval
        self.running = False
        self.paused = False
        
        # Initialize monitors
        self.cpu_monitor = CPUMonitor(history_size=config.HISTORY_SIZE)
        self.memory_monitor = MemoryMonitor(history_size=config.HISTORY_SIZE)
        self.disk_monitor = DiskMonitor(history_size=config.HISTORY_SIZE)
        self.process_monitor = ProcessMonitor()
        
        # Initialize anomaly detector
        self.anomaly_detector = AnomalyDetector()
        
        # Initialize ML detector
        self.ml_detector = get_ml_detector()
        
        # Initialize database
        self.db = get_database()
        
        # Counters
        self.save_counter = 0
        self.save_interval = 5  # Save to DB every 5 readings
        self.ml_train_counter = 0
        self.ml_train_interval = 60  # Try to train ML every 60 readings (~3 minutes)
        
        # Rolling statistics for ML features
        self.cpu_history = []
        self.memory_history = []
        self.max_history = 30  # For calculating std dev
        
        # Logger
        self.logger = logging.getLogger('SystemObserver.Monitor')
        
        # Settings
        self.enable_ml_detection = True
        self.enable_anomaly_detection = True
    
    def run(self):
        """
        Main monitoring loop - runs in background thread.
        """
        self.running = True
        self.logger.info("Monitor worker started")
        
        # Initialize CPU measurement
        psutil.cpu_percent(interval=None)
        
        while self.running:
            try:
                if not self.paused:
                    # Collect all metrics
                    metrics = self._collect_metrics()
                    anomalies = []

                    # Analyze for anomalies before emitting metrics so UI gets fresh anomaly list
                    if self.enable_anomaly_detection:
                        anomalies = self._detect_anomalies(metrics)

                        # Emit anomaly signals
                        for anomaly in anomalies:
                            self.anomaly_detected.emit(anomaly)

                    # Update health score using current cycle anomalies
                    health_score = self.anomaly_detector.calculate_health_score(
                        metrics['cpu']['usage'],
                        metrics['memory']['usage'],
                        len(anomalies)
                    )
                    metrics['health_score'] = health_score
                    metrics['health_status'] = self.anomaly_detector.get_health_status(health_score)
                    metrics['anomalies'] = anomalies

                    # Emit metrics signal
                    self.metrics_updated.emit(metrics)
                    
                    # Save to database periodically
                    self._save_to_database(metrics)
                    
                    # Train ML model periodically
                    if self.enable_ml_detection:
                        self._train_ml_if_needed(metrics)
                
                # Sleep for refresh interval
                time.sleep(self.refresh_interval)
                
            except Exception as e:
                self.logger.error(f"Error in monitor loop: {e}")
                self.error_occurred.emit(str(e))
                time.sleep(1)  # Brief pause on error
        
        self.logger.info("Monitor worker stopped")
    
    def _collect_metrics(self) -> dict:
        """
        Collect all system metrics.
        
        Returns:
            Dictionary with all metrics
        """
        # Get current readings
        cpu_usage = self.cpu_monitor.record_reading()
        memory_usage = self.memory_monitor.record_reading()
        disk_usage = self.disk_monitor.record_reading()
        
        # Get process list (limited for performance)
        try:
            process_list = self.process_monitor.get_all_processes()
            process_count = len(process_list)
            
            # Get top processes
            top_cpu = self.process_monitor.get_top_processes_by_cpu(5)
            top_memory = self.process_monitor.get_top_processes_by_memory(5)
        except Exception as e:
            self.logger.error(f"Error getting processes: {e}")
            process_list = []
            process_count = 0
            top_cpu = []
            top_memory = []
        
        # Calculate rolling statistics for ML
        self.cpu_history.append(cpu_usage)
        self.memory_history.append(memory_usage)
        
        if len(self.cpu_history) > self.max_history:
            self.cpu_history.pop(0)
        if len(self.memory_history) > self.max_history:
            self.memory_history.pop(0)
        
        cpu_std = self._calculate_std(self.cpu_history)
        memory_std = self._calculate_std(self.memory_history)
        
        metrics = {
            'timestamp': datetime.now(),
            'cpu': {
                'usage': cpu_usage,
                'cores': self.cpu_monitor.get_cpu_count(),
                'average': self.cpu_monitor.get_average_usage(),
                'std': cpu_std
            },
            'memory': {
                'usage': memory_usage,
                'info': self.memory_monitor.get_memory_in_mb(),
                'average': self.memory_monitor.get_average_usage(),
                'std': memory_std
            },
            'disk': {
                'usage': disk_usage,
                'info': self.disk_monitor.get_disk_in_gb()
            },
            'processes': {
                'count': process_count,
                'top_cpu': top_cpu,
                'top_memory': top_memory,
                'summary': self.process_monitor.get_system_process_summary()
            },
            'health_score': 100.0,
            'health_status': 'Excellent',
            'ml_ready': self.ml_detector.can_predict(),
            'anomalies': []
        }
        
        return metrics
    
    def _calculate_std(self, values: list) -> float:
        """
        Calculate standard deviation of values.
        
        Args:
            values: List of numeric values
            
        Returns:
            Standard deviation
        """
        if len(values) < 2:
            return 0.0
        
        mean = sum(values) / len(values)
        variance = sum((x - mean) ** 2 for x in values) / len(values)
        return variance ** 0.5
    
    def _detect_anomalies(self, metrics: dict) -> list:
        """
        Detect anomalies using hybrid approach (rule-based + ML).
        
        Args:
            metrics: Current system metrics
            
        Returns:
            List of detected anomalies
        """
        cpu = metrics['cpu']['usage']
        memory = metrics['memory']['usage']
        process_list = metrics['processes']['top_cpu'] + metrics['processes']['top_memory']
        
        # Rule-based detection
        anomalies = self.anomaly_detector.analyze_all(
            cpu, memory, process_list
        )
        
        # ML-based detection (hybrid approach)
        if self.enable_ml_detection and self.ml_detector.can_predict():
            process_count = metrics['processes']['count']
            cpu_std = metrics['cpu']['std']
            memory_std = metrics['memory']['std']
            
            ml_anomaly, ml_score, ml_explanation = self.ml_detector.predict(
                cpu, memory, metrics['disk']['usage'],
                process_count, cpu_std, memory_std
            )
            
            # If ML detects anomaly but rule-based doesn't, 
            # we mark it as suspicious but not critical
            if ml_anomaly and not anomalies:
                # Check if it's a significant anomaly
                if ml_score > 70:
                    anomalies.append({
                        'type': 'ML Detected Anomaly',
                        'severity': config.SEVERITY_MEDIUM,
                        'description': f"{ml_explanation} (ML Score: {ml_score:.1f})",
                        'source': 'ML',
                        'ml_score': ml_score
                    })
        
        return anomalies
    
    def _save_to_database(self, metrics: dict):
        """
        Save metrics to database periodically.
        
        Args:
            metrics: Current metrics dictionary
        """
        self.save_counter += 1
        
        if self.save_counter >= self.save_interval:
            self.save_counter = 0
            
            try:
                self.db.insert_metrics(
                    metrics['cpu']['usage'],
                    metrics['memory']['usage'],
                    metrics['disk']['usage'],
                    metrics['processes']['count']
                )
                
                # Also add sample to ML detector
                if self.enable_ml_detection:
                    self.ml_detector.add_sample(
                        metrics['cpu']['usage'],
                        metrics['memory']['usage'],
                        metrics['disk']['usage'],
                        metrics['processes']['count'],
                        metrics['cpu']['std'],
                        metrics['memory']['std']
                    )
                    
            except Exception as e:
                self.logger.error(f"Error saving to database: {e}")
    
    def _train_ml_if_needed(self, metrics: dict):
        """
        Train ML model if enough data is available.
        
        Args:
            metrics: Current metrics dictionary
        """
        self.ml_train_counter += 1
        
        if self.ml_train_counter >= self.ml_train_interval:
            self.ml_train_counter = 0
            
            # Check if we should train
            if self.ml_detector.should_train():
                self.logger.info("Training ML model...")
                success = self.ml_detector.train()
                if success:
                    self.logger.info("ML model trained successfully")
                else:
                    self.logger.warning("ML model training failed or insufficient data")
    
    def pause(self):
        """Pause monitoring."""
        self.paused = True
        self.logger.info("Monitor paused")
    
    def resume(self):
        """Resume monitoring."""
        self.paused = False
        self.logger.info("Monitor resumed")
    
    def stop(self):
        """Stop the monitoring thread."""
        self.running = False
        self.logger.info("Monitor stopping...")
    
    def update_settings(self, settings: dict):
        """
        Update worker settings.
        
        Args:
            settings: Dictionary of settings
        """
        if 'enable_monitoring' in settings:
            if settings['enable_monitoring']:
                self.resume()
            else:
                self.pause()
        
        if 'enable_anomaly_detection' in settings:
            self.enable_anomaly_detection = settings['enable_anomaly_detection']
        
        if 'enable_ml_detection' in settings:
            self.enable_ml_detection = settings['enable_ml_detection']
        
        if 'refresh_interval' in settings:
            self.refresh_interval = settings['refresh_interval']
        
        if 'alert_cooldown_seconds' in settings:
            # Update will be handled by AlertManager
            pass
    
    def get_ml_stats(self) -> dict:
        """
        Get ML detector statistics.
        
        Returns:
            Dictionary with ML stats
        """
        return self.ml_detector.get_training_stats()


# Module-level instance
_monitor_worker = None


def get_monitor_worker(refresh_interval=3) -> MonitorWorker:
    """
    Get the singleton monitor worker instance.
    
    Args:
        refresh_interval: Seconds between updates
        
    Returns:
        MonitorWorker instance
    """
    global _monitor_worker
    if _monitor_worker is None:
        _monitor_worker = MonitorWorker(refresh_interval)
    return _monitor_worker

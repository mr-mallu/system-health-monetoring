"""
Configuration file for System Health Monitoring
Contains all configuration settings and thresholds for the monitoring system.
"""

import os

# Application identity
APP_NAME = "System Health Monitoring"
VERSION = "2.0.0"
AUTHOR = "Mallikarjun"

# Project paths
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, "data")
LOGS_DIR = os.path.join(BASE_DIR, "logs")
LOG_FILE = os.path.join(LOGS_DIR, "system.log")

# Database
DB_NAME = os.path.join("data", "system_observer.db")

# Ensure logs directory exists
os.makedirs(DATA_DIR, exist_ok=True)
os.makedirs(LOGS_DIR, exist_ok=True)

# Refresh interval for metrics (in seconds)
REFRESH_INTERVAL = 3

# CPU thresholds (percentage)
CPU_WARNING_THRESHOLD = 70.0
CPU_CRITICAL_THRESHOLD = 90.0
CPU_SPIKE_THRESHOLD = 30.0  # Sudden increase threshold

# Memory thresholds (percentage)
MEMORY_WARNING_THRESHOLD = 70.0
MEMORY_CRITICAL_THRESHOLD = 90.0

# Disk thresholds (percentage)
DISK_WARNING_THRESHOLD = 80.0
DISK_CRITICAL_THRESHOLD = 95.0

# Process thresholds
PROCESS_HIGH_CPU_THRESHOLD = 50.0  # High CPU usage percentage
PROCESS_HIGH_MEMORY_THRESHOLD = 500  # High memory in MB (or percentage threshold)
PROCESS_LONG_RUNNING_HOURS = 24  # Hours to consider a process as long-running

# Anomaly detection settings
HISTORY_SIZE = 60  # Number of data points to keep for history (60 seconds)
SUSTAINED_HIGH_COUNT = 10  # Count of consecutive high readings to detect sustained usage

# Health score weights
CPU_WEIGHT = 0.35
MEMORY_WEIGHT = 0.35
ANOMALY_WEIGHT = 0.30

# Alert severity levels
SEVERITY_LOW = "Low"
SEVERITY_MEDIUM = "Medium"
SEVERITY_HIGH = "High"
SEVERITY_CRITICAL = "Critical"

# ML-based anomaly detection settings
ML_CONTAMINATION = 0.1  # Expected proportion of anomalies (0.0-0.5)
ML_N_ESTIMATORS = 100  # Number of isolation trees
ML_MIN_SAMPLES = 60  # Minimum samples needed before training
ML_RETRAIN_INTERVAL = 300  # Seconds between retraining attempts

# Alert cooldown settings (in seconds)
ALERT_COOLDOWN_DEFAULT = 300  # 5 minutes default cooldown
ALERT_COOLDOWN_MIN = 60  # 1 minute minimum
ALERT_COOLDOWN_MAX = 1800  # 30 minutes maximum

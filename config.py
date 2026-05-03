"""
Configuration — System Health Monitoring
All thresholds, paths, and tunables live here.
"""

import os

# Optional: load .env overrides (python-dotenv is not required)
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass


# ---------------------------------------------------------------------------
# Application identity
# ---------------------------------------------------------------------------
APP_NAME = "System Health Monitoring"
VERSION = "2.0.0"
AUTHOR = "Mallikarjun"


# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, "data")
LOGS_DIR = os.environ.get("SYSTEM_OBSERVER_LOG_DIR", os.path.join(BASE_DIR, "logs"))
LOG_FILE = os.path.join(LOGS_DIR, "system.log")

DB_NAME = os.path.join("data", "system_observer.db")

# Ensure runtime directories exist
os.makedirs(DATA_DIR, exist_ok=True)
os.makedirs(LOGS_DIR, exist_ok=True)


# ---------------------------------------------------------------------------
# Monitoring
# ---------------------------------------------------------------------------
REFRESH_INTERVAL = 3  # Seconds between metric updates


# ---------------------------------------------------------------------------
# CPU thresholds (percentage)
# ---------------------------------------------------------------------------
CPU_WARNING_THRESHOLD = 70.0
CPU_CRITICAL_THRESHOLD = 90.0
CPU_SPIKE_THRESHOLD = 30.0  # Minimum jump to flag as a spike


# ---------------------------------------------------------------------------
# Memory thresholds (percentage)
# ---------------------------------------------------------------------------
MEMORY_WARNING_THRESHOLD = 70.0
MEMORY_CRITICAL_THRESHOLD = 90.0


# ---------------------------------------------------------------------------
# Disk thresholds (percentage)
# ---------------------------------------------------------------------------
DISK_WARNING_THRESHOLD = 80.0
DISK_CRITICAL_THRESHOLD = 95.0


# ---------------------------------------------------------------------------
# Process thresholds
# ---------------------------------------------------------------------------
PROCESS_HIGH_CPU_THRESHOLD = 50.0       # Per-process CPU warning
PROCESS_HIGH_MEMORY_THRESHOLD = 500     # Per-process memory in MB
PROCESS_LONG_RUNNING_HOURS = 24         # Hours before flagging as long-running


# ---------------------------------------------------------------------------
# Anomaly detection
# ---------------------------------------------------------------------------
HISTORY_SIZE = 60              # Rolling history buffer length
SUSTAINED_HIGH_COUNT = 10      # Consecutive readings to confirm sustained usage


# ---------------------------------------------------------------------------
# Health score weights (must sum to 1.0)
# ---------------------------------------------------------------------------
CPU_WEIGHT = 0.35
MEMORY_WEIGHT = 0.35
ANOMALY_WEIGHT = 0.30


# ---------------------------------------------------------------------------
# Alert severity labels
# ---------------------------------------------------------------------------
SEVERITY_LOW = "Low"
SEVERITY_MEDIUM = "Medium"
SEVERITY_HIGH = "High"
SEVERITY_CRITICAL = "Critical"


# ---------------------------------------------------------------------------
# ML-based anomaly detection (Isolation Forest)
# ---------------------------------------------------------------------------
ML_CONTAMINATION = 0.1         # Expected anomaly proportion (0.0–0.5)
ML_N_ESTIMATORS = 100          # Number of isolation trees
ML_MIN_SAMPLES = 60            # Minimum samples before first training
ML_RETRAIN_INTERVAL = 300      # Seconds between retraining attempts


# ---------------------------------------------------------------------------
# Alert cooldown (seconds) — prevents repeated popups for the same issue
# ---------------------------------------------------------------------------
ALERT_COOLDOWN_DEFAULT = 300   # 5 minutes
ALERT_COOLDOWN_MIN = 60        # 1 minute
ALERT_COOLDOWN_MAX = 1800      # 30 minutes

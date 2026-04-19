# 🖥️ System Health Monitoring

**Intelligent Desktop System Observability and Anomaly Response Tool**

> A real-time desktop application that monitors CPU, memory, disk, and process activity — detects anomalies using rule-based and ML algorithms — and presents actionable insights through a professional dashboard.

| | |
|---|---|
| **Version** | 2.0.0 |
| **Author** | Mallikarjun |
| **Project** | Final Year BCA Project, 2026 |
| **Platform** | Windows (Python 3.8+) |
| **UI** | PySide6 (Qt 6) |

---

## ✨ Features

### Core Monitoring
- **Real-time CPU, Memory & Disk tracking** with configurable thresholds
- **Process monitoring** — top CPU/memory consumers, uptime, simulated termination
- **Rule-based anomaly detection** — threshold breaches, spike detection, sustained high usage
- **ML-based anomaly detection** — Isolation Forest (unsupervised learning) for pattern-based alerts
- **Alert management** — popup notifications, severity levels, cooldown control, acknowledgement

### Advanced Features
| # | Feature | Description |
|---|---------|-------------|
| 1 | **Performance Cause Explanation** | Identifies *which* process is causing slowdowns and explains why |
| 2 | **Smart Suggestions Engine** | Context-aware recommendations based on current system state |
| 3 | **Diagnostic Report Generator** | Professional PDF reports with metrics, graphs, anomalies & alerts |
| 4 | **Daily System Summary** | Peak/average statistics, alert counts, and health trends |
| 5 | **Real-time Graph Dashboard** | Live CPU, Memory & Health Score graphs (pyqtgraph / matplotlib) |
| 6 | **Startup Impact Analyzer** | Identifies startup programs by impact level; supports disabling |

### Additional Capabilities
- 🎨 **Dark / Light theme** with premium toggle switches in settings
- 📝 **Admin Notes** — CRUD diagnostic notes stored in SQLite
- 🧹 **Cache Cleanup Scanner** — identifies safe-to-clean temp files
- 📊 **History View** — browse past metrics with time-range filters
- 📈 **Health Score** — weighted composite score (CPU + Memory + Anomalies)

---

## 📁 Project Structure

```
system-health-monitoring/
├── main.py .......................... Application entry point
├── config.py ........................ Configuration & thresholds
├── requirements.txt ................. Python dependencies
├── run_app.bat ...................... Quick launcher (Windows)
│
├── monitor/ ......................... Data collection layer
│   ├── cpu_monitor.py
│   ├── memory_monitor.py
│   ├── disk_monitor.py
│   └── process_monitor.py
│
├── analysis/ ........................ Intelligence layer
│   ├── anomaly_detector.py .......... Rule-based detection
│   ├── ml_detector.py ............... Isolation Forest ML
│   ├── performance_analyzer.py ...... Root-cause analysis
│   └── suggestions_engine.py ....... Smart recommendations
│
├── backend/ ......................... Services layer
│   ├── database.py .................. SQLite operations (singleton)
│   ├── monitor_worker.py ............ Background QThread worker
│   ├── report_generator.py .......... PDF report generation
│   ├── daily_summary.py ............. 24-hour statistics
│   ├── startup_checker.py ........... Startup program analyzer
│   └── cache_cleaner.py ............. Temp file scanner
│
├── ui/ .............................. Presentation layer
│   ├── main_window.py ............... Main GUI window
│   ├── graph_dashboard.py ........... Live metric graphs
│   ├── suggestions_view.py .......... Startup & cache UI
│   ├── history_view.py .............. Historical data browser
│   ├── settings_view.py ............. Settings with toggle switches
│   └── notes_view.py ................ Admin notes CRUD
│
├── alerts/
│   └── alert_manager.py ............. Desktop alert system
│
├── themes/
│   ├── dark.qss ..................... Dark theme stylesheet
│   └── light.qss ................... Light theme stylesheet
│
├── data/
│   ├── system_observer.db ........... SQLite database (auto-created)
│   └── reports/ ..................... Generated PDF reports
│
├── logs/
│   └── system.log ................... Rotating application log
│
├── docs/ ............................ Documentation
│   ├── PROJECT_OVERVIEW.md
│   ├── FEATURES.md
│   ├── CODE_SNIPPETS.md
│   ├── QUICK_START.md
│   ├── TROUBLESHOOTING.md
│   ├── TODO.md
│   └── UPGRADE_SUMMARY.md
│
├── tests/ ........................... Test suite
│   ├── test_imports.py
│   ├── test_db.py
│   ├── test_filter.py
│   └── verify_app.py
│
└── scripts/
    └── run_app.bat .................. Launcher script
```

---

## 🚀 Quick Start

### Prerequisites
- **Python 3.8+** (tested on Python 3.14)
- **Windows OS** (uses Windows-specific process/startup APIs)

### Installation

```bash
# 1. Clone or download the project
cd system-health-monitoring

# 2. Install dependencies
pip install -r requirements.txt
```

### Running the Application

```bash
# Option A: Command line
python main.py

# Option B: Double-click launcher (Windows)
run_app.bat
```

---

## 🛠️ Technology Stack

| Technology | Purpose |
|------------|---------|
| **Python 3** | Core language |
| **PySide6** | Desktop GUI (Qt 6 bindings) |
| **psutil** | System metrics collection |
| **scikit-learn** | ML anomaly detection (Isolation Forest) |
| **pyqtgraph** | High-performance live graphs |
| **matplotlib** | Fallback graph rendering |
| **SQLite** | Local database for metrics, alerts, settings, notes |

---

## 📋 Requirements

```
PySide6>=6.10.0
psutil>=5.9.0
scikit-learn>=1.3.0
pyqtgraph>=0.12.0
matplotlib>=3.5.0
```

---

## 🔧 Configuration

All thresholds and settings are centralized in `config.py`:

| Setting | Default | Description |
|---------|---------|-------------|
| `REFRESH_INTERVAL` | 3s | Metrics polling interval |
| `CPU_WARNING_THRESHOLD` | 70% | CPU warning level |
| `CPU_CRITICAL_THRESHOLD` | 90% | CPU critical level |
| `MEMORY_WARNING_THRESHOLD` | 70% | RAM warning level |
| `DISK_WARNING_THRESHOLD` | 80% | Disk warning level |
| `ALERT_COOLDOWN_DEFAULT` | 300s | Minimum gap between repeated alerts |

Settings can also be modified live through the **Settings** tab in the application.

---

## 🐛 Troubleshooting

| Problem | Solution |
|---------|----------|
| `ModuleNotFoundError` | Run `pip install -r requirements.txt` |
| Graphs not displaying | Install `pyqtgraph` or `matplotlib` |
| Reports failing | Ensure `data/reports/` directory is writable |
| High CPU from the app itself | Increase `REFRESH_INTERVAL` in config.py |

See [TROUBLESHOOTING.md](docs/TROUBLESHOOTING.md) for more.

---

## 📄 License

This project is an academic submission for the BCA Final Year Project, 2026.

---

*Built with ❤️ by Mallikarjun*

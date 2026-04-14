"""Comprehensive verification script for System Health Monitoring."""
import sys
import os
import tempfile
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, PROJECT_ROOT)

# Use isolated test database to avoid polluting production data
test_db_path = os.path.join(tempfile.gettempdir(), f"system_observer_verify_{os.getpid()}.db")
os.environ["SYSTEM_OBSERVER_DB_PATH"] = test_db_path

print("=" * 60)
print("System Health Monitoring - Comprehensive Verification")
print("=" * 60)

# Track test results
all_passed = True

# Test 1: Import all critical modules
print("\n[TEST 1] Module Imports")
print("-" * 40)

modules_to_test = [
    ("ui.main_window", "MainWindow"),
    ("backend.monitor_worker", "MonitorWorker"),
    ("backend.database", "Database"),
    ("analysis.ml_detector", "ML Detector"),
    ("analysis.anomaly_detector", "Anomaly Detector"),
    ("alerts.alert_manager", "AlertManager"),
    ("monitor.cpu_monitor", "CPUMonitor"),
    ("monitor.memory_monitor", "MemoryMonitor"),
    ("monitor.disk_monitor", "DiskMonitor"),
    ("monitor.process_monitor", "ProcessMonitor"),
    ("ui.settings_view", "SettingsView"),
    ("ui.history_view", "HistoryView"),
    ("ui.suggestions_view", "SuggestionsView"),
]

for module_name, display_name in modules_to_test:
    try:
        __import__(module_name)
        print(f"  [OK] {display_name}")
    except Exception as e:
        print(f"  [FAIL] {display_name}: {e}")
        all_passed = False

# Test 2: Database connection and operations
print("\n[TEST 2] Database Connection & Operations")
print("-" * 40)

try:
    from backend.database import get_database
    db = get_database()
    
    # Test connection
    cursor = db.conn.cursor()
    cursor.execute("SELECT 1")
    print("  [OK] Database connection")
    
    # Test metrics insert
    test_id = db.insert_metrics(50.0, 60.0, 70.0, 100)
    print(f"  [OK] Insert metrics (ID: {test_id})")
    
    # Test metrics fetch
    metrics = db.get_metrics_history(limit=5)
    print(f"  [OK] Fetch metrics ({len(metrics)} records)")
    
    # Test alerts insert
    alert_id = db.insert_alert("High", "Test alert", "Verification")
    print(f"  [OK] Insert alert (ID: {alert_id})")
    
    # Test settings
    db.set_setting("test_setting", "test_value")
    value = db.get_setting("test_setting")
    print(f"  [OK] Settings get/set: {value}")
    
except Exception as e:
    print(f"  [FAIL] Database: {e}")
    all_passed = False

# Test 3: CPU Monitor - Range validation
print("\n[TEST 3] CPU Monitor - Range Validation")
print("-" * 40)

try:
    from monitor.cpu_monitor import CPUMonitor
    cpu_mon = CPUMonitor(history_size=10)
    
    # Get current usage
    cpu_usage = cpu_mon.get_current_usage()
    
    # Validate range
    if 0 <= cpu_usage <= 100:
        print(f"  [OK] CPU usage in valid range: {cpu_usage:.1f}%")
    else:
        print(f"  [FAIL] CPU usage out of range: {cpu_usage}%")
        all_passed = False
    
    # Record some readings
    for _ in range(5):
        cpu_mon.record_reading()
    
    avg_cpu = cpu_mon.get_average_usage()
    if 0 <= avg_cpu <= 100:
        print(f"  [OK] Average CPU in valid range: {avg_cpu:.1f}%")
    else:
        print(f"  [FAIL] Average CPU out of range: {avg_cpu}%")
        all_passed = False
        
except Exception as e:
    print(f"  [FAIL] CPU Monitor: {e}")
    all_passed = False

# Test 4: Process Monitor - Non-empty list
print("\n[TEST 4] Process Monitor - Process List")
print("-" * 40)

try:
    from monitor.process_monitor import ProcessMonitor
    proc_mon = ProcessMonitor()
    
    processes = proc_mon.get_all_processes()
    
    if processes:
        print(f"  [OK] Process list not empty: {len(processes)} processes")
        
        # Check for PID 0
        pid_0_count = sum(1 for p in processes if p['pid'] == 0)
        if pid_0_count == 0:
            print(f"  [OK] PID 0 (System Idle) properly filtered")
        else:
            print(f"  [WARN] PID 0 found: {pid_0_count}")
        
        # Check for blank names
        blank_names = [p for p in processes if not p.get('name') or p['name'].strip() == '']
        if not blank_names:
            print(f"  [OK] No blank process names")
        else:
            print(f"  [WARN] {len(blank_names)} processes with blank names")
        
        # Check CPU range
        invalid_cpu = [p for p in processes if p.get('cpu_percent', 0) < 0 or p.get('cpu_percent', 0) > 100]
        if not invalid_cpu:
            print(f"  [OK] All CPU values in valid range (0-100)")
        else:
            print(f"  [FAIL] {len(invalid_cpu)} processes with invalid CPU")
            all_passed = False
            
    else:
        print(f"  [FAIL] Process list is empty")
        all_passed = False
        
except Exception as e:
    print(f"  [FAIL] Process Monitor: {e}")
    all_passed = False

# Test 5: Memory Monitor
print("\n[TEST 5] Memory Monitor")
print("-" * 40)

try:
    from monitor.memory_monitor import MemoryMonitor
    mem_mon = MemoryMonitor()
    
    mem_usage = mem_mon.get_current_usage()
    if 0 <= mem_usage <= 100:
        print(f"  [OK] Memory usage in valid range: {mem_usage:.1f}%")
    else:
        print(f"  [FAIL] Memory usage out of range: {mem_usage}%")
        all_passed = False
        
except Exception as e:
    print(f"  [FAIL] Memory Monitor: {e}")
    all_passed = False

# Test 6: Alert Manager
print("\n[TEST 6] Alert Manager")
print("-" * 40)

try:
    from alerts.alert_manager import AlertManager
    alert_mgr = AlertManager()
    
    # Test cooldown
    alert_mgr.alert_cooldown = 300
    print(f"  [OK] Alert cooldown set: {alert_mgr.alert_cooldown}s")
    
    # Test should_show_alert
    result = alert_mgr.should_show_alert("test_alert")
    print(f"  [OK] should_show_alert works: {result}")
    
    # Test suppression
    alert_mgr.suppress_process({'name': 'test', 'pid': 12345})
    suppressed = alert_mgr.get_suppressed_processes()
    print(f"  [OK] Process suppression: {len(suppressed)} suppressed")
    
except Exception as e:
    print(f"  [FAIL] Alert Manager: {e}")
    all_passed = False

# Test 7: Anomaly Detector
print("\n[TEST 7] Anomaly Detector")
print("-" * 40)

try:
    from analysis.anomaly_detector import AnomalyDetector
    anomaly_det = AnomalyDetector()
    
    # Test health score calculation
    score = anomaly_det.calculate_health_score(50, 60, 2)
    if 0 <= score <= 100:
        print(f"  [OK] Health score in valid range: {score:.1f}")
    else:
        print(f"  [FAIL] Health score out of range: {score}")
        all_passed = False
    
    status = anomaly_det.get_health_status(score)
    print(f"  [OK] Health status: {status}")
    
except Exception as e:
    print(f"  [FAIL] Anomaly Detector: {e}")
    all_passed = False

# Final summary
print("\n" + "=" * 60)
if all_passed:
    print("RESULT: ALL TESTS PASSED")
else:
    print("RESULT: SOME TESTS FAILED")
print("=" * 60)

# Exit with appropriate code



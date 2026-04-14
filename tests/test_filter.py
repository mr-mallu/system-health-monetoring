"""
Test script to verify system process filtering is working correctly.
"""
import sys
import os

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, PROJECT_ROOT)

from monitor.process_monitor import ProcessMonitor
from analysis.anomaly_detector import AnomalyDetector

def main():
    output = []
    
    output.append("=" * 60)
    output.append("Testing System Process Filtering")
    output.append("=" * 60)
    
    # Test process monitor
    pm = ProcessMonitor()
    processes = pm.get_all_processes()
    
    output.append("\n[Process Monitor Test]")
    output.append(f"Total processes returned: {len(processes)}")
    
    # Check if PID 0 is in the list
    pid_0_found = any(p['pid'] == 0 for p in processes)
    output.append(f"PID 0 (System Idle Process) in list: {pid_0_found}")
    
    # Check for system processes being flagged
    system_procs = [p for p in processes if p.get('is_system_process', False)]
    output.append(f"System processes flagged: {len(system_procs)}")
    
    # Test high CPU processes
    high_cpu = pm.get_high_cpu_processes()
    output.append(f"\nHigh CPU processes (excluding PID 0): {len(high_cpu)}")
    for p in high_cpu[:5]:
        output.append(f"  - {p['name']} (PID: {p['pid']}) CPU: {p['cpu_percent']:.1f}%")
    
    # Test anomaly detector
    output.append("\n[Anomaly Detector Test]")
    ad = AnomalyDetector()
    
    # Add some history for the detector
    for i in range(15):
        ad.update_history(50.0 + i, 60.0)
    
    anomalies = ad.analyze_all(50.0, 60.0, processes)
    output.append(f"Anomalies detected: {len(anomalies)}")
    
    for a in anomalies:
        output.append(f"  - {a['type']}: {a.get('description', 'N/A')[:60]}")
    
    output.append("\n" + "=" * 60)
    output.append("TEST COMPLETE")
    output.append("=" * 60)
    
    # Write to file
    output_path = os.path.join(PROJECT_ROOT, 'tests', 'test_output.txt')
    with open(output_path, 'w') as f:
        f.write('\n'.join(output))
    
    print('\n'.join(output))

if __name__ == "__main__":
    main()

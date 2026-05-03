"""
Database Module
SQLite database management for System Health Monitoring.
Provides modular and reusable database operations.
"""

import sqlite3
import os
import logging
from datetime import datetime
from typing import List, Dict, Optional, Any
import config

logger = logging.getLogger(__name__)


class Database:
    """
    Centralized database manager for System Health Monitoring.
    Handles all SQLite operations with connection pooling.
    """
    
    _instance = None
    
    def __new__(cls):
        """Singleton pattern for database connection."""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        """Initialize database connection and create tables."""
        if self._initialized:
            return
            
        # Database path (supports override for tests)
        self.db_path = os.getenv("SYSTEM_OBSERVER_DB_PATH")
        if not self.db_path:
            self.db_path = os.path.join(config.BASE_DIR, config.DB_NAME)
            legacy_db_path = os.path.join(config.BASE_DIR, "system_observer.db")
            if not os.path.exists(self.db_path) and os.path.exists(legacy_db_path):
                self.db_path = legacy_db_path
        
        # Create connection
        self.conn = None
        self._connect()
        
        # Create tables
        self._create_tables()
        
        self._initialized = True
    
    def _connect(self):
        """Establish database connection."""
        try:
            self.conn = sqlite3.connect(self.db_path, check_same_thread=False)
            self.conn.row_factory = sqlite3.Row  # Enable column access by name
            # Enable foreign keys
            self.conn.execute("PRAGMA foreign_keys = ON")
        except sqlite3.Error as e:
            logger.error("Database connection error: %s", e)
            raise
    
    def _create_tables(self):
        """Create all required database tables."""
        cursor = self.conn.cursor()
        
        # System Metrics Table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS system_metrics (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                cpu_usage REAL NOT NULL,
                memory_usage REAL NOT NULL,
                disk_usage REAL NOT NULL,
                process_count INTEGER DEFAULT 0
            )
        """)
        
        # Alerts Table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS alerts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                severity TEXT NOT NULL,
                message TEXT NOT NULL,
                source TEXT,
                acknowledged INTEGER DEFAULT 0
            )
        """)
        
        # User Settings Table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS user_settings (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                feature TEXT UNIQUE NOT NULL,
                enabled INTEGER DEFAULT 1,
                value TEXT,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Process History Table (for analysis)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS process_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                pid INTEGER NOT NULL,
                process_name TEXT NOT NULL,
                cpu_percent REAL,
                memory_mb REAL,
                memory_percent REAL
            )
        """)
        
        # Admin Notes Table (Custom Diagnostics Notes CRUD)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS admin_notes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                target_date TEXT NOT NULL,
                note_text TEXT NOT NULL
            )
        """)
        
        # Create indexes for better query performance
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_metrics_timestamp 
            ON system_metrics(timestamp)
        """)
        
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_alerts_timestamp 
            ON alerts(timestamp)
        """)
        
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_alerts_severity 
            ON alerts(severity)
        """)
        
        self.conn.commit()
        
        # Initialize default settings if not exist
        self._initialize_default_settings()
    
    def _initialize_default_settings(self):
        """Initialize default user settings."""
        default_settings = {
            'enable_monitoring': True,
            'enable_anomaly_detection': True,
            'enable_popup_alerts': True,
            'enable_tray_notifications': True,
            'enable_startup_suggestions': True,
            'enable_cache_cleanup_suggestions': True,
            'alert_cooldown_seconds': config.ALERT_COOLDOWN_DEFAULT,
            'refresh_interval': 1,
            'theme': 'dark'
        }
        
        for feature, default_value in default_settings.items():
            self.set_setting(feature, default_value)
    
    # ==================== System Metrics Operations ====================
    
    def insert_metrics(self, cpu_usage: float, memory_usage: float, 
                       disk_usage: float, process_count: int = 0) -> int:
        """
        Insert system metrics record.
        
        Args:
            cpu_usage: CPU usage percentage
            memory_usage: Memory usage percentage
            disk_usage: Disk usage percentage
            process_count: Number of running processes
            
        Returns:
            int: Row ID of inserted record
        """
        cursor = self.conn.cursor()
        # Store local timestamps so history filters (which use datetime.now()) match
        local_ts = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        cursor.execute("""
            INSERT INTO system_metrics (timestamp, cpu_usage, memory_usage, disk_usage, process_count)
            VALUES (?, ?, ?, ?, ?)
        """, (local_ts, cpu_usage, memory_usage, disk_usage, process_count))
        self.conn.commit()
        return cursor.lastrowid
    
    def get_metrics_history(self, limit: int = 60, 
                          start_time: Optional[str] = None) -> List[Dict]:
        """
        Get system metrics history.
        
        Args:
            limit: Maximum number of records to return
            start_time: Optional start time filter (ISO format string)
            
        Returns:
            List of metric records as dictionaries
        """
        cursor = self.conn.cursor()
        
        if start_time:
            # Convert ISO format to SQLite datetime format for comparison
            if isinstance(start_time, datetime):
                start_time = start_time.isoformat()
            
            # Convert ISO format to SQLite datetime format for comparison
            start_time_formatted = start_time.replace('T', ' ')
            # If it has microseconds, truncate to seconds
            if '.' in start_time_formatted:
                start_time_formatted = start_time_formatted.split('.')[0]
            
            cursor.execute("""
                SELECT * FROM system_metrics
                WHERE datetime(timestamp) >= datetime(?)
                ORDER BY timestamp DESC
                LIMIT ?
            """, (start_time_formatted, limit))
        else:
            cursor.execute("""
                SELECT * FROM system_metrics
                ORDER BY timestamp DESC
                LIMIT ?
            """, (limit,))
        
        return [dict(row) for row in cursor.fetchall()]
    
    def get_average_metrics(self, last_n: int = 60) -> Dict:
        """
        Calculate average metrics over last N records.
        
        Args:
            last_n: Number of recent records to average
            
        Returns:
            Dictionary with average values
        """
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT 
                AVG(cpu_usage) as avg_cpu,
                AVG(memory_usage) as avg_memory,
                AVG(disk_usage) as avg_disk,
                AVG(process_count) as avg_processes
            FROM (
                SELECT * FROM system_metrics
                ORDER BY timestamp DESC
                LIMIT ?
            )
        """, (last_n,))
        
        row = cursor.fetchone()
        return {
            'avg_cpu': row['avg_cpu'] or 0,
            'avg_memory': row['avg_memory'] or 0,
            'avg_disk': row['avg_disk'] or 0,
            'avg_processes': row['avg_processes'] or 0
        }
    
    def get_metrics_range(self, start_time: str, end_time: str) -> List[Dict]:
        """
        Get metrics within a time range.
        
        Args:
            start_time: Start time (ISO format)
            end_time: End time (ISO format)
            
        Returns:
            List of metric records
        """
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT * FROM system_metrics
            WHERE timestamp BETWEEN ? AND ?
            ORDER BY timestamp ASC
        """, (start_time, end_time))
        
        return [dict(row) for row in cursor.fetchall()]
    
    # ==================== Alert Operations ====================
    
    def insert_alert(self, severity: str, message: str, source: str = None) -> int:
        """
        Insert an alert record.
        
        Args:
            severity: Alert severity (Low/Medium/High/Critical)
            message: Alert message
            source: Source of the alert
            
        Returns:
            int: Row ID of inserted record
        """
        cursor = self.conn.cursor()
        # Also store local timestamp for alerts
        local_ts = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        cursor.execute("""
            INSERT INTO alerts (timestamp, severity, message, source)
            VALUES (?, ?, ?, ?)
        """, (local_ts, severity, message, source))
        self.conn.commit()
        return cursor.lastrowid
    
    def get_alerts(self, limit: int = 100, 
                   severity: Optional[str] = None) -> List[Dict]:
        """
        Get alert history.
        
        Args:
            limit: Maximum number of records
            severity: Optional severity filter
            
        Returns:
            List of alert records
        """
        cursor = self.conn.cursor()
        
        if severity:
            cursor.execute("""
                SELECT * FROM alerts
                WHERE severity = ?
                ORDER BY timestamp DESC
                LIMIT ?
            """, (severity, limit))
        else:
            cursor.execute("""
                SELECT * FROM alerts
                ORDER BY timestamp DESC
                LIMIT ?
            """, (limit,))
        
        return [dict(row) for row in cursor.fetchall()]
    
    def acknowledge_alert(self, alert_id: int) -> bool:
        """
        Mark an alert as acknowledged.
        
        Args:
            alert_id: ID of alert to acknowledge
            
        Returns:
            bool: True if successful
        """
        cursor = self.conn.cursor()
        cursor.execute("""
            UPDATE alerts
            SET acknowledged = 1
            WHERE id = ?
        """, (alert_id,))
        self.conn.commit()
        return cursor.rowcount > 0
    
    def clear_alerts(self) -> int:
        """
        Clear all alerts.
        
        Returns:
            int: Number of records deleted
        """
        cursor = self.conn.cursor()
        cursor.execute("DELETE FROM alerts")
        self.conn.commit()
        return cursor.rowcount
    
    def get_alert_count_by_severity(self) -> Dict:
        """
        Get count of alerts grouped by severity.
        
        Returns:
            Dictionary with severity counts
        """
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT severity, COUNT(*) as count
            FROM alerts
            GROUP BY severity
        """)
        
        result = {'Low': 0, 'Medium': 0, 'High': 0, 'Critical': 0}
        for row in cursor.fetchall():
            result[row['severity']] = row['count']
        
        return result
    
    # ==================== User Settings Operations ====================
    
    def set_setting(self, feature: str, value: Any) -> bool:
        """
        Set a user setting.
        
        Args:
            feature: Setting name
            value: Setting value
            
        Returns:
            bool: True if successful
        """
        cursor = self.conn.cursor()
        
        # Convert boolean to int for storage
        if isinstance(value, bool):
            value = 1 if value else 0
        
        cursor.execute("""
            INSERT INTO user_settings (feature, value, updated_at)
            VALUES (?, ?, CURRENT_TIMESTAMP)
            ON CONFLICT(feature) DO UPDATE SET
                value = excluded.value,
                updated_at = CURRENT_TIMESTAMP
        """, (feature, str(value)))
        
        self.conn.commit()
        return True
    
    def get_setting(self, feature: str, default: Any = None) -> Any:
        """
        Get a user setting.
        
        Args:
            feature: Setting name
            default: Default value if not found
            
        Returns:
            Setting value or default
        """
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT value FROM user_settings
            WHERE feature = ?
        """, (feature,))
        
        row = cursor.fetchone()
        
        if row is None:
            return default
        
        # Try to convert back to appropriate type
        value = row['value']
        
        # Check if it's a boolean string '0' or '1' ONLY
        if isinstance(value, str) and value in ('0', '1'):
            return bool(int(value))
        
        # Check if it's already a boolean (from Python bool type)
        if isinstance(value, bool):
            return value
        
        # Try numeric - only for non-empty strings that look like numbers
        if isinstance(value, str) and value.strip():
            try:
                if '.' in value:
                    return float(value)
                else:
                    return int(value)
            except (ValueError, TypeError):
                pass
        
        return value
    
    def get_all_settings(self) -> Dict:
        """
        Get all user settings.
        
        Returns:
            Dictionary of all settings
        """
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT feature, value FROM user_settings
        """)
        
        settings = {}
        for row in cursor.fetchall():
            feature = row['feature']
            value = row['value']
            
            # Convert to appropriate type - only convert '0' and '1' for booleans
            if isinstance(value, str) and value in ('0', '1'):
                settings[feature] = bool(int(value))
            else:
                try:
                    if isinstance(value, str) and '.' in value:
                        settings[feature] = float(value)
                    elif isinstance(value, str):
                        settings[feature] = int(value)
                    else:
                        settings[feature] = value
                except (ValueError, TypeError):
                    settings[feature] = value
        
        return settings
    
    # ==================== Process History Operations ====================
    
    def insert_process_snapshot(self, processes: List[Dict]) -> int:
        """
        Insert a snapshot of all processes.
        
        Args:
            processes: List of process dictionaries
            
        Returns:
            int: Number of records inserted
        """
        cursor = self.conn.cursor()
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        data = [
            (timestamp, p['pid'], p['name'], p['cpu_percent'], p['memory_mb'], p['memory_percent'])
            for p in processes
        ]
        
        cursor.executemany("""
            INSERT INTO process_history 
            (timestamp, pid, process_name, cpu_percent, memory_mb, memory_percent)
            VALUES (?, ?, ?, ?, ?, ?)
        """, data)
        
        self.conn.commit()
        return cursor.rowcount
    
    def get_process_history(self, process_name: str = None, 
                           limit: int = 100) -> List[Dict]:
        """
        Get process history.
        
        Args:
            process_name: Optional filter by process name
            limit: Maximum records to return
            
        Returns:
            List of process history records
        """
        cursor = self.conn.cursor()
        
        if process_name:
            cursor.execute("""
                SELECT * FROM process_history
                WHERE process_name = ?
                ORDER BY timestamp DESC
                LIMIT ?
            """, (process_name, limit))
        else:
            cursor.execute("""
                SELECT * FROM process_history
                ORDER BY timestamp DESC
                LIMIT ?
            """, (limit,))
        
        return [dict(row) for row in cursor.fetchall()]
    
    # ==================== Utility Methods ====================
    
    def cleanup_old_data(self, days: int = 7) -> Dict:
        """
        Clean up old data from all tables.
        
        Args:
            days: Number of days to keep
            
        Returns:
            Dictionary with cleanup statistics
        """
        cursor = self.conn.cursor()
        cutoff = f"datetime('now', '-{days} days')"
        
        # Clean up metrics
        cursor.execute(f"DELETE FROM system_metrics WHERE timestamp < {cutoff}")
        metrics_deleted = cursor.rowcount
        
        # Clean up alerts
        cursor.execute(f"DELETE FROM alerts WHERE timestamp < {cutoff}")
        alerts_deleted = cursor.rowcount
        
        # Clean up process history
        cursor.execute(f"DELETE FROM process_history WHERE timestamp < {cutoff}")
        process_deleted = cursor.rowcount
        
        self.conn.commit()
        
        return {
            'metrics_deleted': metrics_deleted,
            'alerts_deleted': alerts_deleted,
            'process_deleted': process_deleted
        }
    
    def get_database_stats(self) -> Dict:
        """
        Get database statistics.
        
        Returns:
            Dictionary with database statistics
        """
        cursor = self.conn.cursor()
        
        stats = {}
        
        # Count records in each table
        tables = ['system_metrics', 'alerts', 'user_settings', 'process_history']
        for table in tables:
            cursor.execute(f"SELECT COUNT(*) as count FROM {table}")
            stats[f'{table}_count'] = cursor.fetchone()['count']
        
        # Get database file size
        if os.path.exists(self.db_path):
            stats['database_size_bytes'] = os.path.getsize(self.db_path)
        
        return stats
    
    # ==================== Admin Notes Operations (CRUD) ====================
    
    def insert_note(self, target_date: str, note_text: str) -> int:
        """Create an admin note."""
        cursor = self.conn.cursor()
        cursor.execute("""
            INSERT INTO admin_notes (target_date, note_text)
            VALUES (?, ?)
        """, (target_date, note_text))
        self.conn.commit()
        return cursor.lastrowid
        
    def get_all_notes(self) -> List[Dict]:
        """Read all admin notes."""
        cursor = self.conn.cursor()
        cursor.execute("SELECT * FROM admin_notes ORDER BY timestamp DESC")
        return [dict(row) for row in cursor.fetchall()]
        
    def update_note(self, note_id: int, new_text: str) -> bool:
        """Update an existing admin note."""
        cursor = self.conn.cursor()
        cursor.execute("""
            UPDATE admin_notes
            SET note_text = ?
            WHERE id = ?
        """, (new_text, note_id))
        self.conn.commit()
        return cursor.rowcount > 0
        
    def delete_note(self, note_id: int) -> bool:
        """Delete an admin note."""
        cursor = self.conn.cursor()
        cursor.execute("DELETE FROM admin_notes WHERE id = ?", (note_id,))
        self.conn.commit()
        return cursor.rowcount > 0
    
    def close(self):
        """Close database connection."""
        if self.conn:
            self.conn.close()
            self.conn = None


# Module-level instance for easy import
db = Database()


def get_database() -> Database:
    """
    Get the singleton database instance.
    
    Returns:
        Database instance
    """
    return db

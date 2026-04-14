"""
Cache and Temp File Cleaner Module
Detects and analyzes cache and temporary files.
Provides safe cleanup recommendations.
"""

import os
import shutil
from typing import List, Dict, Optional
from datetime import datetime


class CacheCleaner:
    """
    Analyzes and helps clean temporary files and cache.
    Provides safe cleanup options without breaking system functionality.
    """
    
    # Common cache and temp locations on Windows
    CACHE_LOCATIONS = [
        # Windows Temp
        {
            'name': 'Windows Temp',
            'path': os.environ.get('TEMP', 'C:\\Windows\\Temp'),
            'category': 'temp',
            'safe_to_clean': True,
            'description': 'Temporary files used by Windows and applications'
        },
        # User Temp
        {
            'name': 'User Temp',
            'path': os.path.join(os.environ.get('LOCALAPPDATA', ''), 'Temp'),
            'category': 'temp',
            'safe_to_clean': True,
            'description': 'Temporary files for current user'
        },
        # Windows Prefetch
        {
            'name': 'Prefetch',
            'path': 'C:\\Windows\\Prefetch',
            'category': 'cache',
            'safe_to_clean': True,
            'description': 'Pre-fetched application data (recreates automatically)'
        },
        # Windows Update Cache
        {
            'name': 'Windows Update Cache',
            'path': 'C:\\Windows\\SoftwareDistribution\\Download',
            'category': 'update',
            'safe_to_clean': True,
            'description': 'Downloaded Windows updates (needed after updates)'
        },
        # Browser Caches
        {
            'name': 'Chrome Cache',
            'path': os.path.join(os.environ.get('LOCALAPPDATA', ''), 
                                 r'Google\Chrome\User Data\Default\Cache'),
            'category': 'browser',
            'safe_to_clean': True,
            'description': 'Google Chrome browser cache'
        },
        {
            'name': 'Firefox Cache',
            'path': os.path.join(os.environ.get('LOCALAPPDATA', ''), 
                                 r'Mozilla\Firefox\Profiles'),
            'category': 'browser',
            'safe_to_clean': True,
            'description': 'Mozilla Firefox browser cache'
        },
        {
            'name': 'Edge Cache',
            'path': os.path.join(os.environ.get('LOCALAPPDATA', ''), 
                                 r'Microsoft\Edge\User Data\Default\Cache'),
            'category': 'browser',
            'safe_to_clean': True,
            'description': 'Microsoft Edge browser cache'
        },
        # Windows Thumbnail Cache
        {
            'name': 'Thumbnail Cache',
            'path': os.path.join(os.environ.get('LOCALAPPDATA', ''), 
                                 r'Microsoft\Windows\Explorer'),
            'category': 'cache',
            'safe_to_clean': True,
            'description': 'Windows thumbnail cache (recreates automatically)'
        },
        # Recent Documents
        {
            'name': 'Recent Documents',
            'path': os.path.join(os.environ.get('APPDATA', ''), 
                                 r'Microsoft\Windows\Recent'),
            'category': 'recent',
            'safe_to_clean': True,
            'description': 'Recent documents shortcuts (actual files not deleted)'
        },
        # Download folder cleanup suggestion
        {
            'name': 'Downloads Folder',
            'path': os.path.join(os.environ.get('USERPROFILE', os.environ.get('HOME', 'C:\\Users\\Default')), 'Downloads'),
            'category': 'downloads',
            'safe_to_clean': False,  # Manual check only
            'description': 'Downloads folder - check for unwanted files'
        },
        # Windows Logs
        {
            'name': 'Windows Logs',
            'path': 'C:\\Windows\\Logs',
            'category': 'logs',
            'safe_to_clean': True,
            'description': 'Windows system logs'
        },
        # Font Cache
        {
            'name': 'Font Cache',
            'path': os.path.join(os.environ.get('WINDIR', 'C:\\Windows'), 
                                 'ServiceProfiles\\LocalService\\AppData\\Local\\FontCache'),
            'category': 'cache',
            'safe_to_clean': True,
            'description': 'Windows Font Cache'
        },
        # DirectX Shader Cache
        {
            'name': 'DirectX Shader Cache',
            'path': os.path.join(os.environ.get('LOCALAPPDATA', ''), 
                                 r'D3DSCache'),
            'category': 'cache',
            'safe_to_clean': True,
            'description': 'DirectX shader cache (recreates when needed)'
        },
        # Icon Cache
        {
            'name': 'Icon Cache',
            'path': os.path.join(os.environ.get('LOCALAPPDATA', ''), 
                                 r'IconCache.db'),
            'category': 'cache',
            'safe_to_clean': True,
            'description': 'Windows icon cache database'
        }
    ]
    
    def __init__(self):
        """Initialize the cache cleaner."""
        self.scan_results = []
    
    def scan_all(self) -> List[Dict]:
        """
        Scan all known cache locations.
        
        Returns:
            List of scan results with sizes
        """
        results = []
        
        for location in self.CACHE_LOCATIONS:
            try:
                size_info = self.get_folder_size(location['path'])
                
                result = {
                    'name': location['name'],
                    'path': location['path'],
                    'category': location['category'],
                    'safe_to_clean': location['safe_to_clean'],
                    'description': location['description'],
                    'size_bytes': size_info['size'],
                    'size_formatted': size_info['formatted'],
                    'file_count': size_info['file_count'],
                    'exists': size_info['exists']
                }
                
                results.append(result)
                
            except Exception as e:
                result = {
                    'name': location['name'],
                    'path': location['path'],
                    'category': location['category'],
                    'safe_to_clean': location['safe_to_clean'],
                    'description': location['description'],
                    'size_bytes': 0,
                    'size_formatted': '0 B',
                    'file_count': 0,
                    'exists': False,
                    'error': str(e)
                }
                results.append(result)
        
        self.scan_results = results
        return results
    
    def get_folder_size(self, path: str) -> Dict:
        """
        Calculate size of a folder.
        
        Args:
            path: Folder path
            
        Returns:
            Dictionary with size information
        """
        total_size = 0
        file_count = 0
        exists = os.path.exists(path)
        
        if not exists:
            return {
                'size': 0,
                'formatted': '0 B',
                'file_count': 0,
                'exists': False
            }
        
        try:
            if os.path.isfile(path):
                # Single file (like IconCache.db)
                total_size = os.path.getsize(path)
                file_count = 1
            else:
                # Directory
                for dirpath, dirnames, filenames in os.walk(path):
                    for filename in filenames:
                        filepath = os.path.join(dirpath, filename)
                        try:
                            total_size += os.path.getsize(filepath)
                            file_count += 1
                        except (OSError, PermissionError):
                            pass
        except (OSError, PermissionError):
            pass
        
        return {
            'size': total_size,
            'formatted': self._format_size(total_size),
            'file_count': file_count,
            'exists': exists
        }
    
    def _format_size(self, size_bytes: int) -> str:
        """
        Format size in bytes to human-readable string.
        
        Args:
            size_bytes: Size in bytes
            
        Returns:
            Formatted string (e.g., "1.5 GB")
        """
        for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
            if size_bytes < 1024.0:
                return f"{size_bytes:.2f} {unit}"
            size_bytes /= 1024.0
        return f"{size_bytes:.2f} PB"
    
    def get_safe_to_clean_total(self) -> Dict:
        """
        Get total size of files that are safe to clean.
        
        Returns:
            Dictionary with total size and count
        """
        if not self.scan_results:
            self.scan_all()
        
        safe_items = [r for r in self.scan_results 
                     if r.get('safe_to_clean', False) and r.get('exists', False)]
        
        total_size = sum(r['size_bytes'] for r in safe_items)
        total_files = sum(r['file_count'] for r in safe_items)
        
        return {
            'total_bytes': total_size,
            'total_formatted': self._format_size(total_size),
            'item_count': len(safe_items),
            'file_count': total_files
        }
    
    def get_category_summary(self) -> Dict:
        """
        Get summary of cache sizes by category.
        
        Returns:
            Dictionary with category summaries
        """
        if not self.scan_results:
            self.scan_all()
        
        summary = {}
        
        for result in self.scan_results:
            category = result.get('category', 'other')
            if category not in summary:
                summary[category] = {
                    'total_bytes': 0,
                    'total_formatted': '0 B',
                    'item_count': 0
                }
            
            if result.get('exists', False):
                summary[category]['total_bytes'] += result.get('size_bytes', 0)
                summary[category]['item_count'] += 1
        
        # Format sizes
        for category in summary:
            summary[category]['total_formatted'] = self._format_size(
                summary[category]['total_bytes']
            )
        
        return summary
    
    def clean_location(self, path: str, simulate: bool = True) -> Dict:
        """
        Clean a specific cache location.
        
        Args:
            path: Path to clean
            simulate: If True, only simulate cleaning without actually deleting
            
        Returns:
            Dictionary with cleaning results
        """
        result = {
            'path': path,
            'simulated': simulate,
            'success': True,
            'files_deleted': 0,
            'bytes_freed': 0,
            'errors': []
        }
        
        if not os.path.exists(path):
            result['success'] = False
            result['errors'].append('Path does not exist')
            return result
        
        if simulate:
            # Just calculate what would be freed
            size_info = self.get_folder_size(path)
            result['files_deleted'] = size_info['file_count']
            result['bytes_freed'] = size_info['size']
            result['message'] = f"Simulation: Would delete {size_info['file_count']} files ({size_info['formatted']})"
            return result
        
        # Actually clean
        try:
            if os.path.isfile(path):
                # Single file
                size = os.path.getsize(path)
                os.remove(path)
                result['files_deleted'] = 1
                result['bytes_freed'] = size
            else:
                # Directory
                for dirpath, dirnames, filenames in os.walk(path):
                    for filename in filenames:
                        filepath = os.path.join(dirpath, filename)
                        try:
                            size = os.path.getsize(filepath)
                            os.remove(filepath)
                            result['files_deleted'] += 1
                            result['bytes_freed'] += size
                        except (OSError, PermissionError) as e:
                            result['errors'].append(f"Could not delete {filepath}: {str(e)}")
                
                # Try to remove empty directories
                try:
                    os.rmdir(path)
                except OSError:
                    pass  # Directory not empty or not allowed
            
            result['message'] = f"Successfully cleaned {result['files_deleted']} files ({self._format_size(result['bytes_freed'])})"
            
        except Exception as e:
            result['success'] = False
            result['errors'].append(str(e))
            result['message'] = f"Error cleaning: {str(e)}"
        
        return result
    
    def clean_all_safe(self, simulate: bool = True) -> Dict:
        """
        Clean all safe-to-clean locations.
        
        Args:
            simulate: If True, only simulate cleaning
            
        Returns:
            Dictionary with overall cleaning results
        """
        if not self.scan_results:
            self.scan_all()
        
        total_freed = 0
        total_files = 0
        all_errors = []
        locations_cleaned = []
        
        for result in self.scan_results:
            if result.get('safe_to_clean', False) and result.get('exists', False):
                clean_result = self.clean_location(result['path'], simulate)
                
                total_freed += clean_result.get('bytes_freed', 0)
                total_files += clean_result.get('files_deleted', 0)
                all_errors.extend(clean_result.get('errors', []))
                
                if clean_result['success']:
                    locations_cleaned.append(result['name'])
        
        return {
            'simulated': simulate,
            'locations_cleaned': len(locations_cleaned),
            'total_files_deleted': total_files,
            'total_bytes_freed': total_freed,
            'total_formatted': self._format_size(total_freed),
            'errors': all_errors,
            'message': f"{'Would free' if simulate else 'Freed'} {self._format_size(total_freed)} from {len(locations_cleaned)} locations"
        }
    
    def get_cleanup_tips(self) -> List[str]:
        """
        Get helpful tips for cache cleanup.
        
        Returns:
            List of tip strings
        """
        tips = [
            "Regular cleanup of temporary files can free up significant disk space.",
            "Browser caches can be safely cleared - they will recreate as needed.",
            "Windows Update cache should only be cleared if you're having update issues.",
            "Don't delete everything at once - space will be reclaimed gradually.",
            "Use the 'Simulate Clean' option first to see what would be deleted.",
            "Close applications before cleaning their cache folders.",
            "Disk Cleanup tool (cleanmgr) is a built-in Windows alternative.",
            "Consider cleaning monthly for best performance."
        ]
        
        # Add specific recommendation based on current scan
        if not self.scan_results:
            self.scan_all()
        
        safe_total = self.get_safe_to_clean_total()
        if safe_total['total_bytes'] > 1024 * 1024 * 1024:  # > 1 GB
            tips.append(
                f"You have {safe_total['total_formatted']} of cleanable files. "
                "Running a cleanup could significantly improve disk space."
            )
        
        return tips
    
    def get_recommendations(self) -> List[str]:
        """
        Get specific cleanup recommendations based on scan results.
        
        Returns:
            List of recommendation strings
        """
        if not self.scan_results:
            self.scan_results = self.scan()
        
        recommendations = []
        
        # Check each category
        category_summary = self.get_category_summary()
        
        if 'temp' in category_summary and category_summary['temp']['total_bytes'] > 100 * 1024 * 1024:
            recommendations.append(
                f"Temp files: {category_summary['temp']['total_formatted']} - Safe to clean"
            )
        
        if 'browser' in category_summary and category_summary['browser']['total_bytes'] > 500 * 1024 * 1024:
            recommendations.append(
                f"Browser cache: {category_summary['browser']['total_formatted']} - Consider clearing old cache"
            )
        
        if 'cache' in category_summary and category_summary['cache']['total_bytes'] > 200 * 1024 * 1024:
            recommendations.append(
                f"System cache: {category_summary['cache']['total_formatted']} - Safe to clean"
            )
        
        return recommendations if recommendations else ["System is clean - no immediate action needed"]

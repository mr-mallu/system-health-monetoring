"""
Startup Program Checker Module
Detects and analyzes startup applications on Windows.
Provides recommendations for safe disabling.
"""

import os
import subprocess
import winreg
from typing import List, Dict, Optional
import psutil


class StartupChecker:
    """
    Analyzes Windows startup programs and provides recommendations.
    Helps users identify unnecessary startup applications.
    """
    
    def __init__(self):
        """Initialize the startup checker."""
        self.startup_programs = []
    
    def get_startup_programs(self) -> List[Dict]:
        """
        Get all startup programs from multiple sources.
        
        Returns:
            List of startup program dictionaries
        """
        programs = []
        
        # Get from Run registry key (current user)
        programs.extend(self._get_registry_startup(winreg.HKEY_CURRENT_USER, 
                                                    r"Software\Microsoft\Windows\CurrentVersion\Run"))
        
        # Get from Run registry key (local machine)
        programs.extend(self._get_registry_startup(winreg.HKEY_LOCAL_MACHINE, 
                                                    r"Software\Microsoft\Windows\CurrentVersion\Run"))
        
        # Get from Startup folder
        programs.extend(self._get_startup_folder())
        
        # Get scheduled tasks (common startup tasks)
        programs.extend(self._get_scheduled_tasks())
        
        self.startup_programs = programs
        return programs
    
    def _get_registry_startup(self, hkey, subkey_path: str) -> List[Dict]:
        """
        Get startup programs from a registry key.
        
        Args:
            hkey: Registry hive (HKEY_CURRENT_USER or HKEY_LOCAL_MACHINE)
            subkey_path: Registry subkey path
            
        Returns:
            List of startup program dictionaries
        """
        programs = []
        
        try:
            key = winreg.OpenKey(hkey, subkey_path, 0, winreg.KEY_READ)
            
            i = 0
            while True:
                try:
                    name, value, _ = winreg.EnumValue(key, i)
                    
                    # Determine impact level based on common patterns
                    impact = self._estimate_impact(name, value)
                    
                    program_info = {
                        'name': name,
                        'command': value,
                        'source': 'Registry',
                        'location': self._get_registry_location(hkey, subkey_path),
                        'impact': impact,
                        'recommendation': self._get_recommendation(impact, name),
                        'enabled': True
                    }
                    
                    programs.append(program_info)
                    i += 1
                    
                except WindowsError:
                    break
            
            winreg.CloseKey(key)
            
        except WindowsError:
            pass
        
        return programs
    
    def _get_registry_location(self, hkey, subkey_path: str) -> str:
        """Get human-readable registry location."""
        if hkey == winreg.HKEY_CURRENT_USER:
            return f"HKCU\\{subkey_path}"
        elif hkey == winreg.HKEY_LOCAL_MACHINE:
            return f"HKLM\\{subkey_path}"
        return subkey_path
    
    def _get_startup_folder(self) -> List[Dict]:
        """
        Get startup programs from the user's Startup folder.
        
        Returns:
            List of startup program dictionaries
        """
        programs = []
        
        # Get user startup folder
        startup_folder = os.path.join(os.environ.get('APPDATA', ''), 
                                       r"Microsoft\Windows\Start Menu\Programs\Startup")
        
        # Also check all users startup folder
        all_users_startup = r"C:\ProgramData\Microsoft\Windows\Start Menu\Programs\Startup"
        
        for folder in [startup_folder, all_users_startup]:
            if os.path.exists(folder):
                try:
                    for item in os.listdir(folder):
                        item_path = os.path.join(folder, item)
                        
                        # Determine impact
                        impact = self._estimate_impact(item, item_path)
                        
                        program_info = {
                            'name': os.path.splitext(item)[0],
                            'command': item_path,
                            'source': 'Startup Folder',
                            'location': folder,
                            'impact': impact,
                            'recommendation': self._get_recommendation(impact, item),
                            'enabled': True
                        }
                        
                        programs.append(program_info)
                        
                except PermissionError:
                    pass
        
        return programs
    
    def _get_scheduled_tasks(self) -> List[Dict]:
        """
        Get common startup scheduled tasks.
        
        Returns:
            List of startup task dictionaries
        """
        programs = []
        
        # Common startup tasks to check
        common_tasks = [
            'Adobe Acrobat Update Service',
            'Google Update',
            'Microsoft Office ClickToRun',
            'OneDrive',
            'Dropbox',
            'Spotify Web Helper',
            'Discord',
            'Steam Client',
            'NVIDIA GeForce Experience',
            'AMD Radeon Settings',
            'Realtek Audio',
            'Bluetooth Service'
        ]
        
        for task_name in common_tasks:
            # Determine impact based on task name
            impact = self._estimate_impact(task_name, '')
            
            if impact != 'Low':  # Only include medium/high impact tasks
                program_info = {
                    'name': task_name,
                    'command': f"Scheduled Task: {task_name}",
                    'source': 'Scheduled Tasks',
                    'location': 'Task Scheduler',
                    'impact': impact,
                    'recommendation': self._get_recommendation(impact, task_name),
                    'enabled': True
                }
                
                programs.append(program_info)
        
        return programs
    
    def _estimate_impact(self, name: str, command: str) -> str:
        """
        Estimate the system impact of a startup program.
        
        Args:
            name: Program name
            command: Program command/path
            
        Returns:
            Impact level: 'Low', 'Medium', or 'High'
        """
        name_lower = name.lower() if name else ''
        command_lower = command.lower() if command else ''
        
        # High impact - resource intensive applications
        high_impact_keywords = [
            'steam', 'spotify', 'discord', 'teams', 'zoom', 'skype',
            'slack', 'dropbox', 'onedrive', 'backup', 'antivirus',
            'nvidia', 'amd', 'realtek', 'bluetooth', 'wireless'
        ]
        
        # Low impact - system utilities that are quick
        low_impact_keywords = [
            'security', 'update', 'helper', 'tray', 'notification'
        ]
        
        combined = name_lower + ' ' + command_lower
        
        # Check for high impact
        for keyword in high_impact_keywords:
            if keyword in combined:
                return 'High'
        
        # Check for low impact
        for keyword in low_impact_keywords:
            if keyword in combined:
                return 'Low'
        
        return 'Medium'
    
    def _get_recommendation(self, impact: str, name: str) -> str:
        """
        Get recommendation for a startup program.
        
        Args:
            impact: Impact level
            name: Program name
            
        Returns:
            Recommendation string
        """
        name_lower = name.lower() if name else ''
        
        # System required programs
        system_required = ['windows', 'microsoft', 'security', 'defender', 
                         'audio', 'bluetooth', 'touchpad', 'synaptics']
        
        for req in system_required:
            if req in name_lower:
                return 'System required - Do not disable'
        
        if impact == 'High':
            return 'Consider disabling if not needed'
        elif impact == 'Medium':
            return 'Safe to disable if not used'
        else:
            return 'Low impact - Can disable'
    
    def get_impact_summary(self) -> Dict:
        """
        Get summary of startup program impacts.
        
        Returns:
            Dictionary with impact counts
        """
        if not self.startup_programs:
            self.get_startup_programs()
        
        return {
            'total': len(self.startup_programs),
            'high_impact': sum(1 for p in self.startup_programs if p['impact'] == 'High'),
            'medium_impact': sum(1 for p in self.startup_programs if p['impact'] == 'Medium'),
            'low_impact': sum(1 for p in self.startup_programs if p['impact'] == 'Low'),
            'system_required': sum(1 for p in self.startup_programs 
                                   if 'System required' in p['recommendation'])
        }
    
    def suggest_disable_candidates(self) -> List[Dict]:
        """
        Get list of startup programs that are safe to disable.
        
        Returns:
            List of programs that can be safely disabled
        """
        if not self.startup_programs:
            self.get_startup_programs()
        
        candidates = []
        
        for program in self.startup_programs:
            # Check if it's safe to disable
            if ('System required' not in program['recommendation'] and
                program['recommendation'] != 'System required - Do not disable'):
                candidates.append(program)
        
        return candidates
    
    def get_tips(self) -> List[str]:
        """
        Get helpful tips about startup programs.
        
        Returns:
            List of tip strings
        """
        tips = [
            "Startup programs slow down your computer's boot time.",
            "Disabling unused startup programs can improve performance.",
            "You can manage startup programs in Task Manager > Startup tab.",
            "Some programs need to run at startup to function properly.",
            "Antivirus and security software should not be disabled.",
            "Cloud sync services like OneDrive and Dropbox can be started manually.",
            "Disable programs you don't use frequently to speed up boot time."
        ]
        
        # Add specific recommendations based on current programs
        if not self.startup_programs:
            self.get_startup_programs()
        
        if self.get_impact_summary()['high_impact'] > 3:
            tips.append(
                f"You have {self.get_impact_summary()['high_impact']} high-impact "
                "startup programs. Consider disabling ones you don't need."
            )
        
        return tips
    
    def disable_startup_program(self, program: dict) -> dict:
        """
        Disable a startup program.
        For Registry sources: deletes the value from the Run key (HKCU only).
        For Startup Folder sources: renames the shortcut with a .disabled suffix.
        
        Args:
            program: Program dictionary from get_startup_programs()
            
        Returns:
            dict with 'success' (bool) and 'message' (str)
        """
        result = {'success': False, 'message': ''}
        name = program.get('name', '')
        source = program.get('source', '')
        location = program.get('location', '')
        
        try:
            if source == 'Registry' and 'HKCU' in location:
                # Remove from HKCU registry
                subkey = r"Software\Microsoft\Windows\CurrentVersion\Run"
                key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, subkey, 0,
                                     winreg.KEY_SET_VALUE)
                winreg.DeleteValue(key, name)
                winreg.CloseKey(key)
                result['success'] = True
                result['message'] = f"Removed '{name}' from startup registry."
                # Update local state
                program['enabled'] = False
            
            elif source == 'Startup Folder':
                command = program.get('command', '')
                if os.path.exists(command):
                    disabled_path = command + '.disabled'
                    os.rename(command, disabled_path)
                    result['success'] = True
                    result['message'] = f"Disabled '{name}' by renaming shortcut."
                    program['enabled'] = False
                else:
                    result['message'] = f"Shortcut not found: {command}"
            
            elif source == 'Registry' and 'HKLM' in location:
                result['message'] = (
                    f"Cannot disable '{name}': Machine-level startup items "
                    "require administrator privileges. Use Task Manager instead."
                )
            
            elif source == 'Scheduled Tasks':
                result['message'] = (
                    f"Cannot disable '{name}': Use Task Scheduler to manage "
                    "scheduled tasks."
                )
            
            else:
                result['message'] = f"Unsupported source type: {source}"
        
        except PermissionError:
            result['message'] = f"Permission denied trying to disable '{name}'."
        except Exception as e:
            result['message'] = f"Error disabling '{name}': {str(e)}"
        
        return result

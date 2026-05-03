"""
Shared Constants
Centralized constants used across multiple modules.
"""

# Windows system processes excluded from anomaly alerts and process filtering.
# Updating this set automatically applies to both the process monitor and
# the anomaly detector, keeping them in sync.
SYSTEM_PROCESSES_TO_IGNORE = {
    # Core Windows kernel / session processes
    'System Idle Process', 'System', 'Registry', 'smss.exe',
    'csrss.exe', 'wininit.exe', 'services.exe', 'lsass.exe',
    'svchost.exe', 'dwm.exe', 'fontdrvhost.exe', 'MemCompression',
    'winlogon.exe', 'taskhostw.exe', 'dllhost.exe', 'conhost.exe',
    'ctfmon.exe', 'sihost.exe', 'winmgmt.exe',

    # Windows background services
    'WmiPrvSE.exe', 'wmiprvse.exe', 'WUDFHost.exe', 'wudfhost.exe',
    'RuntimeBroker.exe', 'SearchIndexer.exe', 'SecurityHealthService.exe',
    'MsMpEng.exe', 'NisSrv.exe', 'audiodg.exe', 'SearchHost.exe',
    'TextInputHost.exe', 'ShellExperienceHost.exe',
    'StartMenuExperienceHost.exe', 'SgrmBroker.exe',
    'SearchProtocolHost.exe', 'SearchFilterHost.exe',
    'SecurityHealthSystray.exe', 'TiWorker.exe', 'MoUsoCoreWorker.exe',

    # Windows shell & UX
    'Windows Terminal', 'ApplicationFrameHost.exe', 'LockApp.exe',
    'PeopleHub.exe', 'DesktopBridge.exe',

    # Networking, scheduling, and system services
    'EventLog.exe', 'PlugPlay.exe', 'SamSs.exe', 'LanmanServer.exe',
    'LanmanWorkstation.exe', 'NlaSvc.exe', 'nsi.exe', 'Schedule.exe',
    'Seclogon.exe', 'Themes.exe', 'UserManager.exe', 'ProfSvc.exe',
    'BITS.exe', 'ClipSVC.exe', 'DiagTrack.exe', 'DPS.exe',
    'iphlpsvc.exe', 'lfsvc.exe', 'MapsBroker.exe', 'msiexec.exe',
    'Netlogon.exe', 'Netman.exe', 'netprofm.exe',
    'Spooler.exe', 'spoolsv.exe', 'SysMain.exe',
    'SystemEventsBroker.exe', 'TrustedInstaller.exe',
    'unsecapp.exe', 'VaultSvc.exe', 'VSSVC.exe', 'W32Time.exe',
    'WerFault.exe', 'WerFaultSecure.exe', 'WinDefend.exe',
    'Winmgmt.exe', 'wuauserv.exe',

    # Third-party security / antivirus
    'AVGIDSAgent.exe', 'avgwdsvc.exe', 'avp.exe', 'avpui.exe',
    'McUICnt.exe', 'mcapexe.exe', 'aswidsagent.exe', 'aswEngSrv.exe',

    # Java / common runtimes
    'java.exe', 'javaw.exe',

    # Database engines (often legitimate background services)
    'sqlservr.exe', 'mongod.exe',
}

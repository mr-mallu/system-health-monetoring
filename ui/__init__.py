"""
UI Package
Contains all GUI modules for the System Health Monitoring application.
"""

from ui.main_window import MainWindow
from ui.settings_view import SettingsView
from ui.history_view import HistoryView
from ui.suggestions_view import SuggestionsView
from ui.graph_dashboard import GraphDashboard

__all__ = [
    'MainWindow',
    'SettingsView',
    'HistoryView',
    'SuggestionsView',
    'GraphDashboard'
]


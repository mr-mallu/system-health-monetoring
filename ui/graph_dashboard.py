"""
Graph Dashboard Module
Provides lightweight graphs for system metrics visualization.
Uses pyqtgraph for performance or matplotlib as fallback.
"""

from typing import List, Dict, Optional
from datetime import datetime
from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel
from PySide6.QtCore import Qt
from PySide6.QtGui import QFont

try:
    import pyqtgraph as pg
    HAS_PYQTGRAPH = True
except ImportError:
    HAS_PYQTGRAPH = False
    try:
        from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
        from matplotlib.figure import Figure
        HAS_MATPLOTLIB = True
    except ImportError:
        try:
            from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
            from matplotlib.figure import Figure
            HAS_MATPLOTLIB = True
        except ImportError:
            HAS_MATPLOTLIB = False


class GraphDashboard(QWidget):
    """
    Dashboard for displaying system metrics graphs.
    Automatically uses pyqtgraph if available, falls back to matplotlib.
    """

    def __init__(self):
        """Initialize the graph dashboard."""
        super().__init__()

        self.history_data = {
            'cpu': [],
            'memory': [],
            'health': [],
            'timestamps': []
        }

        self.init_ui()

    def init_ui(self):
        """Initialize the UI."""
        layout = QVBoxLayout()

        # Title
        title = QLabel("System Metrics - Live Graphs")
        title_font = QFont()
        title_font.setPointSize(12)
        title_font.setBold(True)
        title.setFont(title_font)
        layout.addWidget(title)

        # Create graph container
        graphs_layout = QHBoxLayout()

        if HAS_PYQTGRAPH:
            self._create_pyqtgraph_ui(graphs_layout)
        elif HAS_MATPLOTLIB:
            self._create_matplotlib_ui(graphs_layout)
        else:
            # Fallback: simple text display
            fallback = QLabel(
                "Graph visualization requires either PyQtGraph or Matplotlib.\n"
                "Install with: pip install pyqtgraph\n"
                "Or: pip install matplotlib"
            )
            graphs_layout.addWidget(fallback)

        layout.addLayout(graphs_layout)
        self.setLayout(layout)

    def _create_pyqtgraph_ui(self, layout):
        """Create pyqtgraph-based visualizations."""
        # Set background color
        pg.setConfigOption('background', '#333333')
        pg.setConfigOption('foreground', '#CCCCCC')

        # CPU Graph
        self.cpu_plot = pg.PlotWidget(title="CPU Usage (%)")
        self.cpu_plot.setLabel('left', 'CPU Usage', units='%')
        self.cpu_plot.setLabel('bottom', 'Time (samples)')
        self.cpu_plot.setYRange(0, 100)
        self.cpu_plot.showGrid(x=True, y=True, alpha=0.3)
        self.cpu_line = self.cpu_plot.plot(pen='#FF6B6B', name='CPU')

        # Memory Graph
        self.memory_plot = pg.PlotWidget(title="Memory Usage (%)")
        self.memory_plot.setLabel('left', 'Memory Usage', units='%')
        self.memory_plot.setLabel('bottom', 'Time (samples)')
        self.memory_plot.setYRange(0, 100)
        self.memory_plot.showGrid(x=True, y=True, alpha=0.3)
        self.memory_line = self.memory_plot.plot(pen='#4ECDC4', name='Memory')

        # Health Score Graph
        self.health_plot = pg.PlotWidget(title="Health Score")
        self.health_plot.setLabel('left', 'Health Score', units='/100')
        self.health_plot.setLabel('bottom', 'Time (samples)')
        self.health_plot.setYRange(0, 100)
        self.health_plot.showGrid(x=True, y=True, alpha=0.3)
        self.health_line = self.health_plot.plot(pen='#95E1D3', name='Health')

        layout.addWidget(self.cpu_plot)
        layout.addWidget(self.memory_plot)
        layout.addWidget(self.health_plot)

        self.use_pyqtgraph = True

    def _create_matplotlib_ui(self, layout):
        """Create matplotlib-based visualizations (fallback)."""
        self.figure = Figure(figsize=(12, 4), dpi=80, facecolor='#2B2B2B')
        self.canvas = FigureCanvas(self.figure)

        # Create subplots
        self.ax_cpu = self.figure.add_subplot(131)
        self.ax_memory = self.figure.add_subplot(132)
        self.ax_health = self.figure.add_subplot(133)

        # Configure subplots
        for ax in [self.ax_cpu, self.ax_memory, self.ax_health]:
            ax.set_facecolor('#333333')
            ax.tick_params(colors='#CCCCCC')
            for spine in ax.spines.values():
                spine.set_color('#555555')

        self.ax_cpu.set_title('CPU Usage (%)', color='#CCCCCC')
        self.ax_cpu.set_ylim(0, 100)
        self.ax_cpu.set_xlabel('Samples', color='#CCCCCC')

        self.ax_memory.set_title('Memory Usage (%)', color='#CCCCCC')
        self.ax_memory.set_ylim(0, 100)
        self.ax_memory.set_xlabel('Samples', color='#CCCCCC')

        self.ax_health.set_title('Health Score', color='#CCCCCC')
        self.ax_health.set_ylim(0, 100)
        self.ax_health.set_xlabel('Samples', color='#CCCCCC')

        layout.addWidget(self.canvas)

        self.use_pyqtgraph = False

    def update_metrics(self, cpu: float, memory: float, health: float):
        """
        Update graphs with new metrics.

        Args:
            cpu: CPU usage percentage
            memory: Memory usage percentage
            health: Health score (0-100)
        """
        self.history_data['cpu'].append(cpu)
        self.history_data['memory'].append(memory)
        self.history_data['health'].append(health)
        self.history_data['timestamps'].append(datetime.now())

        # Keep last 60 data points
        max_history = 60
        for key in self.history_data:
            if len(self.history_data[key]) > max_history:
                self.history_data[key].pop(0)

        self._refresh_graphs()

    def _refresh_graphs(self):
        """Refresh all graphs with current data."""
        if HAS_PYQTGRAPH and self.use_pyqtgraph:
            self._refresh_pyqtgraph()
        elif HAS_MATPLOTLIB:
            self._refresh_matplotlib()

    def _refresh_pyqtgraph(self):
        """Refresh pyqtgraph visualizations."""
        x_data = list(range(len(self.history_data['cpu'])))

        self.cpu_line.setData(x_data, self.history_data['cpu'])
        self.memory_line.setData(x_data, self.history_data['memory'])
        self.health_line.setData(x_data, self.history_data['health'])

    def _refresh_matplotlib(self):
        """Refresh matplotlib visualizations."""
        x_data = list(range(len(self.history_data['cpu'])))

        # Clear axes
        self.ax_cpu.clear()
        self.ax_memory.clear()
        self.ax_health.clear()

        # Plot data
        self.ax_cpu.plot(x_data, self.history_data['cpu'], color='#FF6B6B', linewidth=2)
        self.ax_cpu.fill_between(x_data, self.history_data['cpu'], alpha=0.3, color='#FF6B6B')
        self.ax_cpu.set_ylim(0, 100)
        self.ax_cpu.set_title('CPU Usage (%)', color='#CCCCCC')
        self.ax_cpu.tick_params(colors='#CCCCCC')

        self.ax_memory.plot(x_data, self.history_data['memory'], color='#4ECDC4', linewidth=2)
        self.ax_memory.fill_between(x_data, self.history_data['memory'], alpha=0.3, color='#4ECDC4')
        self.ax_memory.set_ylim(0, 100)
        self.ax_memory.set_title('Memory Usage (%)', color='#CCCCCC')
        self.ax_memory.tick_params(colors='#CCCCCC')

        self.ax_health.plot(x_data, self.history_data['health'], color='#95E1D3', linewidth=2)
        self.ax_health.fill_between(x_data, self.history_data['health'], alpha=0.3, color='#95E1D3')
        self.ax_health.set_ylim(0, 100)
        self.ax_health.set_title('Health Score', color='#CCCCCC')
        self.ax_health.tick_params(colors='#CCCCCC')

        self.figure.tight_layout()
        self.canvas.draw()

    def clear_history(self):
        """Clear all graph history."""
        self.history_data = {
            'cpu': [],
            'memory': [],
            'health': [],
            'timestamps': []
        }
        self._refresh_graphs()

    def export_graph_data(self) -> Dict:
        """
        Export graph data as dictionary.

        Returns:
            Dictionary with graph history data
        """
        return {
            'cpu_history': self.history_data['cpu'].copy(),
            'memory_history': self.history_data['memory'].copy(),
            'health_history': self.history_data['health'].copy(),
            'timestamps': [t.isoformat() for t in self.history_data['timestamps']],
            'exported_at': datetime.now().isoformat()
        }

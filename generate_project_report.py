import sys
from pathlib import Path

from PySide6.QtGui import QTextDocument
from PySide6.QtPrintSupport import QPrinter
from PySide6.QtWidgets import QApplication


HTML_CONTENT = """
<html>
<body style="font-family: Arial, sans-serif; margin: 24px;">
    <table width="100%" cellpadding="18" cellspacing="0" bgcolor="#1d4ed8">
        <tr>
            <td align="center">
                <font color="#ffffff" size="7"><b>System Health Monitoring System</b></font><br><br>
                <font color="#dbeafe" size="4">Project Report</font>
            </td>
        </tr>
    </table>

    <br><br>

    <font size="6" color="#0f172a"><b>1. Introduction</b></font>
    <hr color="#cbd5e1" size="1">
    <p>
        The System Health Monitoring System is a software application used to monitor the
        performance and health of a computer system in real time. It tracks important
        parameters like CPU usage, memory usage, and disk space, and alerts the user when
        the system exceeds safe limits.
    </p>

    <font size="6" color="#0f172a"><b>2. Purpose of the Project</b></font>
    <hr color="#cbd5e1" size="1">
    <ul>
        <li>To automate system monitoring</li>
        <li>To avoid system crashes</li>
        <li>To improve performance</li>
        <li>To provide real-time updates</li>
    </ul>

    <font size="6" color="#0f172a"><b>3. Problem It Solves</b></font>
    <hr color="#cbd5e1" size="1">
    <ul>
        <li>Manual monitoring is difficult</li>
        <li>No early warning before failure</li>
        <li>Hard to track multiple system parameters</li>
    </ul>

    <font size="6" color="#0f172a"><b>4. Key Features</b></font>
    <hr color="#cbd5e1" size="1">
    <ul>
        <li>Real-time CPU monitoring</li>
        <li>RAM usage tracking</li>
        <li>Disk space analysis</li>
        <li>Alert or notification system</li>
        <li>Simple dashboard UI</li>
    </ul>

    <font size="6" color="#0f172a"><b>5. How the System Works</b></font>
    <hr color="#cbd5e1" size="1">
    <ol>
        <li>The system collects hardware data such as CPU, RAM, and disk usage.</li>
        <li>Data is processed in the backend.</li>
        <li>Monitoring history can be stored in the database.</li>
        <li>Results are displayed on the dashboard.</li>
        <li>Alerts are generated when limits are exceeded.</li>
    </ol>

    <font size="6" color="#0f172a"><b>6. System Architecture</b></font>
    <hr color="#cbd5e1" size="1">
    <table width="100%" cellpadding="12" cellspacing="0" bgcolor="#eff6ff" style="border: 1px solid #bfdbfe;">
        <tr>
            <td align="center">
                <font size="4" color="#1e3a8a"><b>User -> Dashboard (UI) -> Backend Server -> System Metrics (CPU, RAM, Disk)</b></font>
            </td>
        </tr>
    </table>

    <br>

    <font size="6" color="#0f172a"><b>7. Modules of the Project</b></font>
    <hr color="#cbd5e1" size="1">
    <ol>
        <li>Data Collection Module</li>
        <li>Monitoring Module</li>
        <li>Alert Module</li>
        <li>User Interface Module</li>
    </ol>

    <font size="6" color="#0f172a"><b>8. Technologies Used</b></font>
    <hr color="#cbd5e1" size="1">
    <ul>
        <li>Python</li>
        <li>PySide6</li>
        <li>psutil</li>
        <li>SQLite</li>
    </ul>

    <font size="6" color="#0f172a"><b>9. Advantages</b></font>
    <hr color="#cbd5e1" size="1">
    <ul>
        <li>Easy to use</li>
        <li>Real-time monitoring</li>
        <li>Prevents system failure</li>
        <li>Saves time</li>
    </ul>

    <font size="6" color="#0f172a"><b>10. Limitations</b></font>
    <hr color="#cbd5e1" size="1">
    <ul>
        <li>Limited to local system monitoring</li>
        <li>Needs connectivity in some extended use cases</li>
        <li>Basic alert system</li>
    </ul>

    <font size="6" color="#0f172a"><b>11. Future Scope</b></font>
    <hr color="#cbd5e1" size="1">
    <ul>
        <li>Mobile app integration</li>
        <li>Cloud monitoring</li>
        <li>AI-based prediction system</li>
    </ul>

    <font size="6" color="#0f172a"><b>12. Conclusion</b></font>
    <hr color="#cbd5e1" size="1">
    <p>
        This project provides an efficient way to monitor system performance and helps
        users maintain system health by giving timely alerts and insights.
    </p>
</body>
</html>
"""


def main() -> int:
    app = QApplication.instance() or QApplication(sys.argv)

    project_root = Path(__file__).resolve().parent
    output_path = project_root / "project_report.pdf"

    document = QTextDocument()
    document.setHtml(HTML_CONTENT)

    printer = QPrinter(QPrinter.HighResolution)
    printer.setOutputFormat(QPrinter.PdfFormat)
    printer.setOutputFileName(str(output_path))
    document.print_(printer)

    print(output_path)
    app.quit()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

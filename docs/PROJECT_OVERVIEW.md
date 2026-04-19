# System Health Monitoring System

## Project Description

The System Health Monitoring System is a software application used to monitor the performance and health of a computer system in real time. It tracks important parameters like CPU usage, memory usage, and disk space, and alerts the user when the system exceeds safe limits.

## Purpose of the Project

- Automate system monitoring
- Avoid system crashes
- Improve performance
- Provide real-time updates

## Problem It Solves

- Manual monitoring is difficult
- No early warning before failure
- Hard to track multiple system parameters

## Key Features

- Real-time CPU monitoring
- RAM usage tracking
- Disk space analysis
- Alert and notification system
- Simple dashboard UI

## How the System Works

1. The system collects hardware data such as CPU, RAM, disk, and process activity.
2. The backend processes the incoming metrics and health signals.
3. Important monitoring history is stored in the database.
4. Results are displayed in the dashboard for the user.
5. Alerts are generated when configured thresholds are exceeded.

## Simple Architecture

`User -> Dashboard (UI) -> Backend Services -> System Metrics (CPU, RAM, Disk)`

## Modules of the Project

1. Data Collection Module
2. Monitoring Module
3. Alert Module
4. User Interface Module

## Technologies Used

- Python
- PySide6
- psutil
- SQLite

## Advantages

- Easy to use
- Real-time monitoring
- Helps prevent system failure
- Saves time

## Limitations

- Limited to the local system
- Basic alert workflow compared with larger monitoring platforms
- No built-in cloud or remote monitoring yet

## Future Scope

- Mobile app integration
- Cloud monitoring
- AI-based prediction system

## Conclusion

This project provides an efficient way to monitor system performance and helps users maintain system health by giving timely alerts and insights.

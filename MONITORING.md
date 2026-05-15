# DP_GP_cluster Monitoring Guide

This guide explains how to run DP_GP_cluster with robust monitoring, logging, and crash recovery.

## Quick Start

1. **Setup**: `./setup_monitoring.sh`
2. **Run with monitoring**: `./run_dp_gp_monitored.sh`
3. **Run with auto-restart**: `./monitor_dp_gp.sh --auto-restart &`

## Scripts Overview

### 1. `run_dp_gp_monitored.sh` - Main Execution Script

Robust wrapper for DP_GP_cluster with comprehensive logging and notifications.

**Features:**
- Complete execution logging with timestamps
- System resource monitoring (memory, disk space)
- Crash detection and notification
- Email and Slack notifications
- Signal handling (SIGTERM, SIGINT, SIGHUP)
- 83-hour timeout protection
- Detailed error reporting

**Usage:**
```bash
./run_dp_gp_monitored.sh
```

### 2. `monitor_dp_gp.sh` - Process Monitor

External monitor that can watch and restart the main process.

**Features:**
- Continuous process monitoring
- Automatic restart on failure
- Memory usage tracking
- Configurable restart attempts
- Independent logging

**Usage:**
```bash
# Monitor only (no restart)
./monitor_dp_gp.sh

# Monitor with auto-restart (max 3 attempts)
./monitor_dp_gp.sh --auto-restart

# Custom restart attempts
./monitor_dp_gp.sh --auto-restart --max-attempts=5
```

### 3. `setup_monitoring.sh` - Configuration Setup

Interactive setup for notifications and system checks.

## Configuration

### Email Notifications
Configure in `run_dp_gp_monitored.sh`:
```bash
EMAIL="your.email@domain.com"
```

Requires `sendmail` (install: `sudo apt-get install mailutils`)

### Slack Notifications
Configure webhook URL in `run_dp_gp_monitored.sh`:
```bash
SLACK_WEBHOOK="https://hooks.slack.com/services/YOUR/WEBHOOK/URL"
```

### GitHub Notifications
Configure GitHub token and repository in `run_dp_gp_monitored.sh`:
```bash
GITHUB_TOKEN="your_github_personal_access_token"
GITHUB_REPO="username/repository"
```

The GitHub token needs "repo" permissions to create issues. Generate one at: https://github.com/settings/tokens

## Log Files

All logs are stored in `logs/` directory:

- `dp_gp_TIMESTAMP.log` - Main execution log
- `monitor_TIMESTAMP.log` - Monitor process log
- `dp_gp.pid` - Process ID file (temporary)

### Log Contents:
- System information (memory, disk, host)
- Complete command output
- Timestamps for all events
- Error messages and exit codes
- Resource usage tracking

## Running on Remote Server

### Option 1: Simple Background Execution
```bash
nohup ./run_dp_gp_monitored.sh > /dev/null 2>&1 &
```

### Option 2: Screen/Tmux Session
```bash
screen -S dp_gp
./run_dp_gp_monitored.sh
# Detach: Ctrl+A, D
# Reattach: screen -r dp_gp
```

### Option 3: With Auto-Restart Monitor
```bash
# Start monitor in background
./monitor_dp_gp.sh --auto-restart --max-attempts=5 &

# Start main process
./run_dp_gp_monitored.sh
```

## Troubleshooting

### Check Process Status
```bash
# Check if running
ps aux | grep DP_GP_cluster

# Check logs
tail -f logs/dp_gp_*.log

# Check monitor status
tail -f logs/monitor_*.log
```

### Common Issues

1. **Out of Memory**: Monitor logs will show memory warnings
   - Solution: Use machine with more RAM or enable swap
   
2. **Process Killed**: Look for "signal" messages in logs
   - Solution: Use `monitor_dp_gp.sh --auto-restart`
   
3. **Disk Space**: Logs will show disk usage warnings
   - Solution: Free up space or move to larger disk
   
4. **Network Issues**: Notification failures are logged
   - Solution: Check email/Slack configuration

### Manual Recovery
```bash
# Kill stuck processes
pkill -f DP_GP_cluster

# Clean up PID file
rm -f logs/dp_gp.pid

# Restart monitoring
./run_dp_gp_monitored.sh
```

## Notification Examples

### Email Format:
```
Subject: DP_GP_cluster STARTED/COMPLETED/FAILED

Timestamp: 2024-01-15 14:30:25
Status: STARTED
Message: DP_GP_cluster execution started with PID 12345
Log file: logs/dp_gp_20240115_143025.log
Working directory: /path/to/project
Host: compute-server-01
```

### Slack Format:
```
🧬 DP_GP_cluster STARTED
Host: compute-server-01
Time: 2024-01-15 14:30:25
Message: DP_GP_cluster execution started with PID 12345
```

## Performance Monitoring

The scripts automatically log:
- Memory usage every 5 minutes
- Disk space at start/end
- Process runtime
- System load information

High memory usage (>90%) triggers warnings in logs.
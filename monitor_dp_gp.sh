#!/bin/bash

# Process monitor for DP_GP_cluster with auto-restart capability
# Usage: ./monitor_dp_gp.sh [--auto-restart] [--max-attempts=N]

set -euo pipefail

# Default configuration
AUTO_RESTART=false
MAX_ATTEMPTS=3
CHECK_INTERVAL=300  # 5 minutes
LOG_DIR="logs"
MONITOR_LOG="${LOG_DIR}/monitor_$(date +%Y%m%d_%H%M%S).log"
PID_FILE="${LOG_DIR}/dp_gp.pid"
MAIN_SCRIPT="./run_dp_gp_monitored.sh"

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --auto-restart)
            AUTO_RESTART=true
            shift
            ;;
        --max-attempts=*)
            MAX_ATTEMPTS="${1#*=}"
            shift
            ;;
        -h|--help)
            echo "Usage: $0 [--auto-restart] [--max-attempts=N]"
            echo "  --auto-restart    Automatically restart failed processes"
            echo "  --max-attempts=N  Maximum restart attempts (default: 3)"
            exit 0
            ;;
        *)
            echo "Unknown option: $1"
            exit 1
            ;;
    esac
done

mkdir -p "${LOG_DIR}"

# Function to log with timestamp
log_message() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" | tee -a "${MONITOR_LOG}"
}

# Function to check if process is running
is_process_running() {
    if [[ -f "${PID_FILE}" ]]; then
        local pid=$(cat "${PID_FILE}")
        if kill -0 "$pid" 2>/dev/null; then
            return 0  # Process is running
        fi
    fi
    return 1  # Process is not running
}

# Function to get process status
get_process_status() {
    if [[ -f "${PID_FILE}" ]]; then
        local pid=$(cat "${PID_FILE}")
        if kill -0 "$pid" 2>/dev/null; then
            echo "RUNNING (PID: $pid)"
        else
            echo "STOPPED (PID file exists but process not running)"
        fi
    else
        echo "NOT_STARTED (no PID file)"
    fi
}

# Function to start the main process
start_process() {
    log_message "Starting DP_GP_cluster process..."
    
    if [[ ! -x "${MAIN_SCRIPT}" ]]; then
        log_message "ERROR: Main script ${MAIN_SCRIPT} not found or not executable"
        return 1
    fi
    
    # Start in background
    nohup "${MAIN_SCRIPT}" > /dev/null 2>&1 &
    local start_pid=$!
    
    # Wait a moment to see if it started successfully
    sleep 5
    
    if kill -0 "$start_pid" 2>/dev/null; then
        log_message "Process started successfully with PID $start_pid"
        return 0
    else
        log_message "Failed to start process"
        return 1
    fi
}

# Function to monitor memory usage
check_memory() {
    if [[ -f "${PID_FILE}" ]]; then
        local pid=$(cat "${PID_FILE}")
        if kill -0 "$pid" 2>/dev/null; then
            # Get memory usage in MB
            local memory_mb=$(ps -p "$pid" -o rss= | awk '{print int($1/1024)}' || echo "unknown")
            log_message "Process memory usage: ${memory_mb}MB"
            
            # Check if memory usage is too high (>90% of available memory)
            local total_mem=$(free -m | awk 'NR==2{print $2}' || echo "0")
            if [[ "$total_mem" -gt 0 && "$memory_mb" != "unknown" ]]; then
                local mem_percent=$((memory_mb * 100 / total_mem))
                if [[ $mem_percent -gt 90 ]]; then
                    log_message "WARNING: High memory usage detected (${mem_percent}%)"
                fi
            fi
        fi
    fi
}

# Main monitoring loop
main_monitor() {
    local attempt=1
    
    log_message "Starting DP_GP_cluster monitor"
    log_message "Configuration: AUTO_RESTART=$AUTO_RESTART, MAX_ATTEMPTS=$MAX_ATTEMPTS"
    log_message "Check interval: ${CHECK_INTERVAL} seconds"
    
    while true; do
        local status=$(get_process_status)
        log_message "Process status: $status"
        
        if is_process_running; then
            check_memory
        else
            log_message "Process is not running"
            
            if [[ "$AUTO_RESTART" == "true" && $attempt -le $MAX_ATTEMPTS ]]; then
                log_message "Attempting restart ($attempt/$MAX_ATTEMPTS)"
                
                if start_process; then
                    log_message "Restart successful"
                    attempt=1  # Reset attempt counter on successful start
                else
                    log_message "Restart failed"
                    ((attempt++))
                    
                    if [[ $attempt -gt $MAX_ATTEMPTS ]]; then
                        log_message "Maximum restart attempts reached. Stopping monitor."
                        break
                    fi
                fi
            else
                if [[ "$AUTO_RESTART" == "true" ]]; then
                    log_message "Maximum restart attempts reached. Process monitoring continues."
                else
                    log_message "Auto-restart disabled. Process monitoring continues."
                fi
            fi
        fi
        
        sleep "${CHECK_INTERVAL}"
    done
    
    log_message "Monitor stopped"
}

# Handle signals
trap 'log_message "Monitor interrupted"; exit 0' SIGTERM SIGINT

# Start monitoring
main_monitor
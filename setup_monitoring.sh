#!/bin/bash

# Setup script for DP_GP_cluster monitoring
# This script helps configure notifications and test the monitoring system

set -euo pipefail

echo "DP_GP_cluster Monitoring Setup"
echo "=============================="

# Create logs directory
mkdir -p logs
echo "✓ Created logs directory"

# Check if email is configured
read -p "Enter your email for notifications (or press Enter to skip): " email
if [[ -n "$email" ]]; then
    # Update the monitoring script with email
    sed -i.bak "s/EMAIL=\"\"/EMAIL=\"$email\"/" run_dp_gp_monitored.sh
    echo "✓ Email configured: $email"
    
    # Test email functionality
    if command -v sendmail &> /dev/null; then
        echo "✓ sendmail is available for email notifications"
    else
        echo "⚠ sendmail not found. Install mailutils: sudo apt-get install mailutils"
    fi
else
    echo "⚠ Email notifications disabled"
fi

# Check for Slack webhook
read -p "Enter Slack webhook URL (or press Enter to skip): " slack_webhook
if [[ -n "$slack_webhook" ]]; then
    # Update the monitoring script with Slack webhook
    sed -i.bak "s|SLACK_WEBHOOK=\"\"|SLACK_WEBHOOK=\"$slack_webhook\"|" run_dp_gp_monitored.sh
    echo "✓ Slack webhook configured"
    
    # Test Slack functionality
    if command -v curl &> /dev/null; then
        echo "✓ curl is available for Slack notifications"
    else
        echo "⚠ curl not found. Install curl: sudo apt-get install curl"
    fi
else
    echo "⚠ Slack notifications disabled"
fi

# Check for GitHub token
read -p "Enter GitHub personal access token (or press Enter to skip): " github_token
if [[ -n "$github_token" ]]; then
    # Update the monitoring script with GitHub token
    sed -i.bak "s|GITHUB_TOKEN=\"\"|GITHUB_TOKEN=\"$github_token\"|" run_dp_gp_monitored.sh
    echo "✓ GitHub notifications configured"
    
    # Test GitHub functionality
    if command -v curl &> /dev/null; then
        echo "✓ curl is available for GitHub notifications"
    else
        echo "⚠ curl not found. Install curl for GitHub notifications"
    fi
else
    echo "⚠ GitHub notifications disabled"
fi

# Check system resources
echo ""
echo "System Resource Check:"
echo "======================"

if command -v free &> /dev/null; then
    echo "Memory:"
    free -h
else
    echo "⚠ 'free' command not available"
fi

if command -v df &> /dev/null; then
    echo "Disk space:"
    df -h .
else
    echo "⚠ 'df' command not available"
fi

# Check if input file exists
if [[ -f "tissue_all/merged.txt" ]]; then
    echo "✓ Input file found: $(ls -lh tissue_all/merged.txt | awk '{print $5}')"
else
    echo "⚠ Input file tissue_all/merged.txt not found"
fi

# Check if DP_GP_cluster.py is available
if command -v DP_GP_cluster.py &> /dev/null; then
    echo "✓ DP_GP_cluster.py is available"
else
    echo "⚠ DP_GP_cluster.py not found. Make sure it's installed and in PATH"
fi

echo ""
echo "Setup complete!"
echo "==============="
echo ""
echo "Usage Examples:"
echo "1. Run with monitoring:           ./run_dp_gp_monitored.sh"
echo "2. Run with auto-restart:         ./monitor_dp_gp.sh --auto-restart &"
echo "3. Monitor existing process:      ./monitor_dp_gp.sh"
echo ""
echo "Log files will be stored in the 'logs/' directory"
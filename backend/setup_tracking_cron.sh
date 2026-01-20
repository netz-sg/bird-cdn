#!/bin/bash
#
# Setup Script: NGINX Log Aggregation Cron Job
# This script sets up a cron job to aggregate NGINX access logs every hour
#

set -e

echo "🔧 Setting up NGINX Log Aggregation Cron Job..."

# Ensure nginx logs directory is accessible
if [ ! -d "/var/log/nginx" ]; then
    echo "⚠️  /var/log/nginx not found, will use shared volume"
fi

# Create cron job script
cat > /app/run_log_aggregation.sh << 'EOF'
#!/bin/bash
# Run log aggregation and log output
/usr/local/bin/python3 /app/cron_aggregate_logs.py >> /var/log/tracking_cron.log 2>&1
EOF

chmod +x /app/run_log_aggregation.sh
chmod +x /app/cron_aggregate_logs.py

# Add cron job (every hour at minute 5)
CRON_CMD="5 * * * * /app/run_log_aggregation.sh"

# Check if cron job already exists
if crontab -l 2>/dev/null | grep -q "run_log_aggregation"; then
    echo "✅ Cron job already exists"
else
    # Add to crontab
    (crontab -l 2>/dev/null; echo "$CRON_CMD") | crontab -
    echo "✅ Cron job added: runs every hour at minute 5"
fi

# Also add daily cleanup (optional - keeps last 7 days of logs)
CLEANUP_CMD="0 2 * * * find /var/log/nginx -name 'access.log.*' -mtime +7 -delete"
if ! crontab -l 2>/dev/null | grep -q "access.log.*"; then
    (crontab -l 2>/dev/null; echo "$CLEANUP_CMD") | crontab -
    echo "✅ Log cleanup job added: runs daily at 2 AM"
fi

# Start cron service (if not running)
if ! pgrep -x "cron" > /dev/null; then
    echo "🚀 Starting cron service..."
    cron
    echo "✅ Cron service started"
else
    echo "✅ Cron service already running"
fi

# Display current crontab
echo ""
echo "📋 Current crontab:"
crontab -l

echo ""
echo "✅ Setup complete!"
echo "💡 To manually trigger aggregation, run: curl -X POST http://localhost:8000/api/tracking/aggregate-logs"

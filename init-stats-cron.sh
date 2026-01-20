#!/bin/bash
# Setup Cron Job für stündliche Stats-Aggregation

echo "🔧 Setting up stats aggregation cron job..."

# Create cron entry (runs every hour at :05)
CRON_CMD="5 * * * * docker-compose -f /opt/cdn-network/docker-compose.yml exec -T backend-api python cron_aggregate_logs.py >> /var/log/cdn-stats.log 2>&1"

# Add to crontab
(crontab -l 2>/dev/null; echo "$CRON_CMD") | crontab -

echo "✅ Cron job installed: Runs every hour at :05"
echo "📄 Logs: /var/log/cdn-stats.log"
echo ""
echo "To manually trigger:"
echo "  docker-compose exec backend-api python cron_aggregate_logs.py"

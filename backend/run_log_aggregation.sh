#!/bin/bash
# Run log aggregation and log output
/usr/local/bin/python3 /app/cron_aggregate_logs.py >> /var/log/tracking_cron.log 2>&1

#!/usr/bin/env python3
"""
Cron Job: Aggregiere NGINX Access Logs in BandwidthLog
Läuft stündlich via systemd-timer oder cron
"""
import sys
import os
from pathlib import Path

# Add backend directory to path
backend_dir = Path(__file__).parent
sys.path.insert(0, str(backend_dir))

from routers.tracking import aggregate_bandwidth_logs

if __name__ == "__main__":
    print("🔄 Starting log aggregation...")
    aggregate_bandwidth_logs()
    print("✅ Log aggregation complete")

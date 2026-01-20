# Quick Start: Enable CDN Tracking

This guide gets tracking working in 5 minutes.

---

## Prerequisites

- Docker and Docker Compose installed
- Bird-CDN already running
- Valid API key or JWT token

---

## Step 1: Rebuild Backend (2 minutes)

```powershell
cd d:\Dev\cdn-tourdiary

# Rebuild backend with cron support
docker-compose build backend-api

# Restart
docker-compose up -d backend-api
```

**What this does:**
- Adds cron package
- Sets up hourly log aggregation
- Shares NGINX logs with backend

---

## Step 2: Verify Setup (30 seconds)

```powershell
# Check cron is running
docker-compose exec backend-api pgrep -x cron

# View crontab (should show hourly job)
docker-compose exec backend-api crontab -l
```

**Expected output:**
```
5 * * * * /app/run_log_aggregation.sh
0 2 * * * find /var/log/nginx -name 'access.log.*' -mtime +7 -delete
```

---

## Step 3: Generate Test Traffic (1 minute)

```powershell
# Make 5 requests to a test file
for ($i=1; $i -le 5; $i++) {
    curl -I http://localhost/media/test.webp
    Start-Sleep -Seconds 1
}
```

---

## Step 4: Trigger Aggregation (30 seconds)

```powershell
# Get API key (or use existing one)
$API_KEY = "cdn_j5kzzQNHVKJFHSNZGGuiTVNk48-oe8aH433YWiYShGI"

# Trigger log aggregation
$result = Invoke-RestMethod -Method POST `
    -Uri "http://localhost:8000/api/tracking/aggregate-logs" `
    -Headers @{"X-API-Key" = $API_KEY}

# Check results
Write-Host "Status: $($result.status)"
Write-Host "Lines processed: $($result.lines_processed)"
Write-Host "Entries updated: $($result.entries_updated)"
```

**Expected:**
```
Status: success
Lines processed: 5
Entries updated: 5
```

---

## Step 5: Verify Database (1 minute)

```powershell
# Connect to database
docker-compose exec postgres psql -U cdn -d cdn -c "
SELECT 
    path, 
    hit_count, 
    miss_count, 
    bytes_served 
FROM cache_entries 
LIMIT 5;"
```

**Expected:** Non-empty results showing paths with counts

---

## Troubleshooting

### No data after aggregation?

```powershell
# Check if logs exist
docker-compose exec backend-api ls -la /var/log/nginx/

# Check if logs have content
docker-compose exec backend-api wc -l /var/log/nginx/access.log

# Run aggregation manually with output
docker-compose exec backend-api python3 /app/cron_aggregate_logs.py
```

### Cron not running?

```powershell
# Restart backend
docker-compose restart backend-api

# Check setup script ran
docker-compose logs backend-api | Select-String "cron"
```

---

## Next Steps

1. **Wait for cron:** Automatic aggregation runs every hour at minute 5
2. **Check stats API:** `http://localhost:8000/api/stats/overview`
3. **View frontend:** Dashboard should show real data

---

## Monitoring

```powershell
# Watch aggregation logs
docker-compose exec backend-api tail -f /var/log/tracking_cron.log

# Watch backend logs
docker-compose logs -f backend-api | Select-String "Aggregated"
```

---

## Success Indicators

✅ Cron job in crontab  
✅ `/var/log/nginx/access.log` accessible from backend  
✅ Aggregation returns `status: "success"`  
✅ `cache_entries` table has rows  
✅ `uploaded_files` shows `download_count > 0`  

**Tracking is live!** 📊

# CDN Analytics & Tracking Implementation

**Date:** 2026-01-20  
**Implementation:** Batch Log Aggregation with Cron  
**Status:** ✅ IMPLEMENTED

---

## Executive Summary

Implemented automated tracking system for Bird-CDN that parses NGINX access logs hourly and updates database statistics:
- ✅ `uploaded_files.download_count` and `bandwidth_used` now tracked
- ✅ `cache_entries` table populated with hit/miss stats
- ✅ `bandwidth_logs` table updated with hourly statistics
- ✅ Cron job runs every hour automatically
- ✅ Manual triggering via API endpoint available

---

## Architecture

### Approach: Option B - Batch Log Aggregation

**Why not Lua (Option A)?**
- Standard NGINX image doesn't include Lua modules
- Requires OpenResty or custom NGINX build
- More complex deployment

**Why Batch Aggregation?**
- ✅ Works with standard NGINX
- ✅ Low performance impact
- ✅ Easier to deploy and maintain
- ✅ Already had partial infrastructure

---

## Components

### 1. Updated Tracking API (`backend/routers/tracking.py`)

**New Pydantic Models:**
```python
class TrackDownloadPayload(BaseModel):
    file_id: int
    bytes_sent: int = 0
    cache_status: Optional[str] = "UNKNOWN"
    user_agent: Optional[str] = None
    ip_address: Optional[str] = None

class TrackCacheHitPayload(BaseModel):
    path: str
    cache_status: str  # HIT/MISS/BYPASS/EXPIRED/STALE
    bytes_sent: int = 0
    response_time: Optional[float] = None

class AggregateLogsResponse(BaseModel):
    status: str
    lines_processed: int
    entries_updated: int
    errors: int
```

**Endpoints:**

| Endpoint | Method | Auth | Purpose |
|----------|--------|------|---------|
| `/api/tracking/track/download` | POST | JWT/API Key | Track single file download |
| `/api/tracking/track/cache-hit` | POST | JWT/API Key | Track cache hit/miss |
| `/api/tracking/aggregate-logs` | POST | JWT/API Key | Trigger log aggregation |

### 2. Log Parser (`parse_nginx_log_line`)

Parses NGINX `cdn_format` logs:
```
IP - USER [timestamp] "METHOD /path HTTP/1.1" status bytes "referer" "user-agent" cache_status=STATUS
```

**Features:**
- Regex pattern matching
- Filters only CDN asset requests (images/videos)
- Extracts: path, bytes_sent, cache_status, status code
- Error handling for malformed lines

### 3. Aggregation Function (`aggregate_bandwidth_logs`)

**What it does:**
1. Reads `/var/log/nginx/access.log`
2. Parses each line
3. Updates `BandwidthLog` (hourly aggregates)
4. Updates `CacheEntry` (per-file cache stats)
5. Updates `UploadedFile` (download counts)

**Database Updates:**

**BandwidthLog** (hourly stats):
- `requests` - Total requests
- `bytes_sent` - Total bandwidth
- `cache_hits` - HIT/STALE count
- `cache_misses` - MISS/BYPASS count
- `status_200`, `status_206`, `status_304`, `status_404`, `status_500`

**CacheEntry** (per-file):
- `hit_count` - Number of cache hits
- `miss_count` - Number of cache misses
- `bytes_served` - Total bytes served
- `last_hit` / `last_miss` - Timestamps
- `is_cached` - Boolean flag

**UploadedFile** (per-file):
- `download_count` - Total downloads
- `bandwidth_used` - Total bytes transferred
- `last_accessed` - Last access timestamp

### 4. Cron Setup (`setup_tracking_cron.sh`)

**What it does:**
- Installs cron job: `5 * * * *` (every hour at minute 5)
- Creates wrapper script `/app/run_log_aggregation.sh`
- Starts cron service in container
- Optional: Daily log cleanup (keeps last 7 days)

### 5. Startup Script (`start.sh`)

**Sequence:**
1. Run `setup_tracking_cron.sh`
2. Start cron service
3. Start FastAPI with uvicorn

---

## Deployment

### Step 1: Rebuild Backend Container

```powershell
# Navigate to project directory
cd d:\Dev\cdn-tourdiary

# Rebuild backend with cron support
docker-compose build backend-api

# Restart services
docker-compose up -d
```

### Step 2: Verify Cron Setup

```powershell
# Check if cron is running
docker-compose exec backend-api pgrep -x cron

# View crontab
docker-compose exec backend-api crontab -l

# Expected output:
# 5 * * * * /app/run_log_aggregation.sh
# 0 2 * * * find /var/log/nginx -name 'access.log.*' -mtime +7 -delete
```

### Step 3: Check Log File Access

```powershell
# Verify NGINX logs are accessible from backend
docker-compose exec backend-api ls -la /var/log/nginx/

# Should show access.log and error.log
```

### Step 4: Manual Test

```powershell
# Trigger aggregation manually
curl -X POST "http://localhost:8000/api/tracking/aggregate-logs" \
  -H "X-API-Key: cdn_j5kzzQNHVKJFHSNZGGuiTVNk48-oe8aH433YWiYShGI"

# Expected response:
# {
#   "status": "success",
#   "lines_processed": 123,
#   "entries_updated": 45,
#   "errors": 0
# }
```

---

## Verification Tests

### Test 1: Generate Traffic

```powershell
# Make 3 requests to the same file
curl -I http://localhost/media/test.webp
Start-Sleep -Seconds 1
curl -I http://localhost/media/test.webp
Start-Sleep -Seconds 1
curl -I http://localhost/media/test.webp
```

### Test 2: Trigger Aggregation

```powershell
# Get JWT token
$response = Invoke-RestMethod -Method POST -Uri "http://localhost:8000/api/auth/login" `
  -ContentType "application/json" `
  -Body '{"username":"Sebastian","password":"your_password"}'
$token = $response.access_token

# Trigger aggregation
$result = Invoke-RestMethod -Method POST -Uri "http://localhost:8000/api/tracking/aggregate-logs" `
  -Headers @{Authorization = "Bearer $token"}

Write-Host "Lines processed: $($result.lines_processed)"
Write-Host "Entries updated: $($result.entries_updated)"
```

### Test 3: Check Database

```powershell
# Connect to database
docker-compose exec postgres psql -U cdn -d cdn

# Check cache_entries
SELECT path, hit_count, miss_count, bytes_served 
FROM cache_entries 
WHERE path LIKE '%test.webp%';

# Check uploaded_files
SELECT filename, download_count, bandwidth_used 
FROM uploaded_files 
WHERE path LIKE '%test.webp%';

# Check bandwidth_logs
SELECT hour, requests, cache_hits, cache_misses, bytes_sent 
FROM bandwidth_logs 
ORDER BY hour DESC 
LIMIT 5;
```

### Test 4: Wait for Cron

```powershell
# Wait for next hour (cron runs at minute 5)
# Then check cron log
docker-compose exec backend-api cat /var/log/tracking_cron.log
```

---

## Expected Results

### Before Implementation
```sql
-- cache_entries table
SELECT COUNT(*) FROM cache_entries;
-- Result: 0

-- uploaded_files stats
SELECT download_count, bandwidth_used FROM uploaded_files LIMIT 5;
-- Result: All zeros
```

### After Implementation
```sql
-- cache_entries table (after traffic + aggregation)
SELECT COUNT(*) FROM cache_entries;
-- Result: > 0 (shows cached files)

-- Example cache entry
SELECT * FROM cache_entries WHERE path = '/media/test.webp';
-- Result:
-- path: /media/test.webp
-- hit_count: 2
-- miss_count: 1
-- bytes_served: 45678
-- is_cached: true
-- last_hit: 2026-01-20 13:25:00

-- uploaded_files stats
SELECT filename, download_count, bandwidth_used FROM uploaded_files WHERE path = '/media/test.webp';
-- Result:
-- filename: test.webp
-- download_count: 3
-- bandwidth_used: 45678
```

---

## API Usage Examples

### Track Download (Manual)

```bash
curl -X POST "http://localhost:8000/api/tracking/track/download" \
  -H "Content-Type: application/json" \
  -H "X-API-Key: cdn_xxx" \
  -d '{
    "file_id": 123,
    "bytes_sent": 15420,
    "cache_status": "HIT",
    "user_agent": "Mozilla/5.0...",
    "ip_address": "192.168.1.100"
  }'
```

### Track Cache Hit (Manual)

```bash
curl -X POST "http://localhost:8000/api/tracking/track/cache-hit" \
  -H "Content-Type: application/json" \
  -H "X-API-Key: cdn_xxx" \
  -d '{
    "path": "/media/image.jpg",
    "cache_status": "HIT",
    "bytes_sent": 25600,
    "response_time": 0.023
  }'
```

### Aggregate Logs

```bash
# Synchronous (wait for completion)
curl -X POST "http://localhost:8000/api/tracking/aggregate-logs" \
  -H "X-API-Key: cdn_xxx"

# Background (non-blocking)
curl -X POST "http://localhost:8000/api/tracking/aggregate-logs?background=true" \
  -H "X-API-Key: cdn_xxx"
```

---

## Monitoring

### Check Cron Logs

```powershell
# View aggregation logs
docker-compose exec backend-api tail -f /var/log/tracking_cron.log
```

### Check Application Logs

```powershell
# View backend logs
docker-compose logs -f backend-api | Select-String "Aggregated"

# Look for:
# ✅ Aggregated 1234 log lines, updated 567 entries
```

### Monitor Database Growth

```sql
-- Trend of bandwidth over time
SELECT 
    DATE_TRUNC('day', hour) as day,
    SUM(requests) as total_requests,
    SUM(bytes_sent) / (1024*1024*1024) as gb_served,
    AVG(cache_hits::float / NULLIF(cache_hits + cache_misses, 0) * 100) as cache_hit_rate
FROM bandwidth_logs
GROUP BY day
ORDER BY day DESC
LIMIT 7;
```

---

## Troubleshooting

### Issue: No data after aggregation

**Check:**
```powershell
# 1. Is NGINX generating logs?
docker-compose exec nginx-cdn ls -la /var/log/nginx/
docker-compose exec nginx-cdn tail /var/log/nginx/access.log

# 2. Can backend access logs?
docker-compose exec backend-api ls -la /var/log/nginx/
docker-compose exec backend-api head /var/log/nginx/access.log

# 3. Run aggregation manually with debug
docker-compose exec backend-api python3 /app/cron_aggregate_logs.py
```

### Issue: Cron not running

**Fix:**
```powershell
# Restart backend
docker-compose restart backend-api

# Check cron process
docker-compose exec backend-api ps aux | grep cron

# Manually start cron
docker-compose exec backend-api cron

# Re-setup cron
docker-compose exec backend-api bash /app/setup_tracking_cron.sh
```

### Issue: Parse errors

**Debug:**
```powershell
# Check log format matches parser
docker-compose exec nginx-cdn cat /etc/nginx/nginx.conf | grep log_format

# Test parser on real log line
docker-compose exec backend-api python3 << 'EOF'
from routers.tracking import parse_nginx_log_line
line = '192.168.1.1 - - [20/Jan/2026:13:45:23 +0000] "GET /media/test.webp HTTP/1.1" 200 15420 "-" "Mozilla/5.0" cache_status=HIT'
print(parse_nginx_log_line(line))
EOF
```

---

## Performance Considerations

### Log File Size
- NGINX access.log grows ~1MB per 10,000 requests
- Cron runs hourly, processes all lines each time
- Consider log rotation:
  ```nginx
  # In nginx.conf or via logrotate
  access_log /var/log/nginx/access.log cdn_format;
  ```

### Database Impact
- Batch updates reduce DB load vs. per-request tracking
- Indexes on `path` columns improve lookup speed
- Consider partitioning `bandwidth_logs` by month for large datasets

### Future Optimizations

1. **Incremental Processing:**
   - Track last processed line number
   - Only parse new entries

2. **Log Streaming:**
   - Use `tail -f` with inotify
   - Real-time processing

3. **Async Processing:**
   - Use Celery/Redis queue
   - Parallel processing for large logs

---

## Configuration

### Adjust Cron Schedule

```bash
# Edit cron timing in setup_tracking_cron.sh
# Current: 5 * * * * (hourly at minute 5)
# 
# Examples:
# Every 30 minutes: */30 * * * *
# Every 5 minutes: */5 * * * *
# Daily at 3 AM: 0 3 * * *
```

### Log Retention

```bash
# In setup_tracking_cron.sh
# Current: Keeps 7 days
# 0 2 * * * find /var/log/nginx -name 'access.log.*' -mtime +7 -delete

# Keep 30 days:
# 0 2 * * * find /var/log/nginx -name 'access.log.*' -mtime +30 -delete
```

---

## Summary

| Feature | Status | Notes |
|---------|--------|-------|
| Log Parsing | ✅ | Parses NGINX cdn_format logs |
| Database Updates | ✅ | Updates 3 tables (bandwidth_logs, cache_entries, uploaded_files) |
| Cron Job | ✅ | Runs hourly at minute 5 |
| Manual Trigger | ✅ | Via POST /api/tracking/aggregate-logs |
| Authentication | ✅ | JWT or API Key required |
| Error Handling | ✅ | Graceful fallback, logging |
| Monitoring | ✅ | Cron logs + application logs |
| Docker Integration | ✅ | Shared volumes for logs |

---

## Next Steps (Optional Enhancements)

1. **Real-time Tracking:** Implement NGINX Lua module for instant updates
2. **Grafana Dashboard:** Visualize bandwidth and cache hit rates
3. **Alerts:** Notify on low cache hit rate or high error rates
4. **Geo-IP Tracking:** Add IP geolocation to track user locations
5. **CDN Analytics API:** Expose aggregated stats via REST API
6. **Export to ClickHouse:** For long-term analytics storage

---

## Support

For issues or questions:
- Check logs: `/var/log/tracking_cron.log`
- Manual test: `python3 /app/cron_aggregate_logs.py`
- API docs: `http://localhost:8000/docs`

**Tracking is now live!** 📊🚀

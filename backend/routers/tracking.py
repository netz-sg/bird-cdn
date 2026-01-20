"""
Background task für Bandwidth & Stats Tracking
Parsed NGINX Access Logs und schreibt in BandwidthLog
"""
from fastapi import APIRouter, BackgroundTasks
from sqlalchemy.orm import Session
from sqlalchemy import func
from database import SessionLocal
from models import BandwidthLog, UploadedFile, CacheEntry
from datetime import datetime, timedelta
import re
from pathlib import Path
from config import settings

router = APIRouter()


def parse_nginx_log_line(line: str):
    """Parse eine NGINX Access Log Zeile"""
    # Log Format: IP - - [timestamp] "METHOD /path HTTP/1.1" status bytes_sent "referer" "user-agent" cache_status=STATUS
    pattern = r'(\S+) - \S+ \[(.*?)\] "(\S+) (\S+) \S+" (\d+) (\d+) .* cache_status=(\S+)'
    match = re.match(pattern, line)
    
    if match:
        return {
            'ip': match.group(1),
            'timestamp': match.group(2),
            'method': match.group(3),
            'path': match.group(4),
            'status': int(match.group(5)),
            'bytes_sent': int(match.group(6)),
            'cache_status': match.group(7)
        }
    return None


def aggregate_bandwidth_logs():
    """
    Aggregiere NGINX Logs in stündliche Bandwidth-Statistiken
    """
    db = SessionLocal()
    
    try:
        # Current hour
        now = datetime.now().replace(minute=0, second=0, microsecond=0)
        
        # Check if log entry for this hour exists
        existing = db.query(BandwidthLog).filter(BandwidthLog.hour == now).first()
        
        if not existing:
            existing = BandwidthLog(
                hour=now,
                requests=0,
                bytes_sent=0,
                cache_hits=0,
                cache_misses=0,
                status_200=0,
                status_206=0,
                status_304=0,
                status_404=0,
                status_500=0
            )
            db.add(existing)
            db.commit()
        
        # Parse NGINX access log (letzte Stunde)
        log_file = Path("/var/log/nginx/access.log")
        
        if not log_file.exists():
            print(f"⚠️ NGINX log file not found: {log_file}")
            return
        
        one_hour_ago = now - timedelta(hours=1)
        
        with open(log_file, 'r') as f:
            for line in f:
                parsed = parse_nginx_log_line(line)
                if not parsed:
                    continue
                
                # Update counters
                existing.requests += 1
                existing.bytes_sent += parsed['bytes_sent']
                
                # Cache status
                if parsed['cache_status'] in ['HIT', 'STALE']:
                    existing.cache_hits += 1
                elif parsed['cache_status'] in ['MISS', 'BYPASS', 'EXPIRED']:
                    existing.cache_misses += 1
                
                # Status codes
                status = parsed['status']
                if status == 200:
                    existing.status_200 += 1
                elif status == 206:
                    existing.status_206 += 1
                elif status == 304:
                    existing.status_304 += 1
                elif status == 404:
                    existing.status_404 += 1
                elif status >= 500:
                    existing.status_500 += 1
        
        db.commit()
        print(f"✅ Bandwidth logs aggregated for {now}")
        
    except Exception as e:
        print(f"❌ Error aggregating bandwidth logs: {e}")
        db.rollback()
    finally:
        db.close()


@router.post("/track/download/{file_id}")
async def track_download(file_id: int, bytes_sent: int = 0):
    """
    Track a file download (called internally)
    """
    db = SessionLocal()
    
    try:
        file = db.query(UploadedFile).filter(UploadedFile.id == file_id).first()
        if file:
            file.download_count = (file.download_count or 0) + 1
            file.bandwidth_used = (file.bandwidth_used or 0) + bytes_sent
            db.commit()
            
        return {"status": "ok"}
    except Exception as e:
        db.rollback()
        return {"status": "error", "detail": str(e)}
    finally:
        db.close()


@router.post("/track/cache-hit")
async def track_cache_hit(path: str, bytes_sent: int = 0):
    """
    Track cache hit/miss
    """
    db = SessionLocal()
    
    try:
        cache_entry = db.query(CacheEntry).filter(CacheEntry.path == path).first()
        
        if not cache_entry:
            cache_entry = CacheEntry(
                path=path,
                hit_count=0,
                miss_count=0,
                bytes_served=0,
                is_cached=True
            )
            db.add(cache_entry)
        
        cache_entry.hit_count = (cache_entry.hit_count or 0) + 1
        cache_entry.bytes_served = (cache_entry.bytes_served or 0) + bytes_sent
        cache_entry.last_hit = datetime.now()
        
        db.commit()
        return {"status": "ok"}
    except Exception as e:
        db.rollback()
        return {"status": "error", "detail": str(e)}
    finally:
        db.close()


@router.post("/aggregate-logs")
async def trigger_log_aggregation(background_tasks: BackgroundTasks):
    """
    Manuell Logs aggregieren (kann via Cron aufgerufen werden)
    """
    background_tasks.add_task(aggregate_bandwidth_logs)
    return {"status": "aggregation started"}

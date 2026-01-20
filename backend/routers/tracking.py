"""
Background task für Bandwidth & Stats Tracking
Parsed NGINX Access Logs und schreibt in BandwidthLog
"""
from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import func
from database import SessionLocal, get_db
from models import BandwidthLog, UploadedFile, CacheEntry
from datetime import datetime, timedelta
from auth import get_current_user_or_api_key
from pydantic import BaseModel, Field
from typing import Optional
import re
from pathlib import Path
from config import settings
import logging

logger = logging.getLogger(__name__)

router = APIRouter()


# Pydantic Models for Tracking Payloads
class TrackDownloadPayload(BaseModel):
    """Payload for tracking file downloads"""
    file_id: int = Field(..., description="ID of the uploaded file")
    bytes_sent: int = Field(default=0, ge=0, description="Number of bytes sent")
    cache_status: Optional[str] = Field(default="UNKNOWN", description="Cache status (HIT/MISS/BYPASS)")
    user_agent: Optional[str] = Field(default=None, max_length=500)
    ip_address: Optional[str] = Field(default=None, max_length=45)


class TrackCacheHitPayload(BaseModel):
    """Payload for tracking cache hits/misses"""
    path: str = Field(..., min_length=1, max_length=500, description="CDN path of the file")
    cache_status: str = Field(..., description="Cache status (HIT/MISS/BYPASS/EXPIRED/STALE)")
    bytes_sent: int = Field(default=0, ge=0, description="Number of bytes sent")
    response_time: Optional[float] = Field(default=None, ge=0, description="Response time in seconds")


class AggregateLogsResponse(BaseModel):
    """Response from log aggregation"""
    status: str
    lines_processed: int
    entries_updated: int
    errors: int


def parse_nginx_log_line(line: str) -> Optional[dict]:
    """
    Parse NGINX Access Log Line
    
    Format: IP - USER [timestamp] "METHOD /path HTTP/1.1" status bytes_sent "referer" "user-agent" cache_status=STATUS
    """
    # Updated pattern to match cdn_format from nginx.conf
    pattern = r'([\d\.]+) - (\S+) \[([^\]]+)\] \"(\S+) ([^\"]+) [^\"]+\" (\d+) (\d+) \"([^\"]*)\" \"([^\"]*)\" cache_status=(\S+)'
    match = re.match(pattern, line)
    
    if match:
        try:
            path = match.group(5)
            # Only track CDN asset requests (bucket/file pattern)
            if not re.match(r'^/[^/]+/.*\.(jpg|jpeg|png|gif|webp|svg|ico|mp4|webm|avi|mov|mkv|flv|m4v)', path, re.IGNORECASE):
                return None
                
            return {
                'ip': match.group(1),
                'user': match.group(2),
                'timestamp': match.group(3),
                'method': match.group(4),
                'path': path,
                'status': int(match.group(6)),
                'bytes_sent': int(match.group(7)),
                'referer': match.group(8),
                'user_agent': match.group(9),
                'cache_status': match.group(10)
            }
        except (ValueError, IndexError) as e:
            logger.warning(f"Error parsing log line: {e}")
            return None
    return None


def aggregate_bandwidth_logs() -> dict:
    """
    Aggregiere NGINX Logs in stündliche Bandwidth-Statistiken und update file/cache stats
    
    Returns:
        dict: Statistics about processed logs
    """
    db = SessionLocal()
    lines_processed = 0
    entries_updated = 0
    errors = 0
    
    try:
        # Current hour for BandwidthLog
        now = datetime.now().replace(minute=0, second=0, microsecond=0)
        
        # Get or create BandwidthLog entry
        bandwidth_log = db.query(BandwidthLog).filter(BandwidthLog.hour == now).first()
        
        if not bandwidth_log:
            bandwidth_log = BandwidthLog(
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
            db.add(bandwidth_log)
            db.flush()
        
        # Parse NGINX access log
        log_file = Path("/var/log/nginx/access.log")
        
        if not log_file.exists():
            logger.warning(f"NGINX log file not found: {log_file}")
            # Try alternative location
            log_file = Path("/app/nginx_logs/access.log")
            if not log_file.exists():
                return {
                    "status": "error",
                    "lines_processed": 0,
                    "entries_updated": 0,
                    "errors": 1,
                    "message": "Log file not found"
                }
        
        # Track processed files to avoid duplicate updates
        processed_files = {}
        
        with open(log_file, 'r', encoding='utf-8', errors='ignore') as f:
            for line in f:
                lines_processed += 1
                parsed = parse_nginx_log_line(line)
                
                if not parsed:
                    continue
                
                try:
                    # Update BandwidthLog counters
                    bandwidth_log.requests += 1
                    bandwidth_log.bytes_sent += parsed['bytes_sent']
                    
                    # Cache status
                    cache_status = parsed['cache_status']
                    if cache_status in ['HIT', 'STALE']:
                        bandwidth_log.cache_hits += 1
                    elif cache_status in ['MISS', 'BYPASS', 'EXPIRED', 'UPDATING']:
                        bandwidth_log.cache_misses += 1
                    
                    # Status codes
                    status = parsed['status']
                    if status == 200:
                        bandwidth_log.status_200 += 1
                    elif status == 206:
                        bandwidth_log.status_206 += 1
                    elif status == 304:
                        bandwidth_log.status_304 += 1
                    elif status == 404:
                        bandwidth_log.status_404 += 1
                    elif status >= 500:
                        bandwidth_log.status_500 += 1
                    
                    # Update UploadedFile statistics
                    path = parsed['path']
                    if path not in processed_files:
                        processed_files[path] = {'downloads': 0, 'bytes': 0}
                    
                    processed_files[path]['downloads'] += 1
                    processed_files[path]['bytes'] += parsed['bytes_sent']
                    
                    # Update CacheEntry
                    cache_entry = db.query(CacheEntry).filter(CacheEntry.path == path).first()
                    
                    if not cache_entry:
                        cache_entry = CacheEntry(
                            path=path,
                            cache_key=f"httpGETlocalhost{path}",
                            hit_count=0,
                            miss_count=0,
                            bytes_served=0,
                            is_cached=False,
                            created_at=datetime.now()
                        )
                        db.add(cache_entry)
                        db.flush()
                    
                    # Update cache entry stats
                    if cache_status in ['HIT', 'STALE']:
                        cache_entry.hit_count = (cache_entry.hit_count or 0) + 1
                        cache_entry.last_hit = datetime.now()
                        cache_entry.is_cached = True
                    elif cache_status in ['MISS', 'BYPASS', 'EXPIRED']:
                        cache_entry.miss_count = (cache_entry.miss_count or 0) + 1
                        cache_entry.last_miss = datetime.now()
                    
                    cache_entry.bytes_served = (cache_entry.bytes_served or 0) + parsed['bytes_sent']
                    cache_entry.updated_at = datetime.now()
                    
                    entries_updated += 1
                    
                except Exception as e:
                    logger.error(f"Error processing log entry: {e}")
                    errors += 1
                    continue
        
        # Batch update UploadedFile records
        for path, stats in processed_files.items():
            try:
                uploaded_file = db.query(UploadedFile).filter(UploadedFile.path == path).first()
                if uploaded_file:
                    uploaded_file.download_count = (uploaded_file.download_count or 0) + stats['downloads']
                    uploaded_file.bandwidth_used = (uploaded_file.bandwidth_used or 0) + stats['bytes']
                    uploaded_file.last_accessed = datetime.now()
            except Exception as e:
                logger.error(f"Error updating file {path}: {e}")
                errors += 1
        
        db.commit()
        logger.info(f" Aggregated {lines_processed} log lines, updated {entries_updated} entries")
        
        return {
            "status": "success",
            "lines_processed": lines_processed,
            "entries_updated": entries_updated,
            "errors": errors
        }
        
    except Exception as e:
        logger.error(f" Error aggregating bandwidth logs: {e}")
        db.rollback()
        return {
            "status": "error",
            "lines_processed": lines_processed,
            "entries_updated": entries_updated,
            "errors": errors + 1,
            "message": str(e)
        }
    finally:
        db.close()


@router.post("/track/download")
async def track_download(
    payload: TrackDownloadPayload,
    db: Session = Depends(get_db),
    auth = Depends(get_current_user_or_api_key)
):
    """
    Track a file download
    
    Updates download_count and bandwidth_used for the specified file.
    """
    try:
        file = db.query(UploadedFile).filter(UploadedFile.id == payload.file_id).first()
        
        if not file:
            raise HTTPException(status_code=404, detail=f"File {payload.file_id} not found")
        
        # Update file statistics
        file.download_count = (file.download_count or 0) + 1
        file.bandwidth_used = (file.bandwidth_used or 0) + payload.bytes_sent
        file.last_accessed = datetime.now()
        
        # Also update cache entry if exists
        if file.path:
            cache_entry = db.query(CacheEntry).filter(CacheEntry.path == file.path).first()
            if cache_entry:
                if payload.cache_status in ['HIT', 'STALE']:
                    cache_entry.hit_count = (cache_entry.hit_count or 0) + 1
                    cache_entry.last_hit = datetime.now()
                else:
                    cache_entry.miss_count = (cache_entry.miss_count or 0) + 1
                cache_entry.bytes_served = (cache_entry.bytes_served or 0) + payload.bytes_sent
        
        db.commit()
        
        return {
            "status": "ok",
            "file_id": payload.file_id,
            "download_count": file.download_count,
            "bandwidth_used": file.bandwidth_used
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error tracking download: {e}")
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Error tracking download: {str(e)}")


@router.post("/track/cache-hit")
async def track_cache_hit(
    payload: TrackCacheHitPayload,
    db: Session = Depends(get_db),
    auth = Depends(get_current_user_or_api_key)
):
    """
    Track cache hit/miss for a specific path
    
    Updates cache_entries table with hit/miss counts and bandwidth.
    """
    try:
        cache_entry = db.query(CacheEntry).filter(CacheEntry.path == payload.path).first()
        
        if not cache_entry:
            cache_entry = CacheEntry(
                path=payload.path,
                cache_key=f"httpGETlocalhost{payload.path}",
                hit_count=0,
                miss_count=0,
                bytes_served=0,
                is_cached=False,
                created_at=datetime.now()
            )
            db.add(cache_entry)
            db.flush()
        
        # Update based on cache status
        if payload.cache_status in ['HIT', 'STALE']:
            cache_entry.hit_count = (cache_entry.hit_count or 0) + 1
            cache_entry.last_hit = datetime.now()
            cache_entry.is_cached = True
            if not cache_entry.first_cached:
                cache_entry.first_cached = datetime.now()
        elif payload.cache_status in ['MISS', 'BYPASS', 'EXPIRED', 'UPDATING']:
            cache_entry.miss_count = (cache_entry.miss_count or 0) + 1
            cache_entry.last_miss = datetime.now()
        
        cache_entry.bytes_served = (cache_entry.bytes_served or 0) + payload.bytes_sent
        cache_entry.updated_at = datetime.now()
        
        # Also update corresponding UploadedFile if exists
        uploaded_file = db.query(UploadedFile).filter(UploadedFile.path == payload.path).first()
        if uploaded_file:
            uploaded_file.download_count = (uploaded_file.download_count or 0) + 1
            uploaded_file.bandwidth_used = (uploaded_file.bandwidth_used or 0) + payload.bytes_sent
            uploaded_file.last_accessed = datetime.now()
        
        db.commit()
        
        return {
            "status": "ok",
            "path": payload.path,
            "cache_status": payload.cache_status,
            "hit_count": cache_entry.hit_count,
            "miss_count": cache_entry.miss_count,
            "bytes_served": cache_entry.bytes_served
        }
        
    except Exception as e:
        logger.error(f"Error tracking cache hit: {e}")
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Error tracking cache hit: {str(e)}")


@router.post("/aggregate-logs")
async def trigger_log_aggregation(
    background: bool = False,
    db: Session = Depends(get_db),
    auth = Depends(get_current_user_or_api_key)
) -> AggregateLogsResponse:
    """
    Manually trigger log aggregation (can be called via cron)
    
    Args:
        background: If True, run in background. If False, run synchronously.
    
    Returns:
        AggregateLogsResponse with processing statistics
    """
    if background:
        # For background processing (not blocking)
        from concurrent.futures import ThreadPoolExecutor
        executor = ThreadPoolExecutor(max_workers=1)
        executor.submit(aggregate_bandwidth_logs)
        return AggregateLogsResponse(
            status="started",
            lines_processed=0,
            entries_updated=0,
            errors=0
        )
    else:
        # Synchronous execution (returns results immediately)
        result = aggregate_bandwidth_logs()
        return AggregateLogsResponse(
            status=result["status"],
            lines_processed=result["lines_processed"],
            entries_updated=result["entries_updated"],
            errors=result["errors"]
        )

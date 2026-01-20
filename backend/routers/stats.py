from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func, and_
from database import get_db
from models import UploadedFile, CacheEntry, BandwidthLog, CachePurgeLog
from datetime import datetime, timedelta
from config import settings
from pathlib import Path
from auth import get_current_user_or_api_key

router = APIRouter()


@router.get("/overview")
async def stats_overview(
    db: Session = Depends(get_db),
    auth = Depends(get_current_user_or_api_key)
):
    """
    Gesamtübersicht aller wichtigen Metriken
    """
    
    # File Statistics
    total_files = db.query(UploadedFile).filter(UploadedFile.is_active == True).count()
    total_images = db.query(UploadedFile).filter(
        and_(UploadedFile.is_active == True, UploadedFile.file_type == "image")
    ).count()
    total_videos = db.query(UploadedFile).filter(
        and_(UploadedFile.is_active == True, UploadedFile.file_type == "video")
    ).count()
    
    # Storage used
    total_storage = db.query(func.sum(UploadedFile.size)).filter(
        UploadedFile.is_active == True
    ).scalar() or 0
    
    # Cache Statistics
    total_cached = db.query(CacheEntry).filter(CacheEntry.is_cached == True).count()
    total_cache_hits = db.query(func.sum(CacheEntry.hit_count)).scalar() or 0
    total_cache_misses = db.query(func.sum(CacheEntry.miss_count)).scalar() or 0
    
    # Cache Hit Ratio
    total_requests = total_cache_hits + total_cache_misses
    hit_ratio = (total_cache_hits / total_requests * 100) if total_requests > 0 else 0
    
    # Cache size on disk
    cache_path = Path(settings.NGINX_CACHE_PATH)
    cache_size_bytes = 0
    if cache_path.exists():
        cache_size_bytes = sum(f.stat().st_size for f in cache_path.rglob('*') if f.is_file())
    
    # Bandwidth (last 24h)
    yesterday = datetime.now() - timedelta(days=1)
    bandwidth_24h = db.query(func.sum(BandwidthLog.bytes_sent)).filter(
        BandwidthLog.hour >= yesterday
    ).scalar() or 0
    
    return {
        "files": {
            "total": total_files,
            "images": total_images,
            "videos": total_videos
        },
        "storage": {
            "used_bytes": total_storage,
            "used_gb": round(total_storage / 1024**3, 2)
        },
        "cache": {
            "cached_files": total_cached,
            "total_hits": total_cache_hits,
            "total_misses": total_cache_misses,
            "hit_ratio": round(hit_ratio, 2),
            "cache_size_bytes": cache_size_bytes,
            "cache_size_gb": round(cache_size_bytes / 1024**3, 2)
        },
        "bandwidth": {
            "last_24h_bytes": bandwidth_24h,
            "last_24h_gb": round(bandwidth_24h / 1024**3, 2)
        }
    }


@router.get("/bandwidth")
async def bandwidth_stats(
    days: int = 7,
    db: Session = Depends(get_db),
    auth = Depends(get_current_user_or_api_key)
):
    """
    Bandwidth Statistics für die letzten N Tage
    """
    
    start_date = datetime.now() - timedelta(days=days)
    
    logs = db.query(BandwidthLog).filter(
        BandwidthLog.hour >= start_date
    ).order_by(BandwidthLog.hour).all()
    
    return {
        "days": days,
        "data": [
            {
                "hour": log.hour.isoformat(),
                "requests": log.requests,
                "bytes_sent": log.bytes_sent,
                "gb_sent": round(log.bytes_sent / 1024**3, 2),
                "cache_hits": log.cache_hits,
                "cache_misses": log.cache_misses,
                "hit_ratio": round((log.cache_hits / (log.cache_hits + log.cache_misses) * 100) 
                                  if (log.cache_hits + log.cache_misses) > 0 else 0, 2)
            }
            for log in logs
        ]
    }


@router.get("/top-files")
async def top_files(
    limit: int = 20,
    db: Session = Depends(get_db),
    auth = Depends(get_current_user_or_api_key)
):
    """
    Top heruntergeladene Dateien
    """
    
    files = db.query(UploadedFile).filter(
        UploadedFile.is_active == True
    ).order_by(
        UploadedFile.download_count.desc()
    ).limit(limit).all()
    
    return {
        "top_files": [
            {
                "filename": f.filename,
                "path": f.path,
                "cdn_url": f.cdn_url,
                "type": f.file_type,
                "size": f.size,
                "downloads": f.download_count,
                "bandwidth_used": f.bandwidth_used,
                "bandwidth_gb": round(f.bandwidth_used / 1024**3, 2)
            }
            for f in files
        ]
    }


@router.get("/cache-performance")
async def cache_performance(
    db: Session = Depends(get_db),
    auth = Depends(get_current_user_or_api_key)
):
    """
    Cache Performance Metriken
    """
    
    # Top cached files
    top_cached = db.query(CacheEntry).filter(
        CacheEntry.is_cached == True
    ).order_by(CacheEntry.hit_count.desc()).limit(10).all()
    
    # Recent misses
    recent_misses = db.query(CacheEntry).filter(
        CacheEntry.last_miss.isnot(None)
    ).order_by(CacheEntry.last_miss.desc()).limit(10).all()
    
    return {
        "top_cached_files": [
            {
                "path": e.path,
                "hit_count": e.hit_count,
                "miss_count": e.miss_count,
                "bytes_served": e.bytes_served,
                "first_cached": e.first_cached.isoformat() if e.first_cached else None,
                "last_hit": e.last_hit.isoformat() if e.last_hit else None
            }
            for e in top_cached
        ],
        "recent_cache_misses": [
            {
                "path": e.path,
                "miss_count": e.miss_count,
                "last_miss": e.last_miss.isoformat() if e.last_miss else None
            }
            for e in recent_misses
        ]
    }

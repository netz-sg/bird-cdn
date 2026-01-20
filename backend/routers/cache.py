from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from database import get_db
from models import CacheEntry
from datetime import datetime
from auth import get_current_user_or_api_key

router = APIRouter()


@router.get("/status")
async def cache_status(
    path: str = Query(..., description="CDN path to check"),
    db: Session = Depends(get_db),
    auth = Depends(get_current_user_or_api_key)
):
    """
    Check cache status für eine bestimmte Datei
    """
    
    cache_entry = db.query(CacheEntry).filter(CacheEntry.path == path).first()
    
    if not cache_entry:
        return {
            "path": path,
            "cached": False,
            "message": "Not in cache"
        }
    
    return {
        "path": path,
        "cached": cache_entry.is_cached,
        "cache_key": cache_entry.cache_key,
        "hit_count": cache_entry.hit_count,
        "miss_count": cache_entry.miss_count,
        "bytes_served": cache_entry.bytes_served,
        "first_cached": cache_entry.first_cached.isoformat() if cache_entry.first_cached else None,
        "last_hit": cache_entry.last_hit.isoformat() if cache_entry.last_hit else None,
        "cache_size": cache_entry.cache_size
    }


@router.get("/list")
async def list_cached_files(
    limit: int = 100,
    offset: int = 0,
    db: Session = Depends(get_db),
    auth = Depends(get_current_user_or_api_key)
):
    """
    Liste aller gecachten Dateien
    """
    
    query = db.query(CacheEntry).filter(CacheEntry.is_cached == True)
    total = query.count()
    
    entries = query.order_by(CacheEntry.last_hit.desc()).offset(offset).limit(limit).all()
    
    return {
        "total": total,
        "limit": limit,
        "offset": offset,
        "cached_files": [
            {
                "path": e.path,
                "cache_key": e.cache_key,
                "hit_count": e.hit_count,
                "bytes_served": e.bytes_served,
                "cache_size": e.cache_size,
                "first_cached": e.first_cached.isoformat() if e.first_cached else None,
                "last_hit": e.last_hit.isoformat() if e.last_hit else None
            }
            for e in entries
        ]
    }


@router.post("/update")
async def update_cache_entry(
    path: str,
    cache_status: str,
    db: Session = Depends(get_db),
    auth = Depends(get_current_user_or_api_key)
):
    """
    Update cache entry (called by NGINX logs parser or webhook)
    """
    
    cache_entry = db.query(CacheEntry).filter(CacheEntry.path == path).first()
    
    if not cache_entry:
        # Create new entry
        cache_entry = CacheEntry(
            path=path,
            cache_key=f"http$GET$localhost{path}",
            created_at=datetime.now()
        )
        db.add(cache_entry)
    
    # Update based on cache status
    if cache_status == "HIT":
        cache_entry.hit_count += 1
        cache_entry.last_hit = datetime.now()
        cache_entry.is_cached = True
    elif cache_status == "MISS":
        cache_entry.miss_count += 1
        cache_entry.last_miss = datetime.now()
    
    cache_entry.updated_at = datetime.now()
    
    db.commit()
    
    return {
        "success": True,
        "path": path,
        "cache_status": cache_status
    }

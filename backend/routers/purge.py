from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from database import get_db
from models import CachePurgeLog, CacheEntry
from config import settings
from auth import get_current_user_or_api_key
import os
import shutil
from datetime import datetime
from pathlib import Path

router = APIRouter()


def purge_nginx_cache_by_pattern(pattern: str = None, full: bool = False) -> dict:
    """
    Purge NGINX cache files
    
    Returns: dict with files_purged and bytes_freed
    """
    
    cache_path = Path(settings.NGINX_CACHE_PATH)
    
    if not cache_path.exists():
        return {"files_purged": 0, "bytes_freed": 0}
    
    files_purged = 0
    bytes_freed = 0
    
    try:
        if full:
            # Full cache purge
            for item in cache_path.iterdir():
                if item.is_file():
                    bytes_freed += item.stat().st_size
                    item.unlink()
                    files_purged += 1
                elif item.is_dir():
                    dir_size = sum(f.stat().st_size for f in item.rglob('*') if f.is_file())
                    bytes_freed += dir_size
                    files_count = len(list(item.rglob('*')))
                    shutil.rmtree(item)
                    files_purged += files_count
        else:
            # Pattern-based purge (simplified - iterate and check)
            # In production: implement proper cache key lookup
            for item in cache_path.rglob('*'):
                if item.is_file():
                    if pattern is None or pattern in str(item):
                        bytes_freed += item.stat().st_size
                        item.unlink()
                        files_purged += 1
    
    except Exception as e:
        print(f"Error purging cache: {e}")
    
    return {
        "files_purged": files_purged,
        "bytes_freed": bytes_freed
    }


@router.delete("/purge")
async def purge_single_file(
    path: str = Query(..., description="CDN path to purge (e.g., /media/image.jpg)"),
    db: Session = Depends(get_db),
    auth = Depends(get_current_user_or_api_key)
):
    """
    Purge einzelne Datei aus dem Cache
    
    **Beispiel**: `/api/purge?path=/media/image.jpg`
    """
    
    result = purge_nginx_cache_by_pattern(pattern=path)
    
    # Log purge operation
    purge_log = CachePurgeLog(
        purge_type="single",
        target=path,
        files_purged=result["files_purged"],
        bytes_freed=result["bytes_freed"],
        triggered_by="api",
        success=True,
        created_at=datetime.now(),
        completed_at=datetime.now()
    )
    
    db.add(purge_log)
    
    # Update cache entry
    cache_entry = db.query(CacheEntry).filter(CacheEntry.path == path).first()
    if cache_entry:
        cache_entry.is_cached = False
        cache_entry.updated_at = datetime.now()
    
    db.commit()
    
    return {
        "success": True,
        "path": path,
        "files_purged": result["files_purged"],
        "bytes_freed": result["bytes_freed"],
        "message": f"Purged cache for {path}"
    }


@router.delete("/purge/bucket/{bucket_name}")
async def purge_bucket(
    bucket_name: str,
    db: Session = Depends(get_db),
    auth = Depends(get_current_user_or_api_key)
):
    """
    Purge alle Dateien eines Buckets aus dem Cache
    
    **Beispiel**: `/api/purge/bucket/media`
    """
    
    result = purge_nginx_cache_by_pattern(pattern=f"/{bucket_name}/")
    
    # Log purge operation
    purge_log = CachePurgeLog(
        purge_type="bucket",
        target=bucket_name,
        files_purged=result["files_purged"],
        bytes_freed=result["bytes_freed"],
        triggered_by="api",
        success=True,
        created_at=datetime.now(),
        completed_at=datetime.now()
    )
    
    db.add(purge_log)
    
    # Update all cache entries for this bucket
    cache_entries = db.query(CacheEntry).filter(CacheEntry.path.like(f"/{bucket_name}/%")).all()
    for entry in cache_entries:
        entry.is_cached = False
        entry.updated_at = datetime.now()
    
    db.commit()
    
    return {
        "success": True,
        "bucket": bucket_name,
        "files_purged": result["files_purged"],
        "bytes_freed": result["bytes_freed"],
        "message": f"Purged cache for bucket '{bucket_name}'"
    }


@router.delete("/purge/all")
async def purge_all_cache(
    confirm: bool = Query(False, description="Set to true to confirm full cache purge"),
    db: Session = Depends(get_db),
    auth = Depends(get_current_user_or_api_key)
):
    """
    ⚠️ Purge GESAMTEN Cache
    
    **VORSICHT**: Löscht alle gecachten Dateien!
    
    Setze `confirm=true` zum Bestätigen
    """
    
    if not confirm:
        raise HTTPException(
            400, 
            "Please set confirm=true to purge entire cache. This will delete all cached files!"
        )
    
    result = purge_nginx_cache_by_pattern(full=True)
    
    # Log purge operation
    purge_log = CachePurgeLog(
        purge_type="full",
        target="all",
        files_purged=result["files_purged"],
        bytes_freed=result["bytes_freed"],
        triggered_by="api",
        reason="Full cache purge",
        success=True,
        created_at=datetime.now(),
        completed_at=datetime.now()
    )
    
    db.add(purge_log)
    
    # Update all cache entries
    db.query(CacheEntry).update({"is_cached": False, "updated_at": datetime.now()})
    
    db.commit()
    
    return {
        "success": True,
        "files_purged": result["files_purged"],
        "bytes_freed": result["bytes_freed"],
        "message": "Full cache purged successfully"
    }


@router.get("/purge/history")
async def purge_history(
    limit: int = 50,
    db: Session = Depends(get_db),
    auth = Depends(get_current_user_or_api_key)
):
    """
    Historie aller Purge-Operationen
    """
    
    logs = db.query(CachePurgeLog).order_by(CachePurgeLog.created_at.desc()).limit(limit).all()
    
    return {
        "total": len(logs),
        "purge_operations": [
            {
                "id": log.id,
                "type": log.purge_type,
                "target": log.target,
                "files_purged": log.files_purged,
                "bytes_freed": log.bytes_freed,
                "triggered_by": log.triggered_by,
                "reason": log.reason,
                "success": log.success,
                "error": log.error_message,
                "created_at": log.created_at.isoformat() if log.created_at else None,
                "completed_at": log.completed_at.isoformat() if log.completed_at else None
            }
            for log in logs
        ]
    }

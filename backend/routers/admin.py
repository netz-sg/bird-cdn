from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from database import get_db
from services import minio_client
from auth import require_admin

router = APIRouter()


@router.get("/buckets")
async def list_buckets(
    admin = Depends(require_admin)
):
    """
    Liste aller MinIO Buckets
    """
    try:
        buckets = minio_client.list_buckets()
        return {
            "buckets": [
                {
                    "name": bucket.name,
                    "created": bucket.creation_date.isoformat() if bucket.creation_date else None
                }
                for bucket in buckets
            ]
        }
    except Exception as e:
        return {"error": str(e)}


@router.post("/buckets")
async def create_bucket(
    name: str,
    admin = Depends(require_admin)
):
    """
    Erstelle neuen Bucket
    """
    try:
        if minio_client.bucket_exists(name):
            return {"error": f"Bucket '{name}' already exists"}
        
        minio_client.make_bucket(name)
        
        # Set bucket policy to public read
        import json
        policy = {
            "Version": "2012-10-17",
            "Statement": [
                {
                    "Effect": "Allow",
                    "Principal": {"AWS": "*"},
                    "Action": ["s3:GetObject"],
                    "Resource": [f"arn:aws:s3:::{name}/*"]
                }
            ]
        }
        minio_client.set_bucket_policy(name, json.dumps(policy))
        
        return {
            "success": True,
            "bucket": name,
            "message": f"Bucket '{name}' created successfully with public read access"
        }
    except Exception as e:
        return {"error": str(e)}


@router.post("/buckets/{name}/public")
async def make_bucket_public(
    name: str,
    admin = Depends(require_admin)
):
    """
    Setze Bucket auf Public Read
    """
    try:
        if not minio_client.bucket_exists(name):
            return {"error": f"Bucket '{name}' does not exist"}
        
        # Set bucket policy to public read
        import json
        policy = {
            "Version": "2012-10-17",
            "Statement": [
                {
                    "Effect": "Allow",
                    "Principal": {"AWS": "*"},
                    "Action": ["s3:GetObject"],
                    "Resource": [f"arn:aws:s3:::{name}/*"]
                }
            ]
        }
        minio_client.set_bucket_policy(name, json.dumps(policy))
        
        return {
            "success": True,
            "bucket": name,
            "message": f"Bucket '{name}' is now public readable"
        }
    except Exception as e:
        return {"error": str(e)}


@router.get("/system-info")
async def system_info(
    db: Session = Depends(get_db),
    admin = Depends(require_admin)
):
    """
    System Informationen
    """
    from config import settings
    
    return {
        "cdn": {
            "domain": settings.CDN_DOMAIN,
            "protocol": settings.CDN_PROTOCOL,
            "cache_path": settings.NGINX_CACHE_PATH
        },
        "storage": {
            "type": "MinIO",
            "endpoint": settings.MINIO_ENDPOINT,
            "default_bucket": settings.MINIO_DEFAULT_BUCKET
        },
        "upload_limits": {
            "max_size_bytes": settings.MAX_UPLOAD_SIZE,
            "max_size_gb": round(settings.MAX_UPLOAD_SIZE / 1024**3, 2),
            "allowed_image_types": list(settings.ALLOWED_IMAGE_EXTENSIONS),
            "allowed_video_types": list(settings.ALLOWED_VIDEO_EXTENSIONS)
        }
    }

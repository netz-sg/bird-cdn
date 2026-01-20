from fastapi import APIRouter, UploadFile, File, Form, Depends, HTTPException
from sqlalchemy.orm import Session
from database import get_db
from services import minio_client, ensure_bucket_exists
from models import UploadedFile
from config import settings
from url_helpers import build_cdn_url, build_transform_url, get_thumbnail_url
from auth import get_current_user_or_api_key
import os
from datetime import datetime
from pathlib import Path
from PIL import Image
import hashlib
import mimetypes
import io

router = APIRouter()


def get_file_hash(file_content: bytes) -> str:
    """Generate SHA256 hash for file deduplication"""
    return hashlib.sha256(file_content).hexdigest()[:16]


def get_image_dimensions(file_path: str) -> tuple:
    """Get image width and height"""
    try:
        with Image.open(file_path) as img:
            return img.size
    except:
        return (None, None)


def convert_image_to_webp(file_content: bytes, quality: int = 85) -> tuple[bytes, int, int]:
    """
    Konvertiert Bilder zu WebP (neuestes Web-Format)
    
    Returns: (webp_content, width, height)
    """
    try:
        # Öffne Originalbild
        img = Image.open(io.BytesIO(file_content))
        
        # Konvertiere zu RGB falls RGBA (WebP unterstützt Transparenz)
        if img.mode in ('RGBA', 'LA', 'P'):
            # Behalte Transparenz
            pass
        elif img.mode != 'RGB':
            img = img.convert('RGB')
        
        # Speichere als WebP
        output = io.BytesIO()
        img.save(output, format='WEBP', quality=quality, method=6)  # method=6 = beste Kompression
        webp_content = output.getvalue()
        
        width, height = img.size
        
        return webp_content, width, height
    except Exception as e:
        raise HTTPException(500, f"Image conversion failed: {str(e)}")


@router.post("/upload")
async def upload_file(
    file: UploadFile = File(...),
    bucket: str = Form(default=settings.MINIO_DEFAULT_BUCKET),
    folder: str = Form(default=""),
    db: Session = Depends(get_db),
    auth = Depends(get_current_user_or_api_key)
):
    """
    Upload eine Datei zum Origin Storage (MinIO)
    
    - **file**: Die hochzuladende Datei (Bild oder Video)
    - **bucket**: Ziel-Bucket (default: 'media')
    - **folder**: Optional: Subfolder im Bucket
    """
    
    # Validiere Dateigröße
    file_content = await file.read()
    file_size = len(file_content)
    
    if file_size > settings.MAX_UPLOAD_SIZE:
        raise HTTPException(400, f"File too large. Max: {settings.MAX_UPLOAD_SIZE} bytes")
    
    # Validiere Dateityp
    file_ext = Path(file.filename).suffix.lower()
    mime_type = mimetypes.guess_type(file.filename)[0] or "application/octet-stream"
    original_ext = file_ext  # Speichere Original-Extension
    
    if file_ext in settings.ALLOWED_IMAGE_EXTENSIONS:
        file_type = "image"
    elif file_ext in settings.ALLOWED_VIDEO_EXTENSIONS:
        file_type = "video"
    else:
        raise HTTPException(400, f"File type not allowed: {file_ext}")
    
    # 🚀 Konvertiere Bilder automatisch zu WebP
    width, height = None, None
    if file_type == "image":
        try:
            file_content, width, height = convert_image_to_webp(file_content, quality=85)
            file_ext = ".webp"
            mime_type = "image/webp"
            file_size = len(file_content)  # Update size nach Konvertierung
        except Exception as e:
            # Fallback: Behalte Original
            print(f"WebP conversion failed, keeping original: {e}")
            if not width:
                # Versuche Dimensionen zu extrahieren
                try:
                    img = Image.open(io.BytesIO(file_content))
                    width, height = img.size
                except:
                    pass
    
    # Generate unique filename (mit Hash für Deduplication)
    file_hash = get_file_hash(file_content)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    safe_filename = f"{timestamp}_{file_hash}{file_ext}"
    
    # Build path
    if folder:
        object_name = f"{folder.strip('/')}/{safe_filename}"
    else:
        object_name = safe_filename
    
    # Ensure bucket exists
    ensure_bucket_exists(bucket)
    
    # Upload to MinIO
    try:
        from io import BytesIO
        
        minio_client.put_object(
            bucket,
            object_name,
            BytesIO(file_content),
            length=file_size,
            content_type=mime_type
        )
    except Exception as e:
        raise HTTPException(500, f"Upload failed: {str(e)}")
    
    # Build CDN URL
    cdn_url = build_cdn_url(bucket, object_name)
    
    # Save to database
    db_file = UploadedFile(
        filename=safe_filename,
        original_filename=file.filename,
        bucket=bucket,
        path=f"/{bucket}/{object_name}",
        size=file_size,
        mime_type=mime_type,
        file_type=file_type,
        cdn_url=cdn_url,
        width=width,
        height=height,
        created_at=datetime.now()
    )
    
    db.add(db_file)
    db.commit()
    db.refresh(db_file)
    
    # Build response mit Transform-URLs für Bilder
    response = {
        "success": True,
        "file_id": db_file.id,
        "filename": safe_filename,
        "original_filename": file.filename,
        "bucket": bucket,
        "path": object_name,
        "size": file_size,
        "type": file_type,
        "cdn_url": cdn_url,
        "origin_url": f"http://{settings.MINIO_ENDPOINT}/{bucket}/{object_name}",
        "dimensions": {"width": width, "height": height} if width else None,
        "message": "File uploaded successfully"
    }
    
    # Füge Transform-URLs hinzu für Bilder
    if file_type == "image":
        response["transform_urls"] = {
            "thumbnail": get_thumbnail_url(bucket, object_name, size=400),
            "preview": build_transform_url(bucket, object_name, w=800, format='webp'),
            "large": build_transform_url(bucket, object_name, w=1600, format='webp'),
            "original_webp": build_transform_url(bucket, object_name, format='webp', quality=90)
        }
    
    return response


@router.get("/files")
async def list_files(
    bucket: str = None,
    file_type: str = None,
    limit: int = 50,
    offset: int = 0,
    db: Session = Depends(get_db),
    auth = Depends(get_current_user_or_api_key)
):
    """
    Liste aller hochgeladenen Dateien
    
    - **bucket**: Filter nach Bucket (optional)
    - **file_type**: Filter nach Type: 'image' oder 'video' (optional)
    - **limit**: Max. Anzahl Ergebnisse
    - **offset**: Offset für Pagination
    """
    
    query = db.query(UploadedFile).filter(UploadedFile.is_active == True)
    
    if bucket:
        query = query.filter(UploadedFile.bucket == bucket)
    
    if file_type:
        query = query.filter(UploadedFile.file_type == file_type)
    
    total = query.count()
    files = query.order_by(UploadedFile.created_at.desc()).offset(offset).limit(limit).all()
    
    return {
        "total": total,
        "limit": limit,
        "offset": offset,
        "files": [
            {
                "id": f.id,
                "filename": f.filename,
                "original_filename": f.original_filename,
                "bucket": f.bucket,
                "path": f.path,
                "size": f.size,
                "type": f.file_type,
                "cdn_url": f.cdn_url,
                "dimensions": {"width": f.width, "height": f.height} if f.width else None,
                "download_count": f.download_count,
                "created_at": f.created_at.isoformat() if f.created_at else None
            }
            for f in files
        ]
    }


@router.delete("/files/{file_id}")
async def delete_file(
    file_id: int,
    db: Session = Depends(get_db),
    auth = Depends(get_current_user_or_api_key)
):
    """
    Lösche eine Datei (soft delete)
    """
    
    file = db.query(UploadedFile).filter(UploadedFile.id == file_id).first()
    if not file:
        raise HTTPException(404, "File not found")
    
    # Soft delete
    file.is_active = False
    db.commit()
    
    # TODO: Optional - physisch aus MinIO löschen
    # minio_client.remove_object(file.bucket, file.path)
    
    return {
        "success": True,
        "message": f"File {file.filename} deleted"
    }

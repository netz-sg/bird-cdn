from sqlalchemy import Column, Integer, String, BigInteger, DateTime, Boolean, Text, Float, ForeignKey, LargeBinary
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from database import Base


class User(Base):
    """User Authentication Table"""
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(100), unique=True, nullable=False, index=True)
    email = Column(String(255), unique=True, nullable=False, index=True)
    hashed_password = Column(String(255), nullable=False)
    role = Column(String(20), default="user")  # 'admin', 'user'
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    last_login = Column(DateTime(timezone=True))
    
    # Relationship
    api_keys = relationship("APIKey", back_populates="owner")


class APIKey(Base):
    """API Keys for external applications (PayloadCMS, etc.)"""
    __tablename__ = "api_keys"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)  # e.g., "PayloadCMS Production"
    key = Column(String(255), unique=True, nullable=False, index=True)
    created_by = Column(Integer, ForeignKey("users.id"), nullable=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    expires_at = Column(DateTime(timezone=True))
    last_used_at = Column(DateTime(timezone=True))
    
    # Relationship
    owner = relationship("User", back_populates="api_keys")


class UploadedFile(Base):
    """Tracking aller hochgeladenen Dateien"""
    __tablename__ = "uploaded_files"

    id = Column(Integer, primary_key=True, index=True)
    filename = Column(String(255), nullable=False)
    original_filename = Column(String(255), nullable=False)
    bucket = Column(String(100), nullable=False, index=True)
    path = Column(String(500), nullable=False, unique=True, index=True)
    size = Column(BigInteger, nullable=False)  # in bytes
    mime_type = Column(String(100))
    file_type = Column(String(20), index=True)  # 'image' oder 'video'
    
    # CDN URL
    cdn_url = Column(String(500))
    
    # Metadata
    width = Column(Integer)
    height = Column(Integer)
    duration = Column(Float)  # für Videos in Sekunden
    
    # Statistics
    download_count = Column(BigInteger, default=0)
    bandwidth_used = Column(BigInteger, default=0)  # in bytes
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    last_accessed = Column(DateTime(timezone=True))
    
    # Status
    is_active = Column(Boolean, default=True)


class CacheEntry(Base):
    """Tracking gecachter Dateien"""
    __tablename__ = "cache_entries"

    id = Column(Integer, primary_key=True, index=True)
    path = Column(String(500), nullable=False, unique=True, index=True)
    cache_key = Column(String(500), nullable=False, index=True)
    
    # Cache Stats
    hit_count = Column(BigInteger, default=0)
    miss_count = Column(BigInteger, default=0)
    bytes_served = Column(BigInteger, default=0)
    
    # Status
    is_cached = Column(Boolean, default=False)
    cache_size = Column(BigInteger)  # Größe im Cache
    
    # Timestamps
    first_cached = Column(DateTime(timezone=True))
    last_hit = Column(DateTime(timezone=True))
    last_miss = Column(DateTime(timezone=True))
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())


class CachePurgeLog(Base):
    """Log aller Cache-Purge Operationen"""
    __tablename__ = "cache_purge_logs"

    id = Column(Integer, primary_key=True, index=True)
    purge_type = Column(String(50), nullable=False)  # 'single', 'bucket', 'pattern', 'full'
    target = Column(String(500))  # path, bucket name, oder pattern
    files_purged = Column(Integer, default=0)
    bytes_freed = Column(BigInteger, default=0)
    
    # User/Trigger
    triggered_by = Column(String(100))
    reason = Column(Text)
    
    # Status
    success = Column(Boolean, default=True)
    error_message = Column(Text)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    completed_at = Column(DateTime(timezone=True))


class BandwidthLog(Base):
    """Bandwidth Usage Logging (aggregiert pro Stunde)"""
    __tablename__ = "bandwidth_logs"

    id = Column(Integer, primary_key=True, index=True)
    hour = Column(DateTime(timezone=True), nullable=False, index=True)
    
    # Traffic
    requests = Column(BigInteger, default=0)
    bytes_sent = Column(BigInteger, default=0)
    
    # Cache Performance
    cache_hits = Column(BigInteger, default=0)
    cache_misses = Column(BigInteger, default=0)
    
    # Status Codes
    status_200 = Column(BigInteger, default=0)
    status_206 = Column(BigInteger, default=0)  # Partial Content (Videos)
    status_304 = Column(BigInteger, default=0)  # Not Modified
    status_404 = Column(BigInteger, default=0)
    status_500 = Column(BigInteger, default=0)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class WatermarkConfig(Base):
    """Watermark Configuration - Global settings for image watermarking"""
    __tablename__ = "watermark_config"

    id = Column(Integer, primary_key=True, index=True)
    logo_data = Column(LargeBinary, nullable=True)  # PNG logo stored as binary
    position = Column(String(20), default="bottom-right")  # top-left, top-right, bottom-left, bottom-right, center
    opacity = Column(Float, default=0.7)  # 0.0 to 1.0
    scale_percent = Column(Integer, default=20)  # Logo size as % of image width
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())


class SystemSetting(Base):
    """System-wide settings (key-value store)"""
    __tablename__ = "system_settings"

    id = Column(Integer, primary_key=True, index=True)
    key = Column(String(100), unique=True, nullable=False, index=True)
    value = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())


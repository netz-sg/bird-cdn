#!/usr/bin/env python3
"""
Erstelle Demo-Daten für Stats-Anzeige
"""
import sys
from pathlib import Path

# Add backend directory to path
backend_dir = Path(__file__).parent
sys.path.insert(0, str(backend_dir))

from database import SessionLocal
from models import BandwidthLog, UploadedFile, CacheEntry
from datetime import datetime, timedelta
import random

def create_demo_data():
    db = SessionLocal()
    
    try:
        print("📊 Creating demo stats data...")
        
        # 1. Bandwidth Logs (letzte 7 Tage, stündlich)
        now = datetime.now().replace(minute=0, second=0, microsecond=0)
        
        for days_ago in range(7):
            for hour in range(24):
                timestamp = now - timedelta(days=days_ago, hours=hour)
                
                # Variiere Traffic realistisch
                base_requests = random.randint(100, 500)
                cache_hit_ratio = random.uniform(0.6, 0.9)
                cache_hits = int(base_requests * cache_hit_ratio)
                cache_misses = base_requests - cache_hits
                
                bytes_per_request = random.randint(500000, 5000000)  # 500KB - 5MB
                
                log = BandwidthLog(
                    hour=timestamp,
                    requests=base_requests,
                    bytes_sent=base_requests * bytes_per_request,
                    cache_hits=cache_hits,
                    cache_misses=cache_misses,
                    status_200=int(base_requests * 0.95),
                    status_206=int(base_requests * 0.02),
                    status_304=int(base_requests * 0.01),
                    status_404=int(base_requests * 0.01),
                    status_500=int(base_requests * 0.01)
                )
                db.add(log)
        
        db.commit()
        print("✅ Created 168 hours of bandwidth logs")
        
        # 2. Update existing uploaded files with demo stats
        files = db.query(UploadedFile).all()
        if files:
            for file in files:
                file.download_count = random.randint(10, 1000)
                file.bandwidth_used = file.size * file.download_count
            db.commit()
            print(f"✅ Updated {len(files)} files with download stats")
        
        # 3. Cache Entries
        if files:
            for file in random.sample(files, min(10, len(files))):
                cache_entry = CacheEntry(
                    path=file.path,
                    hit_count=random.randint(50, 500),
                    miss_count=random.randint(5, 50),
                    bytes_served=file.size * random.randint(50, 500),
                    is_cached=True,
                    first_cached=datetime.now() - timedelta(days=random.randint(1, 7)),
                    last_hit=datetime.now() - timedelta(hours=random.randint(1, 24))
                )
                db.add(cache_entry)
            db.commit()
            print(f"✅ Created cache entries for files")
        
        print("🎉 Demo data created successfully!")
        
    except Exception as e:
        print(f"❌ Error creating demo data: {e}")
        db.rollback()
    finally:
        db.close()


if __name__ == "__main__":
    create_demo_data()

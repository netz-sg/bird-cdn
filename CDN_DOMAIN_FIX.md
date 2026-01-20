# 🔧 CDN Domain Fix - URLs sind localhost statt cdn.sg-netz.de

## Problem
Wenn du auf dem Server `cdn.sg-netz.de` Dateien hochlädst, bekommst du URLs wie:
```
http://localhost/media/20260120_132055_14d82d55a5f2a74b.mp4
```

Statt:
```
https://cdn.sg-netz.de/media/20260120_132055_14d82d55a5f2a74b.mp4
```

## Root Cause
Die `CDN_DOMAIN` Environment Variable ist nicht auf dem Server gesetzt. Das Backend verwendet den Hardcoded Default-Wert `localhost` aus `backend/config.py`.

## ✅ Lösung

### Auf dem Server:

1. **Navigate zum Projekt:**
```bash
cd /opt/cdn-network
```

2. **Erstelle .env Datei:**
```bash
nano .env
```

3. **Füge folgende Zeilen ein:**
```bash
# CDN Configuration
CDN_DOMAIN=cdn.sg-netz.de
CDN_PROTOCOL=https

# Optional: Andere Settings...
CDN_CACHE_SIZE=50g
CDN_CACHE_INACTIVE=30d
```

4. **Speichern:** `CTRL+O`, `ENTER`, `CTRL+X`

5. **Pull Latest Changes (wichtig!):**
```bash
git pull origin main
```

6. **Restart Container:**
```bash
docker-compose down
docker-compose up -d
```

7. **Verify:**
```bash
docker-compose logs backend-api | grep CDN
```

Du solltest sehen:
```
INFO:     CDN_DOMAIN: cdn.sg-netz.de
INFO:     CDN_PROTOCOL: https
```

### Test

1. **Upload eine Datei:** auf https://cdn.sg-netz.de
2. **Check Response:**
```json
{
  "success": true,
  "file_id": 8,
  "filename": "test.jpg",
  "cdn_url": "https://cdn.sg-netz.de/media/test.jpg"  ✅
}
```

3. **Access URL:** https://cdn.sg-netz.de/media/test.jpg sollte die Datei zeigen!

## 📝 Was wurde geändert?

### `docker-compose.yml`
```yaml
# VORHER:
- CDN_DOMAIN=localhost
- CDN_PROTOCOL=http

# NACHHER:
- CDN_DOMAIN=${CDN_DOMAIN:-localhost}
- CDN_PROTOCOL=${CDN_PROTOCOL:-http}
```

Jetzt liest Docker Compose die Werte aus der `.env` Datei!

### `backend/config.py`
```python
class Settings(BaseSettings):
    CDN_DOMAIN: str = "localhost"  # Default wenn keine .env
    CDN_PROTOCOL: str = "http"     # Default wenn keine .env
    
    class Config:
        env_file = ".env"  # Pydantic liest automatisch .env!
```

### `backend/url_helpers.py`
```python
def build_cdn_url(bucket: str, path: str) -> str:
    clean_path = path.lstrip('/')
    return f"{settings.CDN_PROTOCOL}://{settings.CDN_DOMAIN}/{bucket}/{clean_path}"
    # ☝️ Verwendet jetzt die richtigen Werte aus .env!
```

## 🎯 Warum ist das passiert?

Die `docker-compose.yml` hatte hardcoded Values:
```yaml
environment:
  - CDN_DOMAIN=localhost  # ❌ Hardcoded!
  - CDN_PROTOCOL=http     # ❌ Hardcoded!
```

Docker Compose hat diese Werte IMMER verwendet, egal ob eine `.env` Datei existierte oder nicht!

Mit der neuen Syntax:
```yaml
environment:
  - CDN_DOMAIN=${CDN_DOMAIN:-localhost}  # ✅ Liest aus .env, fallback "localhost"
```

Docker Compose prüft:
1. Ist `CDN_DOMAIN` in `.env`? → Verwende diesen Wert
2. Nein? → Verwende Default `localhost`

## 🚀 Production Checklist

Auf dem Server `cdn.sg-netz.de`:

- [ ] `.env` Datei erstellt mit `CDN_DOMAIN=cdn.sg-netz.de`
- [ ] `.env` Datei hat `CDN_PROTOCOL=https`
- [ ] `git pull origin main` ausgeführt
- [ ] `docker-compose down && docker-compose up -d`
- [ ] Test-Upload durchgeführt
- [ ] Upload Response zeigt `"cdn_url": "https://cdn.sg-netz.de/..."`
- [ ] URL im Browser öffnen → Datei wird angezeigt

## 📦 Files Created/Updated

- ✅ `docker-compose.yml` - Environment Variables with fallback defaults
- ✅ `.env.production` - Production configuration template
- ✅ `CDN_DOMAIN_FIX.md` - This file (Dokumentation)

## ⚠️ Wichtig

Nach diesem Fix:
- **Development (lokal):** Funktioniert weiterhin mit `localhost` (default)
- **Production (Server):** Verwendet `cdn.sg-netz.de` aus `.env`

Keine Code-Änderungen nötig! Nur Environment-Konfiguration. 🎉

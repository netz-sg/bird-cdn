# � Bird-CDN

Ein vollständiges Open-Source CDN-System für Bilder und Videos mit Management-Interface.

## 🎯 Features

- **NGINX Edge Cache** - Optimiert für Bilder & Videos mit Range Requests
- **MinIO Origin Storage** - S3-kompatible Object Storage
- **FastAPI Backend** - REST API für Management & Cache Purge
- **React Admin UI** - Benutzerfreundliches Dashboard
- **Prometheus + Grafana** - Monitoring & Analytics
- **Docker Setup** - Lokal testbar & Production-ready
- **🆕 Image Transformation API** - On-the-fly Resize/Crop/Format-Konvertierung mit Caching

## 📦 Architektur

```
Clients → NGINX CDN (Port 80/443)
            ↓ (cache MISS)
          MinIO Origin (Port 9000)
          
Backend API (Port 8000) ←→ PostgreSQL + Redis
Admin UI (Port 3000)
Monitoring (Grafana Port 3001, Prometheus Port 9090)
```

## 🚀 Quick Start (Lokal)

### 1. Setup

```bash
# Repository klonen (falls noch nicht geschehen)
cd d:\Dev\cdn-tourdiary

# .env erstellen
cp .env.example .env

# Alle Services starten
docker-compose up -d

# Logs verfolgen
docker-compose logs -f
```

### 2. SSL/HTTPS Setup (Production)

**🆕 Komplett automatisch (Empfohlen):**

```bash
# 1. Domain + Email in .env konfigurieren
nano .env
# Setze: CDN_DOMAIN=cdn.yourdomain.com
#        LETSENCRYPT_EMAIL=your-email@example.com
#        LETSENCRYPT_STAGING=true

# 2. Start-Script ausführen (macht alles automatisch!)
chmod +x start-with-ssl.sh
./start-with-ssl.sh

# ✨ Fertig! CDN läuft auf https://cdn.yourdomain.com
```

**Was das Script macht:**
1. ✅ Startet Docker Services
2. ✅ Wartet auf Zertifikat-Erstellung
3. ✅ Aktiviert HTTPS-Config automatisch
4. ✅ Startet NGINX + Backend neu
5. ✅ Fertig in ~2 Minuten!

**Alternative (Docker Compose direkt):**
```bash
# Services starten
docker-compose up -d

# Nach erfolgreicher Zertifikat-Erstellung (siehe Logs):
./activate-ssl.sh   # Aktiviert SSL automatisch
```

**Details:**
- 🆕 [AUTO_SSL_SETUP.md](AUTO_SSL_SETUP.md) - **Automatisches Setup (empfohlen)**
- [SSL_QUICKSTART.md](SSL_QUICKSTART.md) - Quick Reference
- [SSL_SETUP.md](SSL_SETUP.md) - Manuelle Anleitung mit Troubleshooting

### 3. Services

Nach dem Start sind folgende Services verfügbar:

| Service | URL | Beschreibung |
|---------|-----|--------------|
| **CDN Edge** | http://localhost | NGINX Cache Layer |
| **Admin UI** | http://localhost:3000 | Management Dashboard |
| **Backend API** | http://localhost:8000 | API (Docs: /docs) |
| **MinIO Console** | http://localhost:9011 | Storage Management |
| **Grafana** | http://localhost:3001 | Monitoring (admin/admin) |
| **Prometheus** | http://localhost:9090 | Metriken |

### 4. Erste Schritte

```bash
# 1. MinIO Console öffnen (http://localhost:9001)
#    Login: admin / adminpassword123
#    Bucket erstellen: "media"

# 2. Test-Datei hochladen
curl -X POST http://localhost:8000/api/upload \
  -F "file=@image.jpg" \
  -F "bucket=media"

# 3. Via CDN abrufen
curl -I http://localhost/media/image.jpg
# Erster Request: X-Cache-Status: MISS
# Zweiter Request: X-Cache-Status: HIT
```

## 📊 Monitoring

**Grafana Dashboard**: http://localhost:3001

Default Login:
- User: `admin`
- Password: `admin`

Pre-configured Dashboards:
- CDN Hit/Miss Ratio
- Bandwidth Usage
- Request Rates
- Cache Size & Performance
- Origin Health

## 🛠️ Management API

API Dokumentation: http://localhost:8000/docs

### Wichtige Endpoints:

```bash
# Upload Datei
POST /api/upload

# Cache purge (einzelne Datei)
DELETE /api/cache/purge?path=/media/image.jpg

# Cache purge (kompletter Bucket)
DELETE /api/cache/purge/bucket/media

# Cache Statistiken
GET /api/stats/cache

# Bandwidth Report
GET /api/stats/bandwidth
```

## 🎬 Video-Optimierung

Das CDN unterstützt:
- **Range Requests** (Seeking in Videos)
- **HLS Streaming** (M3U8 Playlists)
- **Adaptive Bitrate** (verschiedene Qualitäten)
- **Slice Uploads** (große Dateien)

## 🏗️ Production Deployment

### SSL/TLS Setup

```bash
# 1. Certbot installieren (auf Host-Server)
sudo apt install certbot

# 2. Zertifikat erstellen
sudo certbot certonly --standalone -d cdn.yourdomain.com

# 3. Zertifikate nach ./ssl kopieren
sudo cp /etc/letsencrypt/live/cdn.yourdomain.com/*.pem ./ssl/

# 4. NGINX Config anpassen (ssl in nginx/conf.d/cdn.conf aktivieren)
```

### Empfohlene Production-Settings

```yaml
# In docker-compose.yml anpassen:
nginx-cdn:
  environment:
    - CDN_CACHE_SIZE=50g      # Mehr Cache
    - CDN_CACHE_INACTIVE=60d  # Längere Retention
```

## 🔧 Konfiguration

### NGINX Cache tunen

Bearbeite `nginx/nginx.conf`:

```nginx
# Cache Size erhöhen
proxy_cache_path /var/cache/nginx/cdn
  max_size=100g;  # von 50g auf 100g
```

### Video-Streaming optimieren

Bearbeite `nginx/conf.d/cdn.conf`:

```nginx
# Größere Buffer für Videos
proxy_buffer_size 32k;
proxy_buffers 8 32k;
```

## 📈 Skalierung (später)

Für Multi-Region Setup:
1. Weitere NGINX-Instanzen in anderen Regionen
2. GeoDNS für Region-Routing
3. Origin Replication (MinIO Multi-Site)
4. Shared Database für zentrale Verwaltung

## 🐛 Troubleshooting

```bash
# Logs anschauen
docker-compose logs nginx-cdn
docker-compose logs backend-api

# Cache leeren (komplett)
docker-compose exec nginx-cdn rm -rf /var/cache/nginx/*
docker-compose restart nginx-cdn

# Einzelnen Service neu starten
docker-compose restart nginx-cdn

# Alle Services neu bauen
docker-compose down
docker-compose up -d --build
```

## 📝 Development

```bash
# Backend entwickeln (mit Hot-Reload)
cd backend
pip install -r requirements.txt
uvicorn main:app --reload --host 0.0.0.0 --port 8000

# Frontend entwickeln
cd frontend
npm install
npm start
```

## 🔐 Security Checklist (Production)

- [ ] Starke Passwörter in `.env` setzen
- [ ] JWT Secrets ändern
- [ ] SSL/TLS Zertifikate einrichten
- [ ] Firewall Regeln (nur 80/443 öffnen)
- [ ] MinIO Access Keys rotieren
- [ ] API Rate Limiting aktivieren
- [ ] Admin UI mit Basic Auth schützen

## 📄 Lizenz

MIT License - Frei verwendbar für deine Projekte!

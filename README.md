<div align="center">

![Bird-CDN Header](https://i.ibb.co/R4dpTg9V/Unbenannt-1.png)

# Bird-CDN

### Self-Hosted Content Delivery Network for Images & Videos

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Docker](https://img.shields.io/badge/Docker-Ready-blue?logo=docker)](https://www.docker.com/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.100+-009688?logo=fastapi)](https://fastapi.tiangolo.com/)
[![React](https://img.shields.io/badge/React-18-61DAFB?logo=react)](https://react.dev/)
[![Version](https://img.shields.io/badge/Version-Beta-orange)](https://github.com/netz-sg/cdn-network)

**Status: Beta** - Core features functional, ready for testing environments. Review security checklist before production use.

---

### Built With

<p align="center">
  <a href="https://nginx.org/"><img src="https://img.shields.io/badge/NGINX-009639?style=for-the-badge&logo=nginx&logoColor=white" alt="NGINX"/></a>
  <a href="https://fastapi.tiangolo.com/"><img src="https://img.shields.io/badge/FastAPI-009688?style=for-the-badge&logo=fastapi&logoColor=white" alt="FastAPI"/></a>
  <a href="https://react.dev/"><img src="https://img.shields.io/badge/React-61DAFB?style=for-the-badge&logo=react&logoColor=black" alt="React"/></a>
  <a href="https://www.postgresql.org/"><img src="https://img.shields.io/badge/PostgreSQL-316192?style=for-the-badge&logo=postgresql&logoColor=white" alt="PostgreSQL"/></a>
  <a href="https://redis.io/"><img src="https://img.shields.io/badge/Redis-DC382D?style=for-the-badge&logo=redis&logoColor=white" alt="Redis"/></a>
  <a href="https://min.io/"><img src="https://img.shields.io/badge/MinIO-C72E49?style=for-the-badge&logo=minio&logoColor=white" alt="MinIO"/></a>
  <a href="https://prometheus.io/"><img src="https://img.shields.io/badge/Prometheus-E6522C?style=for-the-badge&logo=prometheus&logoColor=white" alt="Prometheus"/></a>
  <a href="https://grafana.com/"><img src="https://img.shields.io/badge/Grafana-F46800?style=for-the-badge&logo=grafana&logoColor=white" alt="Grafana"/></a>
  <a href="https://www.docker.com/"><img src="https://img.shields.io/badge/Docker-2496ED?style=for-the-badge&logo=docker&logoColor=white" alt="Docker"/></a>
</p>

</div>

---

## Table of Contents

- [About](#about)
- [Features](#features)
- [Architecture](#architecture)
- [Quick Start](#quick-start)
- [Services](#services)
- [API Documentation](#api-documentation)
- [Monitoring](#monitoring)
- [Video Delivery](#video-delivery)
- [Configuration](#configuration)
- [Production Deployment](#production-deployment)
- [Security](#security)
- [Contributing](#contributing)
- [License](#license)

---

## About

**Bird-CDN** is a self-hosted Content Delivery Network for images and videos. It combines NGINX edge caching with MinIO object storage, providing a complete solution for media delivery with automatic image optimization and a modern admin interface.

### Key Highlights

| Feature | Description |
|---------|-------------|
| **NGINX Edge Cache** | 50GB cache, 30-day TTL, 100 req/s rate limit |
| **Image Processing** | Auto WebP conversion, on-the-fly transforms |
| **Watermarking** | Configurable logo with position/opacity/scale |
| **S3 Storage** | MinIO backend, multi-bucket support |
| **Admin Dashboard** | React UI for uploads, stats, cache management |
| **Monitoring** | Prometheus metrics, Grafana dashboards |
| **API Access** | JWT + API Key authentication |
| **Docker-First** | Single command deployment |

---

## Features

### Core CDN Features

| Feature | Status | Description |
|---------|--------|-------------|
| **NGINX Edge Cache** | Implemented | 50GB cache, 30d TTL, Rate Limiting (100 req/s) |
| **MinIO Object Storage** | Implemented | S3-compatible, auto public-read policy |
| **Image Transform API** | Implemented | On-the-fly resize, crop, format conversion |
| **Automatic WebP Conversion** | Implemented | All uploaded images converted to WebP |
| **Watermark System** | Implemented | Configurable logo, position, opacity, scale |
| **Video Streaming** | Implemented | Range Requests, 206 Partial Content, Slice Module |
| **Cache Management** | Implemented | Purge single/bucket/pattern/all with history |
| **SSL/TLS** | Implemented | Let's Encrypt via Certbot |

### Authentication & Security

| Feature | Status | Description |
|---------|--------|-------------|
| **JWT Authentication** | Implemented | HS256, 24h expiration, role-based |
| **API Key System** | Implemented | For external apps (PayloadCMS, etc.) |
| **Password Hashing** | Implemented | Argon2 (no 72-byte limit) |
| **Rate Limiting** | Implemented | NGINX-level (CDN: 100/s, API: 10/s) |

### Admin Dashboard (React)

| Page | Status | Features |
|------|--------|----------|
| **Dashboard** | Implemented | Stats overview, bandwidth chart |
| **Upload** | Implemented | Multi-file, progress tracking, watermark toggle |
| **Files** | Implemented | Browse, filter by type/bucket, preview |
| **Statistics** | Implemented | Bandwidth, top files, cache performance |
| **Cache** | Implemented | Status, purge operations |
| **API Keys** | Implemented | Create, list, toggle, delete, test |
| **Watermark** | Implemented | Upload logo, configure position/opacity |
| **Settings** | Implemented | Domain config, SSL setup |

### Monitoring & Analytics

| Feature | Status | Description |
|---------|--------|-------------|
| **Prometheus Metrics** | Implemented | HTTP, uploads, auth, storage, cache |
| **Grafana Dashboards** | Configured | Auto-provisioned, pre-built panels |
| **NGINX Log Parsing** | Implemented | Automatic aggregation to DB |
| **Bandwidth Tracking** | Implemented | Hourly aggregation, per-file stats |

### Planned Features (Roadmap)

| Feature | Priority | Status |
|---------|----------|--------|
| Signed URLs / Token Auth | High | Planned |
| Bandwidth Quotas | High | Planned |
| Video Transcoding (HLS/DASH) | High | Planned |
| Responsive Image srcset | Medium | Planned |
| Multi-Location / Geo-Routing | Low | Planned |
| AVIF Support | Low | Planned |

---

## Architecture

```
                              ┌─────────────────┐
                              │     Clients     │
                              └────────┬────────┘
                                       │
                              ┌────────▼────────┐
                              │   NGINX Edge    │
                              │   Port 80/443   │
                              │                 │
                              │ • 50GB Cache    │
                              │ • Rate Limiting │
                              │ • SSL/TLS       │
                              └────────┬────────┘
                                       │
           ┌───────────────────────────┼───────────────────────────┐
           │                           │                           │
  ┌────────▼────────┐        ┌────────▼────────┐        ┌────────▼────────┐
  │   Static Files  │        │  Transform API  │        │    Admin UI     │
  │   (Cache HIT)   │        │  /api/transform │        │   Port 3000     │
  │                 │        │                 │        │                 │
  │ Images: 30d TTL │        │ • Resize/Crop   │        │ • React 18      │
  │ Videos: 7d TTL  │        │ • Format Conv.  │        │ • Dashboard     │
  └────────┬────────┘        │ • Cached 30d    │        │ • Upload        │
           │                 └────────┬────────┘        └─────────────────┘
           │ (Cache MISS)             │
           │                          │
  ┌────────▼────────┐        ┌────────▼────────┐
  │  MinIO Storage  │        │  FastAPI        │
  │  Port 9010/9011 │◄───────│  Port 8000      │
  │                 │        │                 │
  │ • S3 Compatible │        │ • Auth (JWT)    │
  │ • Multi-Bucket  │        │ • Upload API    │
  └─────────────────┘        │ • Cache Mgmt    │
                             └────────┬────────┘
                                      │
                    ┌─────────────────┼─────────────────┐
                    │                 │                 │
           ┌────────▼────────┐ ┌─────▼─────┐ ┌────────▼────────┐
           │   PostgreSQL    │ │   Redis   │ │   Prometheus    │
           │                 │ │           │ │   Port 9090     │
           │ • Users         │ │ • Cache   │ │                 │
           │ • Files Meta    │ │ • Session │ │ ┌─────────────┐ │
           │ • Bandwidth     │ └───────────┘ │ │   Grafana   │ │
           │ • Cache Stats   │               │ │  Port 3001  │ │
           └─────────────────┘               │ └─────────────┘ │
                                             └─────────────────┘
```

### Service Overview

| Service | Port | Technology | Purpose |
|---------|------|------------|---------|
| nginx-cdn | 80/443 | NGINX 1.25 | Edge cache, SSL, routing |
| backend-api | 8000 | FastAPI | REST API, business logic |
| frontend | 3000 | React + Vite | Admin dashboard |
| origin-storage | 9010/9011 | MinIO | S3-compatible storage |
| postgres | 5432 | PostgreSQL 16 | Metadata, statistics |
| redis | 6379 | Redis 7 | Caching, sessions |
| prometheus | 9090 | Prometheus | Metrics collection |
| grafana | 3001 | Grafana | Dashboards |

---

## Quick Start

### Prerequisites

- Docker Engine 20.10+
- Docker Compose 1.29+
- At least 4GB RAM
- 20GB disk space

### Local Development Setup

```bash
# 1. Clone the repository
git clone https://github.com/netz-sg/cdn-network.git
cd cdn-network

# 2. Create environment configuration
cp .env.example .env

# 3. Start all services
docker-compose up -d

# 4. View logs
docker-compose logs -f
```

### Initial Configuration

```bash
# 1. Access MinIO Console (http://localhost:9011)
#    Login: admin / adminpassword123
#    Create a bucket named "media"

# 2. Test file upload
curl -X POST http://localhost:8000/api/upload \
  -F "file=@image.jpg" \
  -F "bucket=media"

# 3. Access via CDN
curl -I http://localhost/media/image.jpg
# First request: X-Cache-Status: MISS
# Second request: X-Cache-Status: HIT
```

---

## Services

After starting, the following services are available:

| Service | URL | Description | Default Credentials |
|---------|-----|-------------|---------------------|
| **CDN Edge** | http://localhost | NGINX cache layer | - |
| **Admin UI** | http://localhost:3000 | Management dashboard | admin / admin123 |
| **Backend API** | http://localhost:8000 | REST API ([Docs](http://localhost:8000/docs)) | - |
| **MinIO Console** | http://localhost:9011 | Storage management | admin / adminpassword123 |
| **Grafana** | http://localhost:3001 | Monitoring dashboards | admin / admin |
| **Prometheus** | http://localhost:9090 | Metrics collection | - |

> **⚠️ Security Warning**: Change all default passwords before deploying to production!

---

## API Documentation

Interactive documentation available at:
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

### API Endpoints Overview

| Route | Method | Auth | Description |
|-------|--------|------|-------------|
| `/api/auth/login` | POST | - | Get JWT token |
| `/api/auth/api-keys` | POST/GET | JWT | Manage API keys |
| `/api/upload/multi` | POST | JWT/API Key | Upload files |
| `/api/files` | GET | JWT | List uploaded files |
| `/api/transform/{bucket}/{path}` | GET | - | Transform image |
| `/api/cache/status` | GET | JWT | Cache status |
| `/api/purge` | DELETE | JWT | Purge cache |
| `/api/stats/overview` | GET | JWT | Statistics |
| `/api/watermark/*` | * | Admin | Watermark config |

### Authentication

**Option 1: JWT Token**
```bash
# Login
curl -X POST http://localhost:8000/api/auth/login \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=admin&password=admin123"

# Use token
curl http://localhost:8000/api/files \
  -H "Authorization: Bearer YOUR_JWT_TOKEN"
```

**Option 2: API Key (for external apps)**
```bash
# Create API key
curl -X POST http://localhost:8000/api/auth/api-keys \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -d '{"name": "PayloadCMS"}'

# Use API key
curl -X POST http://localhost:8000/api/upload/multi \
  -H "X-API-Key: cdn_abc123..."
```

### Upload Files

```bash
# Multi-file upload with watermark
curl -X POST http://localhost:8000/api/upload/multi \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -F "files=@photo1.jpg" \
  -F "files=@photo2.png" \
  -F "bucket=media" \
  -F "folder=2024/january" \
  -F "apply_watermark_flag=true"
```

**Response:**
```json
{
  "results": [{
    "success": true,
    "cdn_url": "http://localhost/media/2024/january/20240120_143022_abc123.webp",
    "transform_urls": {
      "thumbnail": "/api/transform/...?w=400&h=400&fit=cover",
      "preview": "/api/transform/...?w=800",
      "large": "/api/transform/...?w=1600"
    }
  }]
}
```

### Image Transformation

```bash
# Resize to width 800
GET /api/transform/media/image.webp?w=800

# Thumbnail (400x400, center crop)
GET /api/transform/media/image.webp?w=400&h=400&fit=cover&crop=center

# Convert to JPEG
GET /api/transform/media/image.webp?format=jpg&quality=75
```

**Parameters:**
| Param | Type | Range | Description |
|-------|------|-------|-------------|
| w | int | 1-4000 | Target width |
| h | int | 1-4000 | Target height |
| fit | enum | contain/cover/fill/inside | Resize mode |
| crop | enum | center/top/bottom/left/right/entropy | Crop position |
| format | enum | webp/jpg/png/gif | Output format |
| quality | int | 1-100 | Compression quality |

### Cache Management

```bash
# Purge single file
curl -X DELETE "http://localhost:8000/api/purge?path=/media/image.webp" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN"

# Purge bucket
curl -X DELETE "http://localhost:8000/api/purge/bucket/media" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN"

# Purge all
curl -X DELETE "http://localhost:8000/api/purge/all?confirm=true" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN"
```

### Statistics

```bash
# Overview
curl http://localhost:8000/api/stats/overview \
  -H "Authorization: Bearer YOUR_JWT_TOKEN"

# Bandwidth (last 7 days)
curl "http://localhost:8000/api/stats/bandwidth?days=7" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN"

# Top files
curl "http://localhost:8000/api/stats/top-files?limit=20" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN"
```

---

## Monitoring

### Grafana Dashboards

Access Grafana at **http://localhost:3001**

**Default Credentials:**
- Username: `admin`
- Password: `admin`

**Pre-configured Dashboards:**
- CDN Performance Overview
- Cache Hit/Miss Ratios
- Bandwidth Usage
- Request Rates & Latency
- Storage Capacity
- System Health

### Prometheus Metrics

Access Prometheus at **http://localhost:9090**

**Backend Metrics (FastAPI):**
| Metric | Type | Description |
|--------|------|-------------|
| `http_requests_total` | Counter | Total HTTP requests by method/endpoint/status |
| `http_request_duration_seconds` | Histogram | Request latency |
| `cdn_uploads_total` | Counter | Uploads by file_type/bucket |
| `cdn_upload_size_bytes` | Histogram | Upload sizes (1KB-1GB buckets) |
| `cdn_auth_requests_total` | Counter | Auth attempts by type/status |
| `cdn_storage_operations_total` | Counter | MinIO operations |
| `cdn_cache_hits_total` | Counter | Cache hits by type |
| `cdn_watermark_operations_total` | Counter | Watermark applications |

**NGINX Metrics (via nginx-exporter):**
| Metric | Description |
|--------|-------------|
| `nginx_connections_active` | Active connections |
| `nginx_http_requests_total` | Total HTTP requests |

---

## Video Delivery

### Implemented Features

| Feature | Status | Description |
|---------|--------|-------------|
| **Range Requests** | Implemented | 206 Partial Content for seeking |
| **Slice Module** | Implemented | 1MB chunks for large files |
| **Video Caching** | Implemented | 7-day TTL for video content |
| **Format Support** | Implemented | MP4, WebM, AVI, MOV, MKV, FLV, M4V |

### Video Upload & Access

```bash
# Upload video
curl -X POST http://localhost:8000/api/upload/multi \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -F "files=@video.mp4" \
  -F "bucket=videos"

# Access via CDN (supports seeking)
curl -I http://localhost/videos/video.mp4
# Returns: Accept-Ranges: bytes
```

### Planned Video Features

| Feature | Status |
|---------|--------|
| HLS Transcoding | Planned |
| DASH Support | Planned |
| Adaptive Bitrate | Planned |
| Thumbnail Generation | Planned |

---

## Configuration

### Environment Variables

Create a `.env` file based on `.env.example`:

```bash
# Domain Configuration
CDN_DOMAIN=cdn.yourdomain.com
CDN_PROTOCOL=https

# Database
DATABASE_URL=postgresql://cdn:cdn123@postgres:5432/cdn

# MinIO Storage
MINIO_ENDPOINT=origin-storage:9000
MINIO_ACCESS_KEY=admin
MINIO_SECRET_KEY=adminpassword123

# Redis
REDIS_URL=redis://redis:6379

# JWT Authentication
JWT_SECRET_KEY=your-secret-key-here
JWT_ALGORITHM=HS256
JWT_EXPIRE_MINUTES=30

# SSL/TLS (Production)
LETSENCRYPT_EMAIL=your-email@example.com
LETSENCRYPT_STAGING=false
```

### NGINX Cache Tuning

Edit `nginx/nginx.conf` to adjust cache settings:

```nginx
# Increase cache size
proxy_cache_path /var/cache/nginx/cdn
  levels=1:2
  keys_zone=cdn_cache:100m
  max_size=100g        # Increase from 50g
  inactive=60d         # Keep cached content longer
  use_temp_path=off;
```

### Video Streaming Optimization

Edit `nginx/conf.d/cdn.conf`:

```nginx
# Larger buffers for video streaming
proxy_buffer_size 64k;
proxy_buffers 16 64k;
proxy_busy_buffers_size 128k;
```

---

## Production Deployment

### Automated SSL Setup (Recommended)

```bash
# 1. Configure domain and email in .env
nano .env
# Set: CDN_DOMAIN=cdn.yourdomain.com
#      LETSENCRYPT_EMAIL=your-email@example.com
#      LETSENCRYPT_STAGING=false

# 2. Run automated setup script
chmod +x start-with-ssl.sh
./start-with-ssl.sh

# ✨ Done! Your CDN is now running with HTTPS
```

**The script automatically:**
1. ✅ Starts all Docker services
2. ✅ Requests Let's Encrypt certificate
3. ✅ Configures NGINX for HTTPS
4. ✅ Restarts services with SSL enabled
5. ✅ Completes in ~2 minutes

### Manual SSL Setup

For manual SSL configuration, use Certbot directly:
```bash
# Request certificate
docker-compose --profile ssl up -d certbot

# Verify certificate
docker-compose exec certbot certbot certificates
```

### Production Recommendations

```yaml
# docker-compose.yml adjustments for production
nginx-cdn:
  environment:
    - CDN_CACHE_SIZE=100g      # Increase cache size
    - CDN_CACHE_INACTIVE=60d   # Longer retention
  restart: always

backend-api:
  environment:
    - WORKERS=4                # Increase workers
  restart: always
```

### Scaling Considerations

For multi-region deployments:
1. 🌐 Deploy additional NGINX edge nodes in different regions
2. 🗺️ Use GeoDNS for region-based routing
3. 🔄 Configure MinIO multi-site replication
4. 💾 Use shared PostgreSQL database for centralized management
5. 📊 Aggregate metrics from all regions in Grafana

---

## Security

### Implemented Security Features

| Feature | Status | Notes |
|---------|--------|-------|
| JWT Authentication | Implemented | HS256, 24h expiration |
| API Key System | Implemented | For external integrations |
| Password Hashing | Implemented | Argon2 algorithm |
| Rate Limiting | Implemented | NGINX-level (100/10 req/s) |
| HTTPS/SSL | Implemented | Let's Encrypt via Certbot |

### Known Limitations (Address Before Production)

| Issue | Risk | Recommendation |
|-------|------|----------------|
| CORS allows all origins (`*`) | Medium | Restrict to specific domains |
| No file content validation | Medium | Add magic bytes check |
| No login brute-force protection | Medium | Implement account lockout |
| No per-API-key rate limiting | Low | Add Redis-based limiting |

### Pre-Deployment Checklist

```
[ ] Change all default passwords:
    - Admin UI: admin / admin123
    - MinIO: admin / adminpassword123
    - Grafana: admin / admin
    - PostgreSQL: cdn / cdn123

[ ] Generate secure JWT secret:
    openssl rand -hex 32

[ ] Configure CORS (backend/main.py):
    ALLOWED_ORIGINS = ["https://your-domain.com"]

[ ] Enable SSL:
    docker-compose --profile ssl up -d

[ ] Set firewall rules:
    - Allow: 80, 443
    - Block: 8000, 9010, 9011, 3000, 3001, 9090

[ ] Configure backup strategy
```

### Security Commands

```bash
# Generate secure JWT secret
openssl rand -hex 32

# Change admin password
curl -X PATCH http://localhost:8000/api/auth/change-password \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"old_password":"admin123","new_password":"YOUR_SECURE_PASSWORD"}'

# Change admin username
curl -X PATCH http://localhost:8000/api/auth/change-username \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"new_username":"your_username","password":"YOUR_PASSWORD"}'

# Rotate API key
curl -X DELETE http://localhost:8000/api/auth/api-keys/{key_id} \
  -H "Authorization: Bearer YOUR_JWT_TOKEN"
```

---

## Troubleshooting

### View Logs

```bash
# All services
docker-compose logs -f

# Specific service
docker-compose logs -f nginx-cdn
docker-compose logs -f backend-api
```

### Clear Cache Completely

```bash
# Clear NGINX cache
docker-compose exec nginx-cdn rm -rf /var/cache/nginx/*
docker-compose restart nginx-cdn
```

### Restart Services

```bash
# Single service
docker-compose restart nginx-cdn

# All services
docker-compose restart

# Rebuild and restart
docker-compose down
docker-compose up -d --build
```

### Common Issues

**Issue: Port already in use**
```bash
# Find process using port
sudo lsof -i :80
# Kill process or change port in docker-compose.yml
```

**Issue: Permission denied**
```bash
# Fix permissions
sudo chown -R $(whoami):$(whoami) ./nginx/cache
sudo chown -R $(whoami):$(whoami) ./storage
```

---

## Contributing

We welcome contributions! Please follow these steps:

1. **Fork the repository**
2. **Create a feature branch** (`git checkout -b feature/amazing-feature`)
3. **Commit your changes** (`git commit -m 'Add amazing feature'`)
4. **Push to the branch** (`git push origin feature/amazing-feature`)
5. **Open a Pull Request**

### Development Guidelines

- Follow existing code style
- Write clear commit messages
- Add tests for new features
- Update documentation
- Ensure all tests pass

### Reporting Issues

Please include:
- Detailed description of the issue
- Steps to reproduce
- Expected vs actual behavior
- Environment details (OS, Docker version)
- Relevant logs

---

## License

This project is licensed under the **MIT License** - see the [LICENSE](LICENSE) file for details.

```
MIT License

Copyright (c) 2026 netz-sg

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
```

---

## Acknowledgments

Built with amazing open-source technologies:
- [NGINX](https://nginx.org/) - High-performance web server
- [MinIO](https://min.io/) - S3-compatible object storage
- [FastAPI](https://fastapi.tiangolo.com/) - Modern Python web framework
- [React](https://react.dev/) - UI library
- [PostgreSQL](https://www.postgresql.org/) - Relational database
- [Redis](https://redis.io/) - In-memory data store
- [Prometheus](https://prometheus.io/) - Monitoring system
- [Grafana](https://grafana.com/) - Observability platform

---

## Support

- [Issue Tracker](https://github.com/netz-sg/cdn-network/issues)
- [Discussions](https://github.com/netz-sg/cdn-network/discussions)

---

<div align="center">

**If you find this project useful, please consider giving it a star!**

Made by [netz-sg](https://github.com/netz-sg)

</div>

# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Bird-CDN is a self-hosted Content Delivery Network for images and videos. It features NGINX edge caching, MinIO S3-compatible storage, a FastAPI backend, and a React admin UI.

## Commands

### Development (Docker-based)
```bash
# Start all services
docker-compose up -d

# Start with SSL profile
docker-compose --profile ssl up -d

# View logs
docker-compose logs -f [service-name]

# Rebuild specific service
docker-compose up -d --build backend-api
docker-compose up -d --build frontend
```

### Frontend (Vite + React)
```bash
cd frontend
npm install
npm run dev      # Development server
npm run build    # Production build
npm run preview  # Preview production build
```

### Backend (FastAPI)
The backend runs in Docker. For local development:
```bash
cd backend
pip install -r requirements.txt
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

## Architecture

### Services (docker-compose.yml)
- **nginx-cdn** (port 80/443): NGINX cache layer with SSL termination
- **backend-api** (port 8000): FastAPI REST API
- **frontend** (port 3000): React admin dashboard served via NGINX
- **origin-storage** (port 9010/9011): MinIO object storage
- **postgres**: PostgreSQL database
- **redis**: Session and metadata caching
- **prometheus** (port 9090): Metrics collection
- **grafana** (port 3001): Monitoring dashboards

### Backend Structure (`backend/`)
- `main.py`: FastAPI app entry point, middleware configuration, router registration
- `models.py`: SQLAlchemy models (User, APIKey, UploadedFile, CacheEntry, BandwidthLog, WatermarkConfig, SystemSetting)
- `auth.py`: JWT authentication and password hashing
- `routers/`: API route modules
  - `auth.py`: Login, password/username change
  - `upload_v2.py`: File upload handling
  - `transform.py`: Image transformation API
  - `cache.py`, `purge.py`: Cache management
  - `stats.py`: Analytics endpoints
  - `admin.py`: Administration endpoints
  - `watermark.py`: Watermark configuration
  - `settings.py`: System settings
  - `update.py`: Self-update functionality

### Frontend Structure (`frontend/src/`)
- `App.jsx`: Main router and layout
- `api.js`: Axios API client configuration
- `context/AuthContext.jsx`: Authentication state management
- `pages/`: Route components (Dashboard, UploadPage, FilesPage, CachePage, StatsPage, AdminPage, SettingsPage, WatermarkPage, ApiKeysPage)
- `components/ProtectedRoute.jsx`: Auth guard component

### API Routes
All API endpoints are prefixed with `/api`:
- `/api/auth/*`: Authentication
- `/api/upload`, `/api/files`: File management
- `/api/transform/*`: Image transformations
- `/api/cache/*`, `/api/purge/*`: Cache operations
- `/api/stats/*`: Statistics and analytics
- `/api/admin/*`: Administration
- `/api/settings/*`: System settings

### Key Technologies
- **Backend**: Python 3.12, FastAPI, SQLAlchemy, Pydantic, MinIO SDK, Pillow
- **Frontend**: React 18, Vite, React Router, Axios, Recharts, Lucide icons
- **Infrastructure**: NGINX, PostgreSQL, Redis, MinIO, Prometheus, Grafana

## Important Constraints

- **Never start the server** - the user handles that
- **Never commit or push to git** - the user handles version control
- **Match existing design patterns** - follow the website's existing UI style
- **Localization required** - all content must support German and English (Sanity CMS provides translations)
- **Sanity schemas need localization** - when adding new Sanity schemas, include language support
- **No build errors allowed** - verify builds succeed when implementing new features

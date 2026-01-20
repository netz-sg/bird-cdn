# � Bird-CDN API Documentation

## Übersicht

Das CDN-System wurde um folgende Features erweitert:

1. **JWT Authentication** für Admin-Login
2. **API-Key System** für externe Apps (PayloadCMS)
3. **Multi-Upload** - mehrere Dateien gleichzeitig
4. **Wasserzeichen** - automatisches Logo auf Bildern
5. **Sicherheit** - Auth-geschützte Endpoints
6. **🆕 Image Transformation API** - On-the-fly Resize/Crop/Format-Konvertierung

---

## 1. Authentication

### 🔐 Admin Login

**Endpoint:** `POST /api/auth/login`

```bash
curl -X POST http://localhost/api/auth/login \
  -F "username=admin" \
  -F "password=admin123"
```

**Response:**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "user": {
    "id": 1,
    "username": "admin",
    "email": "admin@cdn-tourdiary.local",
    "role": "admin"
  }
}
```

### 📱 Authentifizierte Requests

**Mit JWT Token:**
```bash
curl -H "Authorization: Bearer YOUR_TOKEN" \
  http://localhost/api/upload
```

**Mit API Key:**
```bash
curl -H "X-API-Key: YOUR_API_KEY" \
  http://localhost/api/upload
```

---

## 2. API-Key Management

### ✨ API-Key erstellen

**Endpoint:** `POST /api/auth/api-keys`

```bash
curl -X POST http://localhost/api/auth/api-keys \
  -H "Authorization: Bearer YOUR_ADMIN_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "PayloadCMS Production",
    "expires_in_days": 365
  }'
```

**Response:**
```json
{
  "id": 1,
  "name": "PayloadCMS Production",
  "key": "cdn_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx",
  "is_active": true,
  "created_at": "2026-01-20T00:00:00Z",
  "expires_at": "2027-01-20T00:00:00Z"
}
```

⚠️ **WICHTIG:** Speichere den Key sofort! Er wird nur einmal angezeigt!

### 📋 API-Keys auflisten

```bash
curl -H "Authorization: Bearer YOUR_ADMIN_TOKEN" \
  http://localhost/api/auth/api-keys
```

### 🗑️ API-Key löschen

```bash
curl -X DELETE \
  -H "Authorization: Bearer YOUR_ADMIN_TOKEN" \
  http://localhost/api/auth/api-keys/1
```

---

## 3. Multi-Upload

### 📤 Mehrere Dateien gleichzeitig hochladen

**Endpoint:** `POST /api/upload/multi`

```bash
curl -X POST http://localhost/api/upload/multi \
  -H "X-API-Key: YOUR_API_KEY" \
  -F "files=@image1.jpg" \
  -F "files=@image2.png" \
  -F "files=@image3.webp" \
  -F "bucket=media" \
  -F "folder=products" \
  -F "apply_watermark_flag=true" \
  -F "watermark_position=bottom-right"
```

**Parameter:**
- `files` - Mehrere Dateien (max. 50)
- `bucket` - Ziel-Bucket (default: media)
- `folder` - Subfolder (optional)
- `apply_watermark_flag` - Wasserzeichen anwenden (true/false)
- `watermark_position` - Position: `top-left`, `top-right`, `bottom-left`, `bottom-right`, `center`

**Response:**
```json
{
  "success": true,
  "uploaded": 3,
  "failed": 0,
  "results": [
    {
      "success": true,
      "file_id": 1,
      "filename": "20260120_001234_abc123.webp",
      "original_filename": "image1.jpg",
      "cdn_url": "http://localhost/media/products/20260120_001234_abc123.webp",
      "size": 123456,
      "type": "image",
      "dimensions": {"width": 1920, "height": 1080}
    }
  ]
}
```

---

## 4. Wasserzeichen

### 🎨 Wasserzeichen-Logo hochladen

**Endpoint:** `POST /api/watermark/upload`

```bash
curl -X POST http://localhost/api/watermark/upload \
  -H "Authorization: Bearer YOUR_ADMIN_TOKEN" \
  -F "file=@logo.png"
```

**Empfehlung:**
- Format: PNG mit Transparenz
- Größe: max. 500x500px
- Wird automatisch auf 20% der Bildbreite skaliert

### 📊 Wasserzeichen-Status prüfen

```bash
curl http://localhost/api/watermark/status
```

**Response:**
```json
{
  "configured": true,
  "path": "/app/watermark.png"
}
```

### 🗑️ Wasserzeichen löschen

```bash
curl -X DELETE \
  -H "Authorization: Bearer YOUR_ADMIN_TOKEN" \
  http://localhost/api/watermark
```

---

## 5. PayloadCMS Integration

### 🔌 Setup in PayloadCMS

```javascript
// payload.config.ts
import { s3Adapter } from '@payloadcms/plugin-cloud-storage/s3'

export default buildConfig({
  plugins: [
    cloudStorage({
      collections: {
        'media': {
          adapter: s3Adapter({
            config: {
              endpoint: 'http://localhost',
              credentials: {
                accessKeyId: 'YOUR_API_KEY',
                secretAccessKey: 'not-used'
              },
              region: 'eu-central-1',
              // Custom upload headers
              customHeaders: {
                'X-API-Key': 'YOUR_CDN_API_KEY'
              }
            },
            bucket: 'media'
          })
        }
      }
    })
  ]
})
```

### 📡 Custom Upload Hook

```javascript
// Alternative: Direkter API-Call
const uploadToC CDN = async (files) => {
  const formData = new FormData()
  
  files.forEach(file => {
    formData.append('files', file)
  })
  
  formData.append('bucket', 'media')
  formData.append('folder', 'cms-uploads')
  formData.append('apply_watermark_flag', 'true')
  
  const response = await fetch('http://localhost/api/upload/multi', {
    method: 'POST',
    headers: {
      'X-API-Key': 'cdn_your_api_key_here'
    },
    body: formData
  })
  
  return response.json()
}
```

---

## 6. Sicherheit

### 🔒 Features

1. **JWT Token Authentication**
   - Secure token-based auth
   - 24h Expiration (konfigurierbar)
   - Role-based access (admin, user)

2. **API Key System**
   - Lange, sichere Keys
   - Ablaufdatum konfigurierbar
   - Per-Key Tracking (last_used_at)

3. **Protected Endpoints**
   - Alle Upload-Endpoints benötigen Auth
   - Admin-Endpoints nur für Admin-Role
   - API Keys für externe Apps

4. **WebP Conversion**
   - Automatische Konvertierung
   - 25-35% kleinere Dateien
   - Bessere Performance

5. **Watermark Protection**
   - Erschwert unbefugte Nutzung
   - Konfigurierbare Position & Opazität
   - Automatisch auf alle Bilder

---

## 7. API-Übersicht

### Authentication
- `POST /api/auth/login` - Login
- `POST /api/auth/register` - Registrierung (admin-only)
- `GET /api/auth/me` - Aktueller User
- `POST /api/auth/api-keys` - API-Key erstellen
- `GET /api/auth/api-keys` - API-Keys auflisten
- `DELETE /api/auth/api-keys/{id}` - API-Key löschen

### Upload
- `POST /api/upload` - Single Upload (mit Auth)
- `POST /api/upload/multi` - Multi Upload (mit Auth)

### Watermark
- `POST /api/watermark/upload` - Wasserzeichen hochladen
- `GET /api/watermark/status` - Status prüfen
- `DELETE /api/watermark` - Wasserzeichen löschen

### Stats (unverändert)
- `GET /api/stats/overview`
- `GET /api/stats/bandwidth`
- `GET /api/stats/top-files`

---

## 8. Erste Schritte

### 🎬 Schnellstart

```bash
# 1. System starten
cd D:\Dev\cdn-tourdiary
.\start.bat

# 2. Admin-Login
curl -X POST http://localhost/api/auth/login \
  -F "username=admin" \
  -F "password=admin123"

# 3. API-Key erstellen
curl -X POST http://localhost/api/auth/api-keys \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"name": "Test Key"}'

# 4. Wasserzeichen hochladen
curl -X POST http://localhost/api/watermark/upload \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -F "file=@logo.png"

# 5. Multi-Upload mit Wasserzeichen
curl -X POST http://localhost/api/upload/multi \
  -H "X-API-Key: YOUR_API_KEY" \
  -F "files=@test1.jpg" \
  -F "files=@test2.png" \
  -F "apply_watermark_flag=true"
```

---

## 9. Swagger UI

Vollständige API-Dokumentation:
```
http://localhost:8000/docs
```

Alle Endpoints mit:
- Request/Response Schemas
- Try-it-out Funktion
- Authentication Flow
- Example Values

---

## 10. Credentials

### 🔑 Default Login

**Admin:**
- Username: `admin`
- Password: `admin123`
- Email: `admin@cdn-tourdiary.local`

⚠️ **WICHTIG:** Ändere das Passwort in Production!

```bash
# Passwort ändern (TODO: Endpoint implementieren)
curl -X PATCH http://localhost/api/auth/change-password \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -d '{"old_password": "admin123", "new_password": "YOUR_NEW_PASSWORD"}'
```

---

## 📝 Notizen

- **Max Upload Size:** 100MB (konfigurierbar in config.py)
- **Max Files per Multi-Upload:** 50
- **Supported Formats:** JPG, PNG, GIF, WEBP, SVG, MP4, WEBM, MOV, AVI, MKV
- **Auto WebP Conversion:** Ja (für alle Bilder)
- **Watermark Format:** PNG recommended
- **Token Expiration:** 24 Stunden
- **API Key Expiration:** Konfigurierbar (default: no expiration)

---

## 🆕 7. Image Transformation API

### 🖼️ On-the-fly Bildbearbeitung

**Endpoint:** `GET /api/transform/{bucket}/{path}`

Die Transformation API ermöglicht Echtzeit-Bildbearbeitung mit automatischem Caching.

**Beispiele:**

```bash
# Resize zu 800x600 WebP
curl "http://localhost/api/transform/media/image.jpg?w=800&h=600&format=webp"

# Square Thumbnail mit Center-Crop
curl "http://localhost/api/transform/media/photo.png?w=400&h=400&fit=cover&crop=center"

# Format-Konvertierung mit hoher Qualität
curl "http://localhost/api/transform/media/banner.jpg?format=webp&quality=95"

# Responsive Width (maintain aspect ratio)
curl "http://localhost/api/transform/media/hero.jpg?w=1200&fit=contain"
```

**Parameter:**

| Parameter | Typ     | Beschreibung                          | Beispiel      |
|-----------|---------|---------------------------------------|---------------|
| `w`       | integer | Zielbreite in Pixel (1-4000)          | `w=800`       |
| `h`       | integer | Zielhöhe in Pixel (1-4000)            | `h=600`       |
| `format`  | string  | Ausgabeformat (webp, jpg, png, gif)   | `format=webp` |
| `quality` | integer | Qualität 1-100 (default: 85)          | `quality=90`  |
| `fit`     | string  | Resize-Modus (contain, cover, fill, inside) | `fit=cover` |
| `crop`    | string  | Crop-Modus (center, top, bottom, left, right, entropy) | `crop=center` |

### 📖 Transformation Info

```bash
# Vollständige Dokumentation abrufen
curl http://localhost/api/transform-info
```

**Response:** Detaillierte Info über alle Parameter, Limits und Beispiele.

### 🚀 Performance & Caching

- **Cache-Dauer:** 30 Tage (NGINX Cache)
- **Erste Request:** ~200-500ms (Processing)
- **Nachfolgende Requests:** ~5-20ms (Cache HIT)
- **Cache-Status:** Im `X-Cache-Status` Header

### 💡 Best Practice - Responsive Srcset

```html
<img 
  src="/api/transform/media/image.jpg?w=800&format=webp"
  srcset="
    /api/transform/media/image.jpg?w=400&format=webp 400w,
    /api/transform/media/image.jpg?w=800&format=webp 800w,
    /api/transform/media/image.jpg?w=1200&format=webp 1200w
  "
  sizes="(max-width: 768px) 100vw, 800px"
  alt="Responsive Image">
```

**Ausführliche Dokumentation:** Siehe [IMAGE_TRANSFORM_API.md](IMAGE_TRANSFORM_API.md)

---

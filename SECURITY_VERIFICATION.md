# API Security Hardening - Verification Guide

## Summary of Changes

All previously unprotected endpoints have been secured with authentication requirements:

### 1. Cache Router (`backend/routers/cache.py`)
- ✅ `GET /api/cache/status` - Now requires JWT or API Key
- ✅ `GET /api/cache/list` - Now requires JWT or API Key
- ✅ `POST /api/cache/update` - Now requires JWT or API Key

### 2. Purge Router (`backend/routers/purge.py`)
- ✅ `DELETE /api/purge` - Now requires JWT or API Key
- ✅ `DELETE /api/purge/bucket/{name}` - Now requires JWT or API Key
- ✅ `DELETE /api/purge/all` - Now requires JWT or API Key
- ✅ `GET /api/purge/history` - Now requires JWT or API Key

### 3. Admin Router (`backend/routers/admin.py`)
- ✅ `GET /api/admin/buckets` - Now requires **Admin JWT only**
- ✅ `POST /api/admin/buckets` - Now requires **Admin JWT only**
- ✅ `POST /api/admin/buckets/{name}/public` - Now requires **Admin JWT only**
- ✅ `GET /api/admin/system-info` - Now requires **Admin JWT only**

### 4. Tracking Router (`backend/routers/tracking.py`)
- ✅ `POST /api/tracking/track/download/{id}` - Now requires JWT or API Key
- ✅ `POST /api/tracking/track/cache-hit` - Now requires JWT or API Key
- ✅ `POST /api/tracking/aggregate-logs` - Now requires JWT or API Key

---

## Authentication Methods Supported

| Method | Header | Example | Works For |
|--------|--------|---------|-----------|
| JWT Token | `Authorization: Bearer <token>` | `Bearer eyJhbGc...` | All endpoints |
| API Key (Bearer) | `Authorization: Bearer <api_key>` | `Bearer cdn_j5kz...` | Non-admin endpoints |
| API Key (X-API-Key) | `X-API-Key: <api_key>` | `cdn_j5kz...` | Non-admin endpoints |

**Note:** Admin endpoints (`/api/admin/*`) require a **JWT token from an admin user**. API keys will return `403 Forbidden`.

---

## Verification Commands

### Setup
First, obtain valid credentials:

```powershell
# Login to get JWT token
$loginResponse = curl -s -X POST http://localhost:8000/api/auth/login `
  -H "Content-Type: application/json" `
  -d '{"username":"Sebastian","password":"your_password"}' | ConvertFrom-Json

$JWT_TOKEN = $loginResponse.access_token

# Use existing API key
$API_KEY = "cdn_j5kzzQNHVKJFHSNZGGuiTVNk48-oe8aH433YWiYShGI"
```

### Test 1: Cache Endpoints (Should Return 401 Without Auth)

```powershell
# Without auth - should fail with 401
curl -i http://localhost:8000/api/cache/status?path=/test

# Expected Response:
# HTTP/1.1 401 Unauthorized
# {"detail":"Valid authentication required (JWT token or API key)"}
```

### Test 2: Cache Endpoints (Should Work With JWT)

```powershell
# With JWT token - should succeed
curl -i http://localhost:8000/api/cache/status?path=/test `
  -H "Authorization: Bearer $JWT_TOKEN"

# Expected Response:
# HTTP/1.1 200 OK
# {"path":"/test","cached":false,"message":"Not in cache"}
```

### Test 3: Cache Endpoints (Should Work With API Key)

```powershell
# With X-API-Key header - should succeed
curl -i http://localhost:8000/api/cache/status?path=/test `
  -H "X-API-Key: $API_KEY"

# Expected Response:
# HTTP/1.1 200 OK
# {"path":"/test","cached":false,...}

# With Bearer API Key - should also succeed
curl -i http://localhost:8000/api/cache/status?path=/test `
  -H "Authorization: Bearer $API_KEY"

# Expected Response:
# HTTP/1.1 200 OK
```

### Test 4: Purge Endpoints (Should Return 401 Without Auth)

```powershell
# Without auth - should fail
curl -i -X DELETE "http://localhost:8000/api/purge?path=/media/test.jpg"

# Expected Response:
# HTTP/1.1 401 Unauthorized
```

### Test 5: Purge Endpoints (Should Work With Auth)

```powershell
# With JWT - should succeed
curl -i -X DELETE "http://localhost:8000/api/purge?path=/media/test.jpg" `
  -H "Authorization: Bearer $JWT_TOKEN"

# Expected Response:
# HTTP/1.1 200 OK
# {"success":true,"path":"/media/test.jpg",...}

# With API Key - should also succeed
curl -i -X DELETE "http://localhost:8000/api/purge?path=/media/test.jpg" `
  -H "X-API-Key: $API_KEY"

# Expected Response:
# HTTP/1.1 200 OK
```

### Test 6: Admin Endpoints (Should Return 401 Without Auth)

```powershell
# Without auth - should fail
curl -i http://localhost:8000/api/admin/buckets

# Expected Response:
# HTTP/1.1 401 Unauthorized
```

### Test 7: Admin Endpoints (Should Return 403 With Non-Admin JWT)

```powershell
# If you have a non-admin user JWT:
# Should return 403 Forbidden
curl -i http://localhost:8000/api/admin/buckets `
  -H "Authorization: Bearer $NON_ADMIN_JWT"

# Expected Response:
# HTTP/1.1 403 Forbidden
# {"detail":"Admin privileges required"}
```

### Test 8: Admin Endpoints (Should Return 403 With API Key)

```powershell
# API Keys cannot access admin endpoints
curl -i http://localhost:8000/api/admin/buckets `
  -H "X-API-Key: $API_KEY"

# Expected Response:
# HTTP/1.1 403 Forbidden
# {"detail":"Admin privileges required"}
```

### Test 9: Admin Endpoints (Should Work With Admin JWT)

```powershell
# With admin JWT - should succeed
curl -i http://localhost:8000/api/admin/buckets `
  -H "Authorization: Bearer $JWT_TOKEN"

# Expected Response (assuming Sebastian is admin):
# HTTP/1.1 200 OK
# {"buckets":[{"name":"media","created":"..."},...]}
```

### Test 10: Tracking Endpoints (Should Return 401 Without Auth)

```powershell
# Without auth - should fail
curl -i -X POST http://localhost:8000/api/tracking/track/cache-hit `
  -H "Content-Type: application/json" `
  -d '{"path":"/media/test.jpg","bytes_sent":1024}'

# Expected Response:
# HTTP/1.1 401 Unauthorized
```

### Test 11: Tracking Endpoints (Should Work With Auth)

```powershell
# With JWT or API Key - should succeed
curl -i -X POST http://localhost:8000/api/tracking/track/cache-hit `
  -H "Content-Type: application/json" `
  -H "Authorization: Bearer $JWT_TOKEN" `
  -d '{"path":"/media/test.jpg","bytes_sent":1024}'

# Expected Response:
# HTTP/1.1 200 OK
# {"status":"ok"}
```

---

## Quick Test Script

Run all tests automatically:

```powershell
# Save as test-security.ps1

# Configuration
$BASE_URL = "http://localhost:8000"
$USERNAME = "Sebastian"
$PASSWORD = "your_password"
$API_KEY = "cdn_j5kzzQNHVKJFHSNZGGuiTVNk48-oe8aH433YWiYShGI"

Write-Host "`n=== API Security Verification Tests ===" -ForegroundColor Cyan

# Login to get JWT
Write-Host "`n[1/11] Obtaining JWT token..." -ForegroundColor Yellow
try {
    $loginResponse = Invoke-RestMethod -Method POST -Uri "$BASE_URL/api/auth/login" `
        -ContentType "application/json" `
        -Body (@{username=$USERNAME;password=$PASSWORD} | ConvertTo-Json)
    $JWT_TOKEN = $loginResponse.access_token
    Write-Host "✅ JWT token obtained" -ForegroundColor Green
} catch {
    Write-Host "❌ Login failed: $_" -ForegroundColor Red
    exit 1
}

# Test 1: Unauthenticated cache request
Write-Host "`n[2/11] Testing unauthenticated cache request (should fail)..." -ForegroundColor Yellow
try {
    $response = Invoke-WebRequest -Uri "$BASE_URL/api/cache/status?path=/test" -ErrorAction Stop
    Write-Host "❌ FAILED: Request succeeded without auth (expected 401)" -ForegroundColor Red
} catch {
    if ($_.Exception.Response.StatusCode -eq 401) {
        Write-Host "✅ PASSED: 401 Unauthorized as expected" -ForegroundColor Green
    } else {
        Write-Host "❌ FAILED: Wrong status code: $($_.Exception.Response.StatusCode)" -ForegroundColor Red
    }
}

# Test 2: Authenticated cache request with JWT
Write-Host "`n[3/11] Testing authenticated cache request with JWT..." -ForegroundColor Yellow
try {
    $headers = @{Authorization = "Bearer $JWT_TOKEN"}
    $response = Invoke-RestMethod -Uri "$BASE_URL/api/cache/status?path=/test" -Headers $headers
    Write-Host "✅ PASSED: Cache status accessible with JWT" -ForegroundColor Green
} catch {
    Write-Host "❌ FAILED: $_" -ForegroundColor Red
}

# Test 3: Authenticated cache request with API Key
Write-Host "`n[4/11] Testing authenticated cache request with API Key..." -ForegroundColor Yellow
try {
    $headers = @{"X-API-Key" = $API_KEY}
    $response = Invoke-RestMethod -Uri "$BASE_URL/api/cache/status?path=/test" -Headers $headers
    Write-Host "✅ PASSED: Cache status accessible with API Key" -ForegroundColor Green
} catch {
    Write-Host "❌ FAILED: $_" -ForegroundColor Red
}

# Test 4: Unauthenticated purge request
Write-Host "`n[5/11] Testing unauthenticated purge request (should fail)..." -ForegroundColor Yellow
try {
    $response = Invoke-WebRequest -Method DELETE -Uri "$BASE_URL/api/purge?path=/test" -ErrorAction Stop
    Write-Host "❌ FAILED: Purge succeeded without auth (expected 401)" -ForegroundColor Red
} catch {
    if ($_.Exception.Response.StatusCode -eq 401) {
        Write-Host "✅ PASSED: 401 Unauthorized as expected" -ForegroundColor Green
    } else {
        Write-Host "❌ FAILED: Wrong status code: $($_.Exception.Response.StatusCode)" -ForegroundColor Red
    }
}

# Test 5: Authenticated purge with JWT
Write-Host "`n[6/11] Testing authenticated purge with JWT..." -ForegroundColor Yellow
try {
    $headers = @{Authorization = "Bearer $JWT_TOKEN"}
    $response = Invoke-RestMethod -Method DELETE -Uri "$BASE_URL/api/purge?path=/test" -Headers $headers
    Write-Host "✅ PASSED: Purge accessible with JWT" -ForegroundColor Green
} catch {
    Write-Host "❌ FAILED: $_" -ForegroundColor Red
}

# Test 6: Unauthenticated admin request
Write-Host "`n[7/11] Testing unauthenticated admin request (should fail)..." -ForegroundColor Yellow
try {
    $response = Invoke-WebRequest -Uri "$BASE_URL/api/admin/buckets" -ErrorAction Stop
    Write-Host "❌ FAILED: Admin endpoint accessible without auth (expected 401)" -ForegroundColor Red
} catch {
    if ($_.Exception.Response.StatusCode -eq 401) {
        Write-Host "✅ PASSED: 401 Unauthorized as expected" -ForegroundColor Green
    } else {
        Write-Host "❌ FAILED: Wrong status code: $($_.Exception.Response.StatusCode)" -ForegroundColor Red
    }
}

# Test 7: Admin request with API Key (should fail with 403)
Write-Host "`n[8/11] Testing admin request with API Key (should fail with 403)..." -ForegroundColor Yellow
try {
    $headers = @{"X-API-Key" = $API_KEY}
    $response = Invoke-WebRequest -Uri "$BASE_URL/api/admin/buckets" -Headers $headers -ErrorAction Stop
    Write-Host "❌ FAILED: Admin endpoint accessible with API Key (expected 403)" -ForegroundColor Red
} catch {
    if ($_.Exception.Response.StatusCode -eq 403 -or $_.Exception.Response.StatusCode -eq 401) {
        Write-Host "✅ PASSED: Access denied as expected (403 or 401)" -ForegroundColor Green
    } else {
        Write-Host "❌ FAILED: Wrong status code: $($_.Exception.Response.StatusCode)" -ForegroundColor Red
    }
}

# Test 8: Admin request with admin JWT
Write-Host "`n[9/11] Testing admin request with admin JWT..." -ForegroundColor Yellow
try {
    $headers = @{Authorization = "Bearer $JWT_TOKEN"}
    $response = Invoke-RestMethod -Uri "$BASE_URL/api/admin/buckets" -Headers $headers
    Write-Host "✅ PASSED: Admin endpoint accessible with admin JWT" -ForegroundColor Green
} catch {
    Write-Host "❌ FAILED: $_" -ForegroundColor Red
}

# Test 9: Unauthenticated tracking request
Write-Host "`n[10/11] Testing unauthenticated tracking request (should fail)..." -ForegroundColor Yellow
try {
    $body = @{path="/test";bytes_sent=1024} | ConvertTo-Json
    $response = Invoke-WebRequest -Method POST -Uri "$BASE_URL/api/tracking/track/cache-hit" `
        -ContentType "application/json" -Body $body -ErrorAction Stop
    Write-Host "❌ FAILED: Tracking succeeded without auth (expected 401)" -ForegroundColor Red
} catch {
    if ($_.Exception.Response.StatusCode -eq 401) {
        Write-Host "✅ PASSED: 401 Unauthorized as expected" -ForegroundColor Green
    } else {
        Write-Host "❌ FAILED: Wrong status code: $($_.Exception.Response.StatusCode)" -ForegroundColor Red
    }
}

# Test 10: Authenticated tracking with JWT
Write-Host "`n[11/11] Testing authenticated tracking with JWT..." -ForegroundColor Yellow
try {
    $headers = @{Authorization = "Bearer $JWT_TOKEN"}
    $body = @{path="/test";bytes_sent=1024} | ConvertTo-Json
    $response = Invoke-RestMethod -Method POST -Uri "$BASE_URL/api/tracking/track/cache-hit" `
        -Headers $headers -ContentType "application/json" -Body $body
    Write-Host "✅ PASSED: Tracking accessible with JWT" -ForegroundColor Green
} catch {
    Write-Host "❌ FAILED: $_" -ForegroundColor Red
}

Write-Host "`n=== All Security Tests Completed ===" -ForegroundColor Cyan
```

---

## Expected Behavior Summary

| Endpoint | No Auth | API Key | User JWT | Admin JWT |
|----------|---------|---------|----------|-----------|
| `/api/cache/*` | 401 ❌ | 200 ✅ | 200 ✅ | 200 ✅ |
| `/api/purge/*` | 401 ❌ | 200 ✅ | 200 ✅ | 200 ✅ |
| `/api/admin/*` | 401 ❌ | 403 ❌ | 403 ❌ | 200 ✅ |
| `/api/tracking/*` | 401 ❌ | 200 ✅ | 200 ✅ | 200 ✅ |

---

## Security Best Practices Implemented

✅ **Authentication Required**: All endpoints now require valid credentials
✅ **Role-Based Access Control**: Admin endpoints restricted to admin users only
✅ **Flexible Auth**: Supports both JWT tokens and API keys where appropriate
✅ **Proper HTTP Status Codes**: 401 for missing/invalid auth, 403 for insufficient permissions
✅ **No Information Leakage**: Unauthorized requests don't reveal endpoint structure

---

## Next Steps (Optional Enhancements)

1. **Rate Limiting**: Add rate limiting to prevent abuse
2. **Audit Logging**: Log all authenticated requests for security auditing
3. **Token Expiration**: Ensure JWT tokens have reasonable expiration times
4. **API Key Scoping**: Consider adding permission scopes to API keys
5. **IP Whitelisting**: For sensitive operations like purge/admin

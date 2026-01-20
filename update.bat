@echo off
REM CDN System Update Script for Windows
REM Führt automatisches Update mit Backup durch

echo.
echo ====================================
echo CDN System Update
echo ====================================
echo.

REM Timestamp für Backups
set TIMESTAMP=%date:~-4%%date:~-7,2%%date:~-10,2%_%time:~0,2%%time:~3,2%%time:~6,2%
set TIMESTAMP=%TIMESTAMP: =0%
set BACKUP_DIR=backups

REM Backup-Verzeichnis erstellen
if not exist "%BACKUP_DIR%" mkdir "%BACKUP_DIR%"

REM ============================================
REM STEP 1: Datenbank Backup
REM ============================================
echo [1/6] Erstelle Datenbank-Backup...
docker exec cdn-postgres pg_dump -U cdn cdn > "%BACKUP_DIR%\db_backup_%TIMESTAMP%.sql"
if %ERRORLEVEL% NEQ 0 (
    echo [FEHLER] Datenbank-Backup fehlgeschlagen!
    exit /b 1
)
echo [OK] Datenbank-Backup erfolgreich
echo.

REM ============================================
REM STEP 2: Storage Backup
REM ============================================
echo [2/6] Erstelle Storage-Backup...
if exist "storage\data" (
    xcopy /E /I /Y "storage\data" "%BACKUP_DIR%\storage_%TIMESTAMP%" > nul
    echo [OK] Storage-Backup erfolgreich
) else (
    echo [WARNUNG] Kein Storage-Verzeichnis gefunden
)
echo.

REM ============================================
REM STEP 3: Git Pull
REM ============================================
echo [3/6] Lade Updates von GitHub...
git fetch origin main
if %ERRORLEVEL% NEQ 0 (
    echo [FEHLER] Git fetch fehlgeschlagen!
    exit /b 1
)

REM Prüfe ob Updates vorhanden
git rev-list --count HEAD..origin/main > temp_count.txt
set /p COMMITS_BEHIND=<temp_count.txt
del temp_count.txt

if "%COMMITS_BEHIND%"=="0" (
    echo [INFO] Keine neuen Commits vorhanden
    echo [WARNUNG] Fahre trotzdem mit Rebuild fort...
    goto :build
)

echo [OK] %COMMITS_BEHIND% neue Update(s) gefunden
echo.
echo Neue Commits:
git log --oneline HEAD..origin/main --pretty=format:"  - %%h - %%s"
echo.
echo.

git pull origin main
if %ERRORLEVEL% NEQ 0 (
    echo [FEHLER] Git pull fehlgeschlagen!
    exit /b 1
)
echo [OK] Updates heruntergeladen

:build
echo.

REM ============================================
REM STEP 4: Frontend neu bauen
REM ============================================
echo [4/6] Baue Frontend neu...
docker-compose build frontend
if %ERRORLEVEL% NEQ 0 (
    echo [FEHLER] Frontend Build fehlgeschlagen!
    exit /b 1
)
echo [OK] Frontend Build abgeschlossen
echo.

REM ============================================
REM STEP 5: Backend neu bauen
REM ============================================
echo [5/6] Baue Backend neu...
docker-compose build backend-api
if %ERRORLEVEL% NEQ 0 (
    echo [FEHLER] Backend Build fehlgeschlagen!
    exit /b 1
)
echo [OK] Backend Build abgeschlossen
echo.

REM ============================================
REM STEP 6: Container neu starten
REM ============================================
echo [6/6] Starte Container neu...
docker-compose up -d
if %ERRORLEVEL% NEQ 0 (
    echo [FEHLER] Container-Start fehlgeschlagen!
    exit /b 1
)
echo [OK] Container neu gestartet
echo.

REM ============================================
REM Fertig!
REM ============================================
echo ========================================
echo Update erfolgreich abgeschlossen!
echo ========================================
echo.
echo Backups:
echo   - Datenbank: %BACKUP_DIR%\db_backup_%TIMESTAMP%.sql
if exist "%BACKUP_DIR%\storage_%TIMESTAMP%" (
    echo   - Storage:   %BACKUP_DIR%\storage_%TIMESTAMP%
)
echo.
echo Services:
echo   - Frontend:    http://localhost:3000
echo   - Backend:     http://localhost:8000
echo   - Grafana:     http://localhost:3001
echo   - Prometheus:  http://localhost:9090
echo   - MinIO:       http://localhost:9011
echo.
pause

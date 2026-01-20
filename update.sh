#!/bin/bash
# CDN System Update Script
# Führt automatisches Update mit Backup durch

set -e  # Exit bei Fehler

echo "🔄 CDN System Update wird gestartet..."
echo ""

# Farben für Output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Timestamp für Backups
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
BACKUP_DIR="./backups"

# Backup-Verzeichnis erstellen
mkdir -p "$BACKUP_DIR"

# ============================================
# STEP 1: Datenbank Backup
# ============================================
echo -e "${YELLOW}[1/6]${NC} Erstelle Datenbank-Backup..."
docker exec cdn-postgres pg_dump -U cdn cdn > "$BACKUP_DIR/db_backup_$TIMESTAMP.sql"
if [ $? -eq 0 ]; then
    echo -e "${GREEN}✓${NC} Datenbank-Backup erfolgreich: $BACKUP_DIR/db_backup_$TIMESTAMP.sql"
else
    echo -e "${RED}✗${NC} Datenbank-Backup fehlgeschlagen!"
    exit 1
fi
echo ""

# ============================================
# STEP 2: Storage Backup
# ============================================
echo -e "${YELLOW}[2/6]${NC} Erstelle Storage-Backup..."
if [ -d "./storage/data" ]; then
    cp -r ./storage/data "$BACKUP_DIR/storage_$TIMESTAMP"
    echo -e "${GREEN}✓${NC} Storage-Backup erfolgreich: $BACKUP_DIR/storage_$TIMESTAMP"
else
    echo -e "${YELLOW}⚠${NC} Kein Storage-Verzeichnis gefunden, überspringe..."
fi
echo ""

# ============================================
# STEP 3: Git Pull
# ============================================
echo -e "${YELLOW}[3/6]${NC} Lade Updates von GitHub..."
git fetch origin main
COMMITS_BEHIND=$(git rev-list --count HEAD..origin/main)

if [ "$COMMITS_BEHIND" -eq 0 ]; then
    echo -e "${GREEN}✓${NC} Keine neuen Commits vorhanden"
    echo -e "${YELLOW}⚠${NC} Fahre trotzdem mit Rebuild fort..."
else
    echo -e "${GREEN}✓${NC} $COMMITS_BEHIND neue Update(s) gefunden"
    echo ""
    echo "Neue Commits:"
    git log --oneline HEAD..origin/main --pretty=format:"  • %h - %s (%an, %ar)"
    echo ""
    echo ""
    
    git pull origin main
    echo -e "${GREEN}✓${NC} Updates heruntergeladen"
fi
echo ""

# ============================================
# STEP 4: Frontend neu bauen
# ============================================
echo -e "${YELLOW}[4/6]${NC} Baue Frontend neu..."
docker-compose build frontend
echo -e "${GREEN}✓${NC} Frontend Build abgeschlossen"
echo ""

# ============================================
# STEP 5: Backend neu bauen
# ============================================
echo -e "${YELLOW}[5/6]${NC} Baue Backend neu..."
docker-compose build backend-api
echo -e "${GREEN}✓${NC} Backend Build abgeschlossen"
echo ""

# ============================================
# STEP 6: Container neu starten
# ============================================
echo -e "${YELLOW}[6/6]${NC} Starte Container neu..."
docker-compose up -d
echo -e "${GREEN}✓${NC} Container neu gestartet"
echo ""

# ============================================
# Fertig!
# ============================================
echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}✅ Update erfolgreich abgeschlossen!${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""
echo "📦 Backups:"
echo "   • Datenbank: $BACKUP_DIR/db_backup_$TIMESTAMP.sql"
if [ -d "$BACKUP_DIR/storage_$TIMESTAMP" ]; then
    echo "   • Storage:   $BACKUP_DIR/storage_$TIMESTAMP"
fi
echo ""
echo "🌐 Services:"
echo "   • Frontend:    http://localhost:3000"
echo "   • Backend:     http://localhost:8000"
echo "   • Grafana:     http://localhost:3001"
echo "   • Prometheus:  http://localhost:9090"
echo "   • MinIO:       http://localhost:9011"
echo ""

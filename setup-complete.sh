#!/bin/bash
# Complete CDN Setup Automation

set -e  # Exit on error

echo "🚀 CDN Complete Setup Starting..."
echo ""

# 1. Environment Check
if [ ! -f ".env" ]; then
    echo "❌ .env file missing!"
    exit 1
fi

source .env

# 2. Start all services
echo "📦 Starting all services..."
docker-compose up -d
sleep 10

# 3. Wait for MinIO
echo "⏳ Waiting for MinIO..."
until docker-compose exec -T origin-storage curl -s http://localhost:9000/minio/health/live > /dev/null 2>&1; do
    echo "   Waiting for MinIO to be ready..."
    sleep 2
done
echo "✅ MinIO ready"

# 4. Create bucket and set public policy
echo "📂 Setting up MinIO bucket..."
docker-compose exec -T origin-storage sh -c '
/usr/bin/mc alias set myminio http://localhost:9000 $MINIO_ROOT_USER $MINIO_ROOT_PASSWORD 2>/dev/null || true
/usr/bin/mc mb myminio/media 2>/dev/null || echo "Bucket already exists"
/usr/bin/mc anonymous set download myminio/media
echo "✅ Bucket media is now public"
'

# 5. Wait for Backend
echo "⏳ Waiting for Backend API..."
until curl -s http://localhost:8000/health > /dev/null 2>&1; do
    echo "   Waiting for Backend..."
    sleep 2
done
echo "✅ Backend ready"

# 6. Initialize Database
echo "💾 Initializing database..."
docker-compose exec -T backend-api python init_db.py 2>/dev/null || echo "Database already initialized"

# 7. Create Admin User (if not exists)
echo "👤 Creating admin user..."
docker-compose exec -T backend-api python -c "
from database import SessionLocal
from models import User
from passlib.context import CryptContext
import sys

pwd_context = CryptContext(schemes=['bcrypt'], deprecated='auto')
db = SessionLocal()

# Check if admin exists
existing = db.query(User).filter(User.username == 'admin').first()
if existing:
    print('✅ Admin user already exists')
    sys.exit(0)

# Create admin
admin = User(
    username='admin',
    email='admin@${CDN_DOMAIN}',
    hashed_password=pwd_context.hash('admin123'),
    is_admin=True,
    is_active=True
)
db.add(admin)
db.commit()
print('✅ Admin user created (username: admin, password: admin123)')
" || echo "Admin setup completed"

# 8. SSL Setup (if production)
if [ "$LETSENCRYPT_STAGING" = "false" ] && [ ! -f "nginx/conf.d/cdn-ssl.conf" ]; then
    echo "🔒 Setting up SSL..."
    
    # Wait for certificate
    echo "   Waiting for SSL certificate..."
    for i in {1..60}; do
        if docker-compose exec -T certbot test -f /etc/letsencrypt/live/$CDN_DOMAIN/fullchain.pem; then
            echo "✅ Certificate found"
            break
        fi
        sleep 2
    done
    
    # Activate SSL
    if docker-compose exec -T certbot test -f /etc/letsencrypt/live/$CDN_DOMAIN/fullchain.pem; then
        sed "s/YOUR_DOMAIN_HERE/$CDN_DOMAIN/g" nginx/conf.d/cdn-ssl.conf.template > nginx/conf.d/cdn-ssl.conf
        docker-compose restart nginx-cdn backend-api
        echo "✅ SSL activated"
    fi
fi

# 9. Restart services to ensure everything is connected
echo "🔄 Final restart..."
docker-compose restart nginx-cdn backend-api
sleep 5

# 10. Status Check
echo ""
echo "==================== CDN SETUP COMPLETE ===================="
echo ""
echo "📊 Service Status:"
docker-compose ps | grep -E "cdn-backend|cdn-edge|cdn-origin|cdn-frontend"
echo ""
echo "🌐 Access URLs:"
echo "   Frontend:    https://$CDN_DOMAIN/"
echo "   Admin Login: https://$CDN_DOMAIN/login"
echo "   API:         https://$CDN_DOMAIN/api/"
echo "   Grafana:     https://$CDN_DOMAIN/grafana/"
echo "   Prometheus:  https://$CDN_DOMAIN/prometheus/"
echo "   MinIO:       http://$(hostname -I | awk '{print $1}'):9011"
echo ""
echo "🔑 Default Credentials:"
echo "   Admin UI:    username: admin, password: admin123"
echo "   Grafana:     username: admin, password: admin"
echo "   MinIO:       username: admin, password: adminpassword123"
echo ""
echo "✅ CDN is ready to use!"
echo "==========================================================="

"""
Settings API - Manage system settings
"""
from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from pydantic import BaseModel, validator
import re
import subprocess
import os
from pathlib import Path
from database import get_db
from auth import get_current_user
from models import User, SystemSetting

router = APIRouter(prefix="/settings", tags=["settings"])


# Helper function to check if user is admin
def require_admin(user: User):
    if user.role != "admin":
        raise HTTPException(403, "Admin access required")
    return user


class MonitoringDomainsModel(BaseModel):
    grafana_domain: str | None = None
    prometheus_domain: str | None = None
    minio_domain: str | None = None

    @validator('grafana_domain', 'prometheus_domain', 'minio_domain')
    def validate_domain(cls, v):
        if v and v.strip():
            # Simple domain validation
            domain_pattern = r'^([a-z0-9]+(-[a-z0-9]+)*\.)+[a-z]{2,}$'
            if not re.match(domain_pattern, v.lower()):
                raise ValueError('Invalid domain format')
        return v.lower().strip() if v else None


@router.get("/monitoring-domains")
async def get_monitoring_domains(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get current monitoring domain settings"""
    require_admin(current_user)
    grafana_domain = db.query(SystemSetting).filter_by(key="grafana_domain").first()
    prometheus_domain = db.query(SystemSetting).filter_by(key="prometheus_domain").first()
    minio_domain = db.query(SystemSetting).filter_by(key="minio_domain").first()

    return {
        "grafana_domain": grafana_domain.value if grafana_domain else None,
        "prometheus_domain": prometheus_domain.value if prometheus_domain else None,
        "minio_domain": minio_domain.value if minio_domain else None
    }


@router.post("/monitoring-domains")
async def update_monitoring_domains(
    domains: MonitoringDomainsModel,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Update monitoring domain settings"""
    require_admin(current_user)
    
    # Update Grafana domain
    grafana_setting = db.query(SystemSetting).filter_by(key="grafana_domain").first()
    if grafana_setting:
        grafana_setting.value = domains.grafana_domain
    elif domains.grafana_domain:
        db.add(SystemSetting(key="grafana_domain", value=domains.grafana_domain))
    
    # Update Prometheus domain
    prometheus_setting = db.query(SystemSetting).filter_by(key="prometheus_domain").first()
    if prometheus_setting:
        prometheus_setting.value = domains.prometheus_domain
    elif domains.prometheus_domain:
        db.add(SystemSetting(key="prometheus_domain", value=domains.prometheus_domain))
    
    # Update MinIO domain
    minio_setting = db.query(SystemSetting).filter_by(key="minio_domain").first()
    if minio_setting:
        minio_setting.value = domains.minio_domain
    elif domains.minio_domain:
        db.add(SystemSetting(key="minio_domain", value=domains.minio_domain))
    
    db.commit()
    
    return {
        "message": "Monitoring domains updated successfully",
        "grafana_domain": domains.grafana_domain,
        "prometheus_domain": domains.prometheus_domain,
        "minio_domain": domains.minio_domain
    }


@router.post("/setup-monitoring-ssl")
async def setup_monitoring_ssl(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Setup SSL certificates and NGINX configs for monitoring domains"""
    require_admin(current_user)
    
    # Get configured domains
    grafana_domain = db.query(SystemSetting).filter_by(key="grafana_domain").first()
    prometheus_domain = db.query(SystemSetting).filter_by(key="prometheus_domain").first()
    minio_domain = db.query(SystemSetting).filter_by(key="minio_domain").first()
    
    domains_to_setup = []
    if grafana_domain and grafana_domain.value:
        domains_to_setup.append(("grafana", grafana_domain.value, "3000"))
    if prometheus_domain and prometheus_domain.value:
        domains_to_setup.append(("prometheus", prometheus_domain.value, "9090"))
    if minio_domain and minio_domain.value:
        domains_to_setup.append(("minio", minio_domain.value, "9001"))
    
    if not domains_to_setup:
        raise HTTPException(400, "No domains configured")
    
    results = []
    nginx_conf_dir = Path("/etc/nginx/conf.d")
    
    for service_name, domain, port in domains_to_setup:
        # Generate NGINX config
        nginx_config = f"""# {service_name.upper()} - {domain}
server {{
    listen 80;
    server_name {domain};
    
    # Let's Encrypt ACME Challenge
    location /.well-known/acme-challenge/ {{
        root /var/www/certbot;
        allow all;
    }}
    
    # Redirect to HTTPS
    location / {{
        return 301 https://$host$request_uri;
    }}
}}

server {{
    listen 443 ssl http2;
    server_name {domain};
    
    ssl_certificate /etc/letsencrypt/live/{domain}/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/{domain}/privkey.pem;
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers HIGH:!aNULL:!MD5;
    
    location / {{
        proxy_pass http://{service_name}:{port};
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        # WebSocket Support
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
    }}
}}
"""
        
        # Write NGINX config
        config_path = nginx_conf_dir / f"{service_name}-ssl.conf"
        try:
            with open(config_path, "w") as f:
                f.write(nginx_config)
            
            # Request SSL certificate via Certbot
            certbot_cmd = [
                "certbot", "certonly",
                "--webroot", "-w", "/var/www/certbot",
                "-d", domain,
                "--non-interactive",
                "--agree-tos",
                "--email", os.getenv("LETSENCRYPT_EMAIL", "admin@example.com"),
                "--no-eff-email"
            ]
            
            result = subprocess.run(certbot_cmd, capture_output=True, text=True)
            
            if result.returncode == 0:
                results.append({
                    "service": service_name,
                    "domain": domain,
                    "status": "success",
                    "message": "SSL certificate obtained"
                })
            else:
                results.append({
                    "service": service_name,
                    "domain": domain,
                    "status": "error",
                    "message": f"Certbot failed: {result.stderr}"
                })
        
        except Exception as e:
            results.append({
                "service": service_name,
                "domain": domain,
                "status": "error",
                "message": str(e)
            })
    
    # Reload NGINX
    try:
        subprocess.run(["nginx", "-s", "reload"], check=True)
    except subprocess.CalledProcessError as e:
        raise HTTPException(500, f"Failed to reload NGINX: {str(e)}")
    
    return {
        "message": "SSL setup completed",
        "results": results
    }

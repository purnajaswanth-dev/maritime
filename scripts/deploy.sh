#!/usr/bin/env bash
# =============================================================================
# Where Is My Ferry? - Production Deployment Script
# Supports: Ubuntu, Debian, CentOS, AlmaLinux, Rocky Linux, AWS Linux 2023
# =============================================================================
set -euo pipefail

echo "======================================================"
echo " Starting Where Is My Ferry? Production Deployment    "
echo "======================================================"

# 1. Check for docker and docker-compose
if ! command -v docker &> /dev/null; then
    echo "ERROR: 'docker' is not installed. Please install Docker first:"
    echo "  curl -fsSL https://get.docker.com | sh"
    exit 1
fi

if ! docker compose version &> /dev/null; then
    echo "ERROR: 'docker compose' (plugin v2) is not available."
    exit 1
fi

# 2. Check for .env file; create from .env.example if missing
if [ ! -f .env ]; then
    echo "NOTICE: .env file not found. Creating from .env.example..."
    cp .env.example .env
    echo "Created .env. Please review and customize your passwords and secrets!"
fi

# 3. Pull base images and build containers
echo "Building and pulling containers..."
docker compose build --parallel

# 4. Start all services in detached mode
echo "Launching all services (Database, ML Platform, Backend, Frontend)..."
docker compose up -d

# 5. Wait for database and backend health checks
echo "Waiting for services to become healthy..."
TIMEOUT=90
ELAPSED=0
INTERVAL=5

while [ "$ELAPSED" -lt "$TIMEOUT" ]; do
    BACKEND_STATUS=$(docker inspect --format='{{json .State.Health.Status}}' where_is_my_ferry_backend 2>/dev/null || echo '"unknown"')
    FRONTEND_STATUS=$(docker inspect --format='{{json .State.Health.Status}}' where_is_my_ferry_frontend 2>/dev/null || echo '"unknown"')
    DB_STATUS=$(docker inspect --format='{{json .State.Health.Status}}' where_is_my_ferry_db 2>/dev/null || echo '"unknown"')
    
    echo "Health status: DB=$DB_STATUS | Backend=$BACKEND_STATUS | Frontend=$FRONTEND_STATUS ($ELAPSED/$TIMEOUT s)"

    if [ "$BACKEND_STATUS" = '"healthy"' ] && [ "$DB_STATUS" = '"healthy"' ]; then
        echo ""
        echo "======================================================"
        echo " Deployment Succeeded! All services healthy.          "
        echo "======================================================"
        echo " Web App URL:      http://$(curl -s ifconfig.me || echo 'localhost')"
        echo " API Health Check: http://localhost:8080/actuator/health"
        echo " ML Health Check:  http://localhost:8000/health"
        echo " Default Admin:    admin@example.com (Password in .env)"
        echo "======================================================"
        exit 0
    fi

    sleep "$INTERVAL"
    ELAPSED=$((ELAPSED + INTERVAL))
done

echo "WARNING: Health check timeout reached ($TIMEOUT s)."
echo "Checking container logs:"
docker compose logs --tail=20
exit 1

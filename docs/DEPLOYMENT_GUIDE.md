# Where Is My Ferry? - Complete Production Deployment Guide

This guide provides step-by-step instructions to deploy **Where Is My Ferry?** to any cloud server or hosting provider using Docker and Docker Compose.

---

## 1. System Architecture

The entire stack runs in four containerized services interconnected via a private Docker bridge network:

```
[ Internet / Browser ]
         │
         ▼ (Port 80 / 443)
┌─────────────────────────────────────────────────────────────┐
│ 1. Frontend Ingress (where_is_my_ferry_frontend)            │
│    - Nginx 1.25 Alpine                                      │
│    - React 19 + TypeScript (Vite bundle)                    │
│    - Real-time OpenStreetMap / Leaflet tiles                 │
│    - Full SSE reverse proxy for live telemetry              │
└──────────────┬──────────────────────────────────────────────┘
               │ (Internal proxy: /api/ -> backend:8080)
┌──────────────▼──────────────────────────────────────────────┐
│ 2. Backend API Gateway (where_is_my_ferry_backend)           │
│    - Spring Boot 3.3.4 (Java 17 Eclipse Temurin)            │
│    - Flyway schema migrations (V1, V2, V3 automatic)        │
│    - JWT access & refresh token authentication               │
│    - SSE /api/v1/stream/vessels broadcaster                 │
└──────────────┬───────────────────────────────┬──────────────┘
               │                               │
               ▼                               ▼
┌───────────────────────────────┐ ┌───────────────────────────┐
│ 3. Database                   │ │ 4. ML Engine & Simulation │
│    (where_is_my_ferry_db)     │ │    (where_is_my_ferry_ml) │
│    - PostgreSQL 16 Alpine     │ │    - Python 3.11 Slim     │
│    - Persistent Docker volume │ │    - FastAPI AIS Daemon   │
│    - Port 5432                │ │    - Ridge Regression ETA │
└───────────────────────────────┘ └───────────────────────────┘
```

---

## 2. Server Requirements

| Resource | Minimum | Recommended (Production) |
|---|---|---|
| **CPU** | 2 vCPUs | 2 to 4 vCPUs |
| **RAM** | 2 GB (with swap) | 4 GB |
| **Disk** | 15 GB SSD | 30 GB SSD |
| **OS** | Ubuntu 22.04 / 24.04 LTS, Debian 12, Rocky Linux 9, Amazon Linux 2023 | Ubuntu 24.04 LTS |

---

## 3. Option A: Deployment on Any Cloud VPS (AWS EC2, DigitalOcean, Hetzner, Linode)

This is the standard, reliable production approach.

### Step 1: Connect to your server
```bash
ssh root@<YOUR_SERVER_IP>
# or on AWS:
ssh -i key.pem ubuntu@<YOUR_EC2_PUBLIC_IP>
```

### Step 2: Install Docker and Docker Compose
Run the official automated Docker installation script:
```bash
# Update packages
sudo apt update && sudo apt upgrade -y

# Install Docker engine and compose plugin
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh

# Verify installations
docker --version
docker compose version
```

### Step 3: Clone the Repository
```bash
git clone https://github.com/purnajaswanth-dev/maritime.git where-is-my-ferry
cd where-is-my-ferry
```

### Step 4: Configure Production Environment Variables
Copy `.env.example` to `.env`:
```bash
cp .env.example .env
nano .env
```

Set secure values for your production instance:
```ini
# PostgreSQL credentials
POSTGRES_DB=where_is_my_ferry
POSTGRES_USER=ferry_user
POSTGRES_PASSWORD=generate_a_strong_password_here
POSTGRES_PORT=5432

# Spring Boot & JWT
SPRING_PROFILES_ACTIVE=prod
APP_JWT_SECRET=generate_at_least_32_random_characters_secret_here!
APP_CORS_ALLOWED_ORIGINS=http://<YOUR_DOMAIN_OR_SERVER_IP>,http://localhost

# Admin seed login (used to log into /admin)
APP_ADMIN_SEED_EMAIL=admin@yourdomain.com
APP_ADMIN_SEED_PASSWORD=ChooseStrongAdminPassword!

# Ingress port
PORT=80
```

### Step 5: Build and Launch Containers
You can run the automated deployment script:
```bash
chmod +x scripts/deploy.sh
./scripts/deploy.sh
```

Or run Docker Compose manually:
```bash
# Build and start all 4 services in detached mode
docker compose up -d --build
```

### Step 6: Verify Deployment
Check the status of running containers:
```bash
docker compose ps
```
Output should show all services healthy:
```
NAME                       IMAGE                              STATUS
where_is_my_ferry_db       postgres:16-alpine                 Up (healthy)
where_is_my_ferry_ml       where-is-my-ferry-ml-platform      Up (healthy)
where_is_my_ferry_backend  where-is-my-ferry-backend          Up (healthy)
where_is_my_ferry_frontend where-is-my-ferry-frontend         Up (healthy)
```

Test endpoints:
```bash
# Frontend
curl -I http://localhost/

# Backend Health
curl http://localhost:8080/actuator/health

# ML Engine Health
curl http://localhost:8000/health
```

Now open `http://<YOUR_SERVER_IP>` in your browser to view the live app!

---

## 4. Option B: AWS EC2 Quick-Deploy

1. **Launch EC2 Instance:**
   - AMI: Ubuntu Server 24.04 LTS (x86_64)
   - Instance Type: `t3.medium` (2 vCPU, 4 GiB Memory)
   - Storage: 30 GiB gp3
   - Security Group Rules:
     - Allow **SSH (22)** from your IP
     - Allow **HTTP (80)** from `0.0.0.0/0`
     - Allow **HTTPS (443)** from `0.0.0.0/0`
     - *(Optional)* Allow **Port 8080** (restricted to your IP for direct API diagnostics)
2. **SSH into the instance:**
   ```bash
   ssh -i your-key.pem ubuntu@<EC2-PUBLIC-IP>
   ```
3. Run the commands in **Section 3** above.

---

## 5. Option C: DigitalOcean Droplet

1. Create a Droplet:
   - Image: **Ubuntu 24.04 LTS** (or choose Marketplace -> **Docker on Ubuntu**)
   - Plan: **Basic Droplet** with 2 vCPUs, 4GB RAM ($24/mo) or 2GB RAM ($12/mo + 2GB swap)
   - Region: Closest to your users (e.g. Frankfurt / London / Paris for European maritime routes)
2. Follow **Section 3** above to clone and launch.

---

## 6. Configuring Free SSL / HTTPS (Let's Encrypt & Certbot)

For a production domain (e.g. `ferry.yourdomain.com`):

### Method 1: Using Certbot & Nginx on Host Server
1. Point your domain DNS A Record to `<YOUR_SERVER_IP>`.
2. Change the host port in `docker-compose.yml` for frontend:
   ```yaml
   frontend:
     ports:
       - "127.0.0.1:8088:80"
   ```
3. Install Nginx and Certbot on the host:
   ```bash
   sudo apt install -y nginx certbot python3-certbot-nginx
   ```
4. Configure host Nginx site `/etc/nginx/sites-available/ferry.conf`:
   ```nginx
   server {
       server_name ferry.yourdomain.com;

       location / {
           proxy_pass http://127.0.0.1:8088;
           proxy_set_header Host $host;
           proxy_set_header X-Real-IP $remote_addr;
           proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
           proxy_set_header X-Forwarded-Proto $scheme;

           # SSE streaming
           proxy_http_version 1.1;
           proxy_set_header Connection '';
           proxy_buffering off;
           proxy_cache off;
           chunked_transfer_encoding off;
           proxy_read_timeout 24h;
       }
   }
   ```
5. Enable site and request SSL certificate:
   ```bash
   sudo ln -s /etc/nginx/sites-available/ferry.conf /etc/nginx/sites-enabled/
   sudo nginx -t
   sudo systemctl reload nginx
   sudo certbot --nginx -d ferry.yourdomain.com
   ```

### Method 2: Cloudflare Proxy (Easiest)
1. In Cloudflare DNS, set your subdomain A record to `<YOUR_SERVER_IP>`.
2. Turn ON the **Orange Cloud (Proxied)**.
3. In Cloudflare SSL/TLS tab, select **Flexible** or **Full**.
4. Cloudflare automatically handles HTTPS encryption, DDoS protection, and global CDN caching.

---

## 7. Useful Operational Commands

### View Logs in Real Time
```bash
# All services
docker compose logs -f

# Specific service
docker compose logs -f backend
docker compose logs -f frontend
docker compose logs -f ml-platform
```

### Restart Stack
```bash
# Graceful restart
docker compose restart

# Stop all services
docker compose down

# Start up
docker compose up -d
```

### Pull Updates & Re-deploy (CI/CD / Manual)
```bash
git pull origin main
docker compose build
docker compose up -d
```

### Database Backup & Restore
```bash
# Backup PostgreSQL database to a file
docker exec -t where_is_my_ferry_db pg_dump -U ferry_user where_is_my_ferry > backup_$(date +%Y%m%d_%H%M%S).sql

# Restore from backup file
docker exec -i where_is_my_ferry_db psql -U ferry_user -d where_is_my_ferry < backup_20261025.sql
```

---

## 8. Summary of Ports & Access URLs

| Component | Container Port | Host Port | Production Access URL |
|---|---|---|---|
| **Frontend Web App** | 80 | 80, 5173 | `http://<SERVER_IP>/` or `https://<YOUR_DOMAIN>/` |
| **API Gateway** | 8080 | 8080 | `http://<SERVER_IP>/api/` (proxied) or `http://<SERVER_IP>:8080/` |
| **API Documentation** | 8080 | 8080 | `http://<SERVER_IP>:8080/swagger-ui.html` |
| **Spring Actuator** | 8080 | 8080 | `http://<SERVER_IP>:8080/actuator/health` |
| **ML Engine Health** | 8000 | 8000 | `http://<SERVER_IP>:8000/health` |
| **PostgreSQL DB** | 5432 | 5432 | `localhost:5432` (internal or secured via firewall) |

# Deploying Where Is My Ferry? to Render

This guide outlines how to deploy the full **Where Is My Ferry?** stack on [Render](https://render.com) using the included `render.yaml` Blueprint or manual web dashboard configuration.

---

## Architecture on Render

```
[ Internet User ] ── HTTPS ──▶ [ where-is-my-ferry-frontend ] (Render Static Site: FREE)
                                            │
                                            ▼ (REST & SSE: /api/v1/...)
                               [ where-is-my-ferry-backend ] (Render Web Service: Docker)
                                   │                   │
                                   ▼                   ▼
     [ where-is-my-ferry-db ] (Postgres)     [ where-is-my-ferry-ml ] (Private Service)
```

---

## Method 1: 1-Click Blueprint Deployment (Recommended)

Render Blueprints automatically parse `render.yaml` in your repository and set up the database, backend, ML daemon, and frontend with all environment variables pre-linked.

### Step 1: Push your code to GitHub
Make sure your changes are pushed to your GitHub repository:
```bash
git push origin main
```

### Step 2: Create a Blueprint on Render
1. Log in to [dashboard.render.com](https://dashboard.render.com).
2. Click **New +** in the top navigation bar and select **Blueprint**.
3. Connect your GitHub repository (`purnajaswanth-dev/maritime`).
4. Give your Blueprint a name (e.g. `where-is-my-ferry`).
5. Render will automatically detect `render.yaml` and display the 4 components:
   - **Database:** `where-is-my-ferry-db` (PostgreSQL)
   - **Private Service:** `where-is-my-ferry-ml` (Python simulation)
   - **Web Service:** `where-is-my-ferry-backend` (Spring Boot API)
   - **Static Site:** `where-is-my-ferry-frontend` (React + Vite)
6. Click **Apply**.
7. Render will provision the database, build the Docker images, run the database migrations, and deploy the frontend.

---

## Method 2: Manual UI Deployment (Free-Tier Friendly)

If you prefer deploying services individually or using Render's 100% Free Tier:

### 1. Create the PostgreSQL Database
1. Go to **Dashboard** -> **New +** -> **PostgreSQL**.
2. **Name:** `where-is-my-ferry-db`
3. **Database:** `where_is_my_ferry`
4. **User:** `ferry_user`
5. **Region:** `Frankfurt (EU Central)` *(closest to Brittany / France)*
6. **Plan:** `Free` (or use a free forever database from [Neon.tech](https://neon.tech))
7. Click **Create Database**.
8. Copy the **Internal Database URL** (e.g. `postgres://ferry_user:...@dpg-...:5432/where_is_my_ferry`).

### 2. Deploy Python ML Simulation (Docker Web / Private Service)
1. **New +** -> **Private Service** (or Web Service).
2. Connect your GitHub repo.
3. **Name:** `where-is-my-ferry-ml`
4. **Environment:** `Docker`
5. **Docker Command / Context:**
   - Dockerfile Path: `./ml-platform/Dockerfile`
   - Docker Context: `./ml-platform`
6. **Environment Variables:**
   - `PORT`: `8000`
   - `ALLOW_CONTAINER_BIND`: `1`
   - `PYTHONUNBUFFERED`: `1`
7. Click **Create Service**.

### 3. Deploy Spring Boot Backend (Docker Web Service)
1. **New +** -> **Web Service**.
2. Connect your GitHub repo.
3. **Name:** `where-is-my-ferry-backend`
4. **Environment:** `Docker`
5. **Docker Command / Context:**
   - Dockerfile Path: `./backend/Dockerfile`
   - Docker Context: `./backend`
6. **Health Check Path:** `/actuator/health`
7. **Environment Variables:**
   - `SPRING_PROFILES_ACTIVE`: `prod`
   - `DATABASE_URL`: Paste the Internal Database URL from Step 1 *(Spring Boot automatically adapts this to JDBC!)*
   - `APP_JWT_SECRET`: `whereismyferrysupersecretkeyforjwttokengenerationshouldbeatleast256bitslong!`
   - `SIMULATION_DAEMON_URL`: `http://where-is-my-ferry-ml:8000`
   - `APP_CORS_ALLOWED_ORIGINS`: `*`
   - `APP_ADMIN_SEED_EMAIL`: `admin@example.com`
   - `APP_ADMIN_SEED_PASSWORD`: `Admin@PennArBed2026`
8. Click **Create Web Service**.
9. Once deployed, copy your backend URL: `https://where-is-my-ferry-backend.onrender.com`.

### 4. Deploy React Frontend (Static Site - 100% Free)
1. **New +** -> **Static Site**.
2. Connect your GitHub repo.
3. **Name:** `where-is-my-ferry-frontend`
4. **Root Directory:** `frontend`
5. **Build Command:** `npm install && npm run build`
6. **Publish Directory:** `dist`
7. Under **Redirects/Rewrites**:
   - **Type:** `Rewrite`
   - **Source:** `/*`
   - **Destination:** `/index.html`
8. Under **Environment Variables**:
   - `VITE_API_BASE_URL`: `https://where-is-my-ferry-backend.onrender.com`
9. Click **Create Static Site**.

---

## Built-In Render Compatibility Features

The codebase includes built-in handlers for Render's architecture:

1. **Dynamic Port Adaptation:**
   - Spring Boot dynamically binds to `${PORT}` (which Render sets to `10000`).
2. **Automatic JDBC Translation:**
   - `DatabasePlaceholderValidator` intercepts Render's `DATABASE_URL` (`postgres://...`) and converts it to a standard HikariCP JDBC string (`jdbc:postgresql://...`) with parsed credentials on the fly.
3. **Cross-Origin SSE Telemetry:**
   - `useVesselStream` dynamically uses `VITE_API_BASE_URL` to establish live EventSource connections across different Render service URLs.
4. **SPA Client Routing:**
   - Rewrites in `render.yaml` route all deep URLs (e.g. `/track`, `/timetable`, `/admin`) to `/index.html` preventing 404s.

---

## Verification Checklist

- [ ] Backend Actuator: `https://<backend-name>.onrender.com/actuator/health` returns `{"status":"UP"}`
- [ ] Swagger API Docs: `https://<backend-name>.onrender.com/swagger-ui.html`
- [ ] Frontend: `https://<frontend-name>.onrender.com/` loads clean OpenStreetMap tiles with zero watermark
- [ ] Live Telemetry: Vessel marker moves along the Iroise Sea corridor and SSE indicator displays `Live`
- [ ] Admin Portal: Login with `admin@example.com` / `Admin@PennArBed2026` at `/admin`

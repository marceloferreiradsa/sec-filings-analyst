# Deployment Guide

This document covers deploying the SEC Filings Analyst to a Linux VPS
alongside an existing site, using Docker for isolation and nginx as the
reverse proxy.

---

## Architecture

```
Internet
    │
    ▼
nginx (host — port 80/443)
    ├── yourdomain.com ──────────► main site (unchanged)
    └── rag.yourdomain.com ──────► Docker container (127.0.0.1:8501)
```

The container binds to `127.0.0.1:8501` (localhost only). It is not
accessible directly from the internet — all traffic goes through nginx.
Your main site is completely unaffected.

---

## Workflow overview

Build and test the image locally. Ship the tested artifact to the VPS.
The VPS only runs the image — it never builds anything.

```
Local machine                          VPS
─────────────────────────────          ─────────────────────
docker build (includes data)           docker load / docker pull
docker run → test at localhost  ──►    docker compose up -d
docker save or docker push             nginx routes traffic in
```

This guarantees what runs in production is identical to what you tested.

---

## Step 1 — Build the image locally

From your project folder with the data files present:

```bash
docker build -t sec-filings-analyst:latest .
```

The image includes:
- Python runtime + dependencies (~200MB)
- app.py, retrieve.py, qa.py
- data/index/index.faiss + data/processed/chunks.json (~48MB)

It does NOT include the API key (passed at runtime) or pipeline scripts.

---

## Step 2 — Test locally before shipping

```powershell
# Windows PowerShell
docker run --rm `
    -e OPENAI_API_KEY=$env:OPENAI_API_KEY `
    -p 8501:8501 `
    sec-filings-analyst:latest
```

Open `http://localhost:8501` and run a few queries. Confirm the answers
are correct and citations appear. Only ship after this passes.

Stop the test container with Ctrl+C (--rm removes it automatically).

---

## Step 3 — Ship the image to the VPS

### Option A — tar file (no registry needed)

```bash
# Local: export
docker save sec-filings-analyst:latest | gzip > sec-analyst.tar.gz

# Transfer (~400MB — takes 2–5 minutes on a typical connection)
scp sec-analyst.tar.gz user@your-vps:~/

# VPS: load
docker load < sec-analyst.tar.gz

# Clean up the tar file locally and on the VPS after loading
rm sec-analyst.tar.gz
ssh user@your-vps "rm ~/sec-analyst.tar.gz"
```

### Option B — GitHub Container Registry (recommended for updates)

Since your project is on GitHub, ghcr.io is free for public repos and
enables version tagging for rollbacks.

```bash
# Local: tag for the registry
docker tag sec-filings-analyst:latest     ghcr.io/YOUR_USERNAME/sec-filings-analyst:latest

# Authenticate (use a GitHub Personal Access Token with write:packages scope)
echo $env:GITHUB_TOKEN | docker login ghcr.io -u YOUR_USERNAME --password-stdin

# Push
docker push ghcr.io/YOUR_USERNAME/sec-filings-analyst:latest

# VPS: pull
docker pull ghcr.io/YOUR_USERNAME/sec-filings-analyst:latest
```

Version tagging for rollbacks:
```bash
# Tag with a version before pushing
docker tag sec-filings-analyst:latest     ghcr.io/YOUR_USERNAME/sec-filings-analyst:v1.0

# Roll back on the VPS if needed
docker compose down
# Edit docker-compose.yml: change image tag to v1.0
docker compose up -d
```

---

## Step 4 — Configure docker-compose.yml on the VPS

The `docker-compose.yml` in the repo has `build: .` for local development.
On the VPS, use a version that only runs the pre-built image. Create
`/path/to/app/docker-compose.yml` on the VPS with this content:

```yaml
services:
  sec-analyst:
    image: sec-filings-analyst:latest   # or ghcr.io/YOUR_USERNAME/... if using registry
    container_name: sec-analyst
    ports:
      - "127.0.0.1:8501:8501"
    environment:
      - OPENAI_API_KEY=${OPENAI_API_KEY}
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8501/_stcore/health"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 15s
```

Set the API key on the VPS (never in a file):
```bash
export OPENAI_API_KEY=sk-your-key-here
# Add to ~/.bashrc for persistence across reboots
```

Start the container:
```bash
docker compose up -d
docker compose ps        # verify it is running
docker compose logs -f   # stream logs
```

---

## Step 5 — Configure nginx

Add a server block for the subdomain.
Create `/etc/nginx/sites-available/sec-analyst`:

```nginx
server {
    listen 80;
    server_name rag.yourdomain.com;
    return 301 https://$host$request_uri;
}

server {
    listen 443 ssl;
    server_name rag.yourdomain.com;

    ssl_certificate     /etc/letsencrypt/live/rag.yourdomain.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/rag.yourdomain.com/privkey.pem;

    location / {
        proxy_pass http://127.0.0.1:8501;

        # Required for Streamlit WebSocket connections.
        # Without these the interface loads but disconnects after a few seconds.
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";

        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;

        # Generous timeout for LLM generation (can take 8–10 seconds)
        proxy_read_timeout 120s;
        proxy_send_timeout 120s;
    }
}
```

Enable and reload:
```bash
sudo ln -s /etc/nginx/sites-available/sec-analyst /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl reload nginx
```

---

## Step 6 — SSL certificate

```bash
sudo certbot --nginx -d rag.yourdomain.com
sudo certbot renew --dry-run    # verify auto-renewal works
```

---

## Updating the deployment

When you update code or rebuild the index locally:

```bash
# Local: rebuild and test
docker build -t sec-filings-analyst:latest .
docker run --rm -e OPENAI_API_KEY=$env:OPENAI_API_KEY -p 8501:8501 sec-filings-analyst:latest
# Test, then ship

# Ship (Option A)
docker save sec-filings-analyst:latest | gzip > sec-analyst.tar.gz
scp sec-analyst.tar.gz user@your-vps:~/

# VPS: load and restart
ssh user@your-vps
docker load < ~/sec-analyst.tar.gz
docker compose down && docker compose up -d
```

---

## WebSocket note

Streamlit uses WebSockets for real-time updates. The `Upgrade` and
`Connection` headers in the nginx config are not optional. Without them,
the page renders but disconnects after a few seconds with a
"Connection error." This is the most common nginx + Streamlit failure.

---

## Resource usage

The container uses approximately 200–400MB RAM (FAISS index loaded in
memory). On a 1GB VPS this is comfortable if it is the only service.
On a 512MB VPS monitor memory if other services are running.

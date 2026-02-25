# StockSense Docker Deployment (stocksense.thatinsaneguy.com)

Single deploy script for Ubuntu: destroys existing containers, rebuilds, obtains HTTPS certs via Let's Encrypt, and hosts both backend and frontend.

## Prerequisites

- **Ubuntu** with Docker and Docker Compose installed
- Domain **stocksense.thatinsaneguy.com** pointing to your server's IP (A record)
- Ports **80** and **443** open on the server

## Install Docker (if not installed)

`deploy.sh` **auto-installs Docker** when missing. Or install manually:

```bash
chmod +x install-docker.sh
./install-docker.sh
# Then run: newgrp docker   (or log out and back in)
```

*Note: Node, npm, nginx run inside Docker containers—no host install needed.*

## Quick Start

```bash
# 1. Clone/copy the project to your Ubuntu server

# 2. Create .env files from examples
cp backend/.env.example backend/.env
cp frontend/.env.example frontend/.env
# Edit backend/.env: DOMAIN, CERTBOT_EMAIL, Stripe keys, FRONTEND_URL
# Edit frontend/.env: VITE_FIREBASE_* (Firebase client keys)

# 3. Ensure firebase-config.json exists in backend/
# (Download from Firebase Console > Project Settings > Service Accounts)

# 4. Deploy (obtains HTTPS cert automatically on first run)
chmod +x deploy.sh
./deploy.sh
```

## What deploy.sh Does

1. Stops and removes any existing StockSense containers
2. **Obtains/renews HTTPS certificate** via Let's Encrypt Certbot (standalone on first run)
3. Rebuilds backend and frontend images from scratch
4. Starts the stack:
   - **Frontend** (nginx): ports 80 (→ HTTPS redirect) + 443 (HTTPS) → React app + proxies to backend
   - **Backend** (FastAPI): port 5000 (internal)

## HTTPS (Let's Encrypt)

- On **first run**, the script obtains a free certificate for your domain (DNS must point to the server).
- On **subsequent runs**, it renews the certificate if needed.
- Certificates are stored in `./certbot/` (gitignored).

## Firebase Setup

Add these to **Firebase Console → Authentication → Settings → Authorized domains**:

- `stocksense.thatinsaneguy.com`
- `www.stocksense.thatinsaneguy.com`

## Stripe Webhook

Set your Stripe webhook URL to:

- `https://stocksense.thatinsaneguy.com/webhook`

## Manual Commands

```bash
# View logs
docker compose logs -f

# Stop
docker compose down

# Restart
docker compose restart
```

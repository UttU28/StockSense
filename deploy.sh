#!/bin/bash
# StockSense deploy script for Ubuntu
# Auto-installs Docker if missing. Destroys existing containers, rebuilds,
# obtains HTTPS certs via Let's Encrypt, and starts fresh.
# Note: Node, npm, nginx run inside Docker containers - no host install needed.

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# --- Ensure Docker is installed (only if missing) ---
install_docker_if_needed() {
    if command -v docker >/dev/null 2>&1; then
        return 0
    fi
    echo "Docker not found. Installing Docker..."
    if ! command -v curl >/dev/null 2>&1; then
        echo "Installing curl..."
        sudo apt-get update -qq && sudo apt-get install -y curl
    fi
    curl -fsSL https://get.docker.com -o /tmp/get-docker.sh
    sudo sh /tmp/get-docker.sh
    rm -f /tmp/get-docker.sh
    sudo usermod -aG docker "$USER" 2>/dev/null || true
    echo "Docker installed. (You may need 'newgrp docker' or logout/login for non-sudo usage.)"
}

# Wrappers that use sg docker (avoids sudo, preserves env) or sudo
run_docker() {
    if docker info >/dev/null 2>&1; then
        docker "$@"
    elif sg docker -c "docker info" >/dev/null 2>&1; then
        sg docker -c "docker $(printf '%q ' "$@")"
    elif sudo docker info >/dev/null 2>&1; then
        sudo docker "$@"
    else
        return 1
    fi
}

run_compose() {
    # Always run from project dir (docker-compose needs it)
    cd "$SCRIPT_DIR"
    if docker info >/dev/null 2>&1; then
        docker compose "$@"
    elif sg docker -c "docker info" >/dev/null 2>&1; then
        sg docker -c "cd $(printf '%q' "$SCRIPT_DIR") && docker compose $(printf '%q ' "$@")"
    elif sudo docker info >/dev/null 2>&1; then
        sudo docker compose "$@"
    elif command -v docker-compose >/dev/null 2>&1; then
        sudo docker-compose "$@" 2>/dev/null || docker-compose "$@"
    else
        return 1
    fi
}

install_docker_if_needed

# Verify we can run docker
if ! docker info >/dev/null 2>&1 && ! sg docker -c "docker info" >/dev/null 2>&1 && ! sudo docker info >/dev/null 2>&1; then
    echo "Error: Could not run Docker. Try: newgrp docker  (then run ./deploy.sh again)"
    exit 1
fi

# Verify docker compose works
if ! (docker compose version >/dev/null 2>&1 || sg docker -c "docker compose version" >/dev/null 2>&1 || sudo docker compose version >/dev/null 2>&1 || command -v docker-compose >/dev/null 2>&1); then
    echo "Error: Docker Compose not found. Try: sudo apt-get install docker-compose-plugin"
    exit 1
fi

# --- Preflight: .env files ---
if [ ! -f backend/.env ]; then
    if [ -f backend/.env.example ]; then
        echo "Creating backend/.env from .env.example (edit with your values)."
        cp backend/.env.example backend/.env
    else
        echo "Error: backend/.env missing. Create it with DOMAIN, CERTBOT_EMAIL, Stripe keys."
        exit 1
    fi
fi
if [ ! -f frontend/.env ]; then
    if [ -f frontend/.env.example ]; then
        echo "Creating frontend/.env from .env.example (edit with Firebase/Stripe keys)."
        cp frontend/.env.example frontend/.env
    else
        echo "Error: frontend/.env missing. Create it with VITE_FIREBASE_* and Stripe keys."
        exit 1
    fi
fi

# --- Preflight: firebase-config.json ---
if [ ! -f backend/firebase-config.json ]; then
    echo "WARNING: backend/firebase-config.json not found."
    echo "Creating placeholder so deploy can proceed. Auth/Firestore will not work until you add the real file."
    echo "Download from: Firebase Console > Project Settings > Service Accounts > Generate new private key"
    echo ""
    printf '%s\n' '{"type":"service_account","project_id":"placeholder","private_key_id":"x","private_key":"","client_email":"","client_id":""}' > backend/firebase-config.json
fi

# Normalize line endings (fix CRLF from Windows editors)
sed -i 's/\r$//' backend/.env 2>/dev/null || true
[ -f frontend/.env ] && sed -i 's/\r$//' frontend/.env 2>/dev/null || true

# Load env from respective dirs (for DOMAIN, CERTBOT_EMAIL, VITE_* build args)
set -a
source backend/.env
[ -f frontend/.env ] && source frontend/.env
set +a

DOMAIN="${DOMAIN:-stocksense.thatinsaneguy.com}"
CERTBOT_EMAIL="${CERTBOT_EMAIL:-admin@stocksense.thatinsaneguy.com}"
CERT_DIR="./certbot/conf"
CERT_FULLCHAIN="$CERT_DIR/live/$DOMAIN/fullchain.pem"

echo "=== StockSense Deploy ==="

# Stop and remove existing containers
echo "Stopping and removing existing containers..."
run_compose down --remove-orphans -v 2>/dev/null || true

# Ensure certbot directories exist
mkdir -p certbot/conf certbot/www

# Obtain HTTPS certificate if missing
if [ ! -f "$CERT_FULLCHAIN" ]; then
    echo "Obtaining HTTPS certificate for $DOMAIN (Let's Encrypt)..."
    echo "  Ensure DNS for $DOMAIN points to this server and port 80 is reachable."
    if run_docker run --rm \
        -v "$(pwd)/certbot/conf:/etc/letsencrypt" \
        -v "$(pwd)/certbot/www:/var/www/certbot" \
        -p 80:80 \
        certbot/certbot certonly \
        --standalone \
        -d "$DOMAIN" \
        -d "www.$DOMAIN" \
        --non-interactive \
        --agree-tos \
        --email "$CERTBOT_EMAIL" 2>/dev/null; then
        echo "Certificate obtained (domain + www)."
    else
        echo "www.$DOMAIN has no DNS record. Obtaining cert for $DOMAIN only..."
        run_docker run --rm \
            -v "$(pwd)/certbot/conf:/etc/letsencrypt" \
            -v "$(pwd)/certbot/www:/var/www/certbot" \
            -p 80:80 \
            certbot/certbot certonly \
            --standalone \
            -d "$DOMAIN" \
            --non-interactive \
            --agree-tos \
            --email "$CERTBOT_EMAIL"
        echo "Certificate obtained."
    fi
else
    echo "HTTPS certificate exists. Renewing if needed..."
    run_docker run --rm \
        -v "$(pwd)/certbot/conf:/etc/letsencrypt" \
        -v "$(pwd)/certbot/www:/var/www/certbot" \
        -p 80:80 \
        certbot/certbot renew --standalone --quiet 2>/dev/null || true
fi

# Build and start
echo "Building images..."
run_compose build --no-cache

echo "Starting services..."
run_compose up -d

echo ""
echo "=== Deploy complete ==="
echo "HTTPS: https://$DOMAIN"
echo "Backend health: https://$DOMAIN/health"
echo ""
echo "View logs: docker compose logs -f"

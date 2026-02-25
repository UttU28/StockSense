#!/bin/bash
# StockSense deploy script for Ubuntu
# Destroys existing containers, rebuilds, obtains HTTPS certs, and starts fresh.

set -e

COMPOSE="docker compose"
command -v docker-compose >/dev/null 2>&1 && COMPOSE="docker-compose"

# Load env from respective dirs (for DOMAIN, CERTBOT_EMAIL, VITE_* build args)
[ -f backend/.env ] && set -a && source backend/.env && set +a
[ -f frontend/.env ] && set -a && source frontend/.env && set +a

DOMAIN="${DOMAIN:-stocksense.thatinsaneguy.com}"
CERTBOT_EMAIL="${CERTBOT_EMAIL:-admin@stocksense.thatinsaneguy.com}"
CERT_DIR="./certbot/conf"
CERT_FULLCHAIN="$CERT_DIR/live/$DOMAIN/fullchain.pem"

echo "=== StockSense Deploy ==="

# Stop and remove existing containers
echo "Stopping and removing existing containers..."
$COMPOSE down --remove-orphans -v 2>/dev/null || true

# Ensure certbot directories exist
mkdir -p certbot/conf certbot/www

# Obtain HTTPS certificate if missing
if [ ! -f "$CERT_FULLCHAIN" ]; then
    echo "Obtaining HTTPS certificate for $DOMAIN (Let's Encrypt)..."
    echo "  Ensure DNS for $DOMAIN points to this server and port 80 is reachable."
    docker run --rm \
        -v "$(pwd)/certbot/conf:/etc/letsencrypt" \
        -v "$(pwd)/certbot/www:/var/www/certbot" \
        -p 80:80 \
        certbot/certbot certonly \
        --standalone \
        -d "$DOMAIN" \
        -d "www.$DOMAIN" \
        --non-interactive \
        --agree-tos \
        --email "$CERTBOT_EMAIL"
    echo "Certificate obtained."
else
    echo "HTTPS certificate exists. Renewing if needed..."
    docker run --rm \
        -v "$(pwd)/certbot/conf:/etc/letsencrypt" \
        -v "$(pwd)/certbot/www:/var/www/certbot" \
        -p 80:80 \
        certbot/certbot renew --standalone --quiet 2>/dev/null || true
fi

# Build and start
echo "Building images..."
$COMPOSE build --no-cache

echo "Starting services..."
$COMPOSE up -d

echo ""
echo "=== Deploy complete ==="
echo "HTTPS: https://$DOMAIN"
echo "Backend health: https://$DOMAIN/health"
echo ""
echo "View logs: $COMPOSE logs -f"

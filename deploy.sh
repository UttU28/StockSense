#!/bin/bash
# Unified Deployment Script for Stock Gita
# Smart deployment - checks what's installed and skips unnecessary steps

set -e

DOMAIN="rakeshent.info"
EMAIL="admin@rakeshent.info"
APP_DIR="$HOME/StockSense"

echo "========================================"
echo "Stock Gita - Smart Deployment"
echo "Domain: $DOMAIN"
echo "========================================"

cd "$APP_DIR"

# Quick check: Server Setup (only if needed)
if ! command -v docker &> /dev/null; then
    echo "[Setup] Installing Docker and dependencies..."
    bash server_setup.sh
else
    echo "✅ Docker already installed (skipping setup)"
fi

# Stop existing containers
echo ""
echo "[1/4] Stopping existing containers..."
docker compose down || true

# Configure Nginx (only if config changed or missing)
echo ""
echo "[2/4] Configuring Nginx..."

# Check if SSL certificate exists to determine which config to use
SSL_EXISTS=false
if [ -d "/etc/letsencrypt/live/$DOMAIN" ]; then
    SSL_EXISTS=true
fi

# Use HTTP-only config if SSL doesn't exist, otherwise use SSL config
if [ "$SSL_EXISTS" = false ]; then
    if [ ! -f "nginx_rakeshent_http.conf" ]; then
        echo "❌ nginx_rakeshent_http.conf not found!"
        exit 1
    fi
    NGINX_CONFIG_FILE="nginx_rakeshent_http.conf"
    echo "Using HTTP-only configuration (SSL will be added by certbot)..."
else
    if [ ! -f "nginx_rakeshent.conf" ]; then
        echo "❌ nginx_rakeshent.conf not found!"
        exit 1
    fi
    NGINX_CONFIG_FILE="nginx_rakeshent.conf"
    echo "Using SSL configuration..."
fi

NGINX_CONFIG_EXISTS=false
if [ -f "/etc/nginx/sites-available/$DOMAIN" ]; then
    if ! sudo diff -q "$NGINX_CONFIG_FILE" /etc/nginx/sites-available/$DOMAIN > /dev/null 2>&1; then
        echo "Updating Nginx configuration..."
        sudo cp "$NGINX_CONFIG_FILE" /etc/nginx/sites-available/$DOMAIN
        NGINX_NEEDS_RELOAD=true
    else
        echo "✅ Nginx config unchanged (skipping copy)"
        NGINX_CONFIG_EXISTS=true
    fi
else
    echo "Creating Nginx configuration..."
    sudo cp "$NGINX_CONFIG_FILE" /etc/nginx/sites-available/$DOMAIN
    NGINX_NEEDS_RELOAD=true
fi

# Enable site if not already enabled
if [ ! -L "/etc/nginx/sites-enabled/$DOMAIN" ]; then
    sudo ln -sf /etc/nginx/sites-available/$DOMAIN /etc/nginx/sites-enabled/
    NGINX_NEEDS_RELOAD=true
fi

# Remove old configs if they exist
sudo rm -f /etc/nginx/sites-enabled/stocks.thatinsaneguy.com
sudo rm -f /etc/nginx/sites-enabled/default

# Test Nginx configuration
if sudo nginx -t > /dev/null 2>&1; then
    echo "✅ Nginx configuration valid"
else
    echo "❌ Nginx configuration error!"
    sudo nginx -t
    exit 1
fi

# Reload Nginx if config was updated (before SSL setup)
if [ "$NGINX_NEEDS_RELOAD" = true ]; then
    echo "Reloading Nginx..."
    sudo systemctl reload nginx
    echo "✅ Nginx reloaded"
fi

# SSL Certificate (only if missing)
echo ""
echo "[3/4] Checking SSL certificate..."
if [ ! -d "/etc/letsencrypt/live/$DOMAIN" ]; then
    echo "Obtaining SSL certificate from Let's Encrypt..."
    # Certbot will automatically modify the nginx config to add SSL and reload nginx
    sudo certbot --nginx -d $DOMAIN --non-interactive --agree-tos --email $EMAIL
    echo "✅ SSL certificate obtained and configured (nginx reloaded by certbot)"
else
    echo "✅ SSL certificate already exists (skipping)"
fi

# Start Docker containers
echo ""
echo "[4/4] Starting Docker containers..."
docker compose up -d --build

echo ""
echo "⏳ Waiting for services to start..."
sleep 10

# Quick status check
echo ""
echo "📊 Service Status:"
docker compose ps

echo ""
echo "========================================"
echo "✅ DEPLOYMENT COMPLETE!"
echo "========================================"
echo ""
echo "Your Stock Gita system is now live at:"
echo "🌐 https://$DOMAIN"
echo ""
echo "Services:"
echo "- Open WebUI (Public): https://$DOMAIN"
echo "- Stock Gita Agent: Internal port 7777"
echo "- Chart Endpoint: https://$DOMAIN/chart?symbol=AAPL"
echo ""
echo "Useful Commands:"
echo "- View logs: docker compose logs -f"
echo "- Restart: docker compose restart"
echo "- Stop: docker compose down"
echo "- Check status: docker compose ps"
echo ""

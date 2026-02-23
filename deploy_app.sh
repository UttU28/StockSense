#!/bin/bash
# Stock Gita Application Deployment Script
# Runs on EC2 to deploy and start the application

set -e

APP_DIR="$HOME/stock_gita_deploy"

echo "=================================="
echo "Stock Gita Application Deployment"
echo "=================================="

cd "$APP_DIR"

# Stop existing containers if any
echo "[1/5] Stopping existing containers..."
docker-compose down || true

# Configure Nginx
echo "[2/5] Configuring Nginx..."
sudo cp nginx_rakeshent.conf /etc/nginx/sites-available/rakeshent.info
sudo ln -sf /etc/nginx/sites-available/rakeshent.info /etc/nginx/sites-enabled/
# Remove old site if exists
sudo rm -f /etc/nginx/sites-enabled/stocks.thatinsaneguy.com
sudo nginx -t

# Obtain SSL Certificate (first time only)
echo "[3/5] Checking SSL certificate..."
if [ ! -d "/etc/letsencrypt/live/rakeshent.info" ]; then
    echo "Obtaining SSL certificate from Let's Encrypt..."
    # Ensure Nginx is stopped for standalone or used with --nginx plugin
    # Here we use --nginx plugin which requires Nginx to be running but reload logic handles it
    sudo certbot --nginx -d rakeshent.info --non-interactive --agree-tos --email vitthal@thatinsaneguy.com
else
    echo "SSL certificate already exists"
fi

# Reload Nginx
echo "[4/5] Reloading Nginx..."
sudo systemctl reload nginx

# Start Docker containers
echo "[5/5] Starting Docker containers..."
docker-compose up -d --build

echo ""
echo "⏳ Waiting for services to start..."
sleep 10

# Check service status
echo ""
echo "📊 Service Status:"
docker-compose ps

echo ""
echo "✅ Deployment complete!"
echo ""
echo "Services:"
echo "- Stock Gita Agent: http://localhost:7777"
echo "- Open WebUI: http://localhost:7778"
echo "- Public URL: https://rakeshent.info"
echo ""
echo "Check logs with: docker-compose logs -f"
echo ""

#!/bin/bash
# Stock Gita Server Setup Script
# Runs on EC2 Ubuntu instance to install all dependencies

set -e  # Exit on any error

echo "=================================="
echo "Stock Gita Server Setup"
echo "=================================="

# Update system
echo "[1/6] Updating system packages..."
sudo apt-get update -y
sudo apt-get upgrade -y

# Install Docker
echo "[2/6] Installing Docker..."
if ! command -v docker &> /dev/null; then
    curl -fsSL https://get.docker.com -o get-docker.sh
    sudo sh get-docker.sh
    sudo usermod -aG docker ubuntu
    rm get-docker.sh
else
    echo "Docker already installed"
fi

# Install Docker Compose
echo "[3/6] Installing Docker Compose..."
if ! command -v docker-compose &> /dev/null; then
    sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
    sudo chmod +x /usr/local/bin/docker-compose
else
    echo "Docker Compose already installed"
fi

# Install Nginx
echo "[4/6] Installing Nginx..."
sudo apt-get install -y nginx

# Install Certbot for SSL
echo "[5/6] Installing Certbot..."
sudo apt-get install -y certbot python3-certbot-nginx

# Configure firewall
echo "[6/6] Configuring firewall..."
sudo ufw allow 22/tcp    # SSH
sudo ufw allow 80/tcp    # HTTP
sudo ufw allow 443/tcp   # HTTPS
sudo ufw --force enable

echo ""
echo "✅ Server setup complete!"
echo "Docker version: $(docker --version)"
echo "Docker Compose version: $(docker-compose --version)"
echo "Nginx version: $(nginx -v 2>&1)"
echo ""
echo "Next steps:"
echo "1. Deploy application files"
echo "2. Configure Nginx reverse proxy"
echo "3. Obtain SSL certificate"
echo ""

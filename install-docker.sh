#!/bin/bash
# Install Docker and Docker Compose on Ubuntu (for StockSense deployment)
# Uses the official Docker installation script: https://get.docker.com

set -e

if command -v docker >/dev/null 2>&1; then
    echo "Docker is already installed."
    docker --version
    docker compose version 2>/dev/null || docker-compose --version 2>/dev/null || true
    echo ""
    echo "You can run ./deploy.sh now."
    exit 0
fi

echo "=== Installing Docker on Ubuntu ==="
echo ""

# Download and run the official Docker install script
echo "Downloading and running official Docker install script..."
curl -fsSL https://get.docker.com -o /tmp/get-docker.sh
sudo sh /tmp/get-docker.sh
rm -f /tmp/get-docker.sh

# Add current user to docker group so 'docker' works without sudo
echo ""
echo "Adding $USER to docker group (run 'newgrp docker' or log out/in to apply)..."
sudo usermod -aG docker "$USER" 2>/dev/null || true

echo ""
echo "=== Docker installed successfully ==="
echo ""
echo "IMPORTANT: To run docker without sudo, either:"
echo "  1. Run: newgrp docker"
echo "  2. Or log out and back in"
echo ""
echo "Then run: ./deploy.sh"
echo ""

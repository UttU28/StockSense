#!/bin/bash
# Master Deployment Script for Stock Gita
# Runs locally to deploy to EC2

set -e

# Configuration
EC2_IP="18.215.117.40"
EC2_USER="ubuntu"
SSH_KEY="$HOME/Downloads/stock-gita-key.pem"
DOMAIN="rakeshent.info"
PROJECT_DIR="/Users/vits/Desktop/trading/stock_gita_deploy"

echo "========================================"
echo "Stock Gita Deployment to EC2"
echo "Domain: $DOMAIN"
echo "IP: $EC2_IP"
echo "========================================"

# Check SSH key exists
if [ ! -f "$SSH_KEY" ]; then
    echo "❌ SSH key not found at: $SSH_KEY"
    echo ""
    echo "Please ensure the SSH key 'stock-gita-key.pem' is in ~/Downloads/"
    echo "You can download it from the AWS EC2 console if needed."
    exit 1
fi

# Set correct permissions on SSH key
chmod 400 "$SSH_KEY"

# Test SSH connection
echo ""
echo "[Step 1/6] Testing SSH connection..."
if ssh -i "$SSH_KEY" -o StrictHostKeyChecking=no "$EC2_USER@$EC2_IP" "echo 'SSH connection successful'"; then
    echo "✅ SSH connection working"
else
    echo "❌ SSH connection failed"
    echo "Please check:"
    echo "  - Instance is running"
    echo "  - Security group allows SSH from your IP"
    echo "  - SSH key is correct"
    exit 1
fi

# Package the project
echo ""
echo "[Step 2/6] Packaging project..."
cd "$PROJECT_DIR/.."
tar -czf stock_gita_deploy.tar.gz \
    --exclude='stock_gita_deploy/stock_gita_engine_charts/__pycache__' \
    --exclude='stock_gita_deploy/stock_gita_engine_charts/*/__pycache__' \
    --exclude='stock_gita_deploy/stock_gita_engine_charts/*/*/__pycache__' \
    --exclude='stock_gita_deploy/stock_gita_engine_charts/data/stock_gita.db' \
    stock_gita_deploy/

echo "✅ Project packaged ($(du -h stock_gita_deploy.tar.gz | cut -f1))"

# Transfer to server
echo ""
echo "[Step 3/6] Transferring files to server..."
scp -i "$SSH_KEY" stock_gita_deploy.tar.gz "$EC2_USER@$EC2_IP:~/"
echo "✅ Files transferred"

# Extract on server
echo ""
echo "[Step 4/6] Extracting files on server..."
ssh -i "$SSH_KEY" "$EC2_USER@$EC2_IP" "tar -xzf stock_gita_deploy.tar.gz && rm stock_gita_deploy.tar.gz"
echo "✅ Files extracted"

# Run server setup
echo ""
echo "[Step 5/6] Running server setup (Docker, Nginx, etc)..."
ssh -i "$SSH_KEY" "$EC2_USER@$EC2_IP" "bash stock_gita_deploy/server_setup.sh"
echo "✅ Server configured"

# Deploy application
echo ""
echo "[Step 6/6] Deploying application..."
ssh -i "$SSH_KEY" "$EC2_USER@$EC2_IP" "bash stock_gita_deploy/deploy_app.sh"

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
echo "- View logs: ssh -i $SSH_KEY $EC2_USER@$EC2_IP 'cd stock_gita_deploy && docker-compose logs -f'"
echo "- Restart: ssh -i $SSH_KEY $EC2_USER@$EC2_IP 'cd stock_gita_deploy && docker-compose restart'"
echo "- Stop: ssh -i $SSH_KEY $EC2_USER@$EC2_IP 'cd stock_gita_deploy && docker-compose down'"
echo ""

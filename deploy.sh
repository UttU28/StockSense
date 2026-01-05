#!/bin/bash

# StockSense Deployment Script
# Deploys both frontend (React/Vite) and backend (FastAPI) using PM2

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Configuration
BACKEND_DIR="backend"
FRONTEND_DIR="frontend"
BACKEND_PORT=8001
FRONTEND_PORT=3000

echo -e "${GREEN}=== StockSense Deployment Script ===${NC}\n"

# Check if PM2 is installed
if ! command -v pm2 &> /dev/null; then
    echo -e "${RED}PM2 is not installed. Installing PM2...${NC}"
    npm install -g pm2
fi

# Check if Python 3 is available
if ! command -v python3 &> /dev/null; then
    echo -e "${RED}Python 3 is not installed. Please install Python 3 first.${NC}"
    exit 1
fi

# Check if Node.js is available
if ! command -v node &> /dev/null; then
    echo -e "${RED}Node.js is not installed. Please install Node.js first.${NC}"
    exit 1
fi

# Function to stop existing PM2 processes
stop_existing() {
    echo -e "${YELLOW}Stopping existing PM2 processes...${NC}"
    pm2 stop stocksense-backend 2>/dev/null || true
    pm2 stop stocksense-frontend 2>/dev/null || true
    pm2 delete stocksense-backend 2>/dev/null || true
    pm2 delete stocksense-frontend 2>/dev/null || true
}

# Deploy Backend
deploy_backend() {
    echo -e "\n${GREEN}=== Deploying Backend ===${NC}"
    cd "$BACKEND_DIR"
    
    # Check if virtual environment exists, create if not
    if [ ! -d "venv" ]; then
        echo -e "${YELLOW}Creating Python virtual environment...${NC}"
        python3 -m venv venv
    fi
    
    # Activate virtual environment
    source venv/bin/activate
    
    # Install/upgrade dependencies
    echo -e "${YELLOW}Installing Python dependencies...${NC}"
    pip install --upgrade pip
    pip install -r requirements.txt
    
    # Create startup script for backend
    cat > start_backend.sh << EOF
#!/bin/bash
cd "\$(dirname "\$0")"
source venv/bin/activate
exec uvicorn app:app --host 0.0.0.0 --port ${BACKEND_PORT}
EOF
    chmod +x start_backend.sh
    
    # Create PM2 ecosystem file for backend
    cat > ecosystem.backend.config.js << EOF
module.exports = {
  apps: [{
    name: 'stocksense-backend',
    script: './start_backend.sh',
    cwd: '$(pwd)',
    instances: 1,
    autorestart: true,
    watch: false,
    max_memory_restart: '500M',
    env: {
      NODE_ENV: 'production'
    },
    error_file: './logs/backend-error.log',
    out_file: './logs/backend-out.log',
    log_date_format: 'YYYY-MM-DD HH:mm:ss Z',
    merge_logs: true
  }]
};
EOF
    
    # Create logs directory
    mkdir -p logs
    
    # Start backend with PM2
    echo -e "${YELLOW}Starting backend with PM2...${NC}"
    pm2 start ecosystem.backend.config.js
    
    cd ..
    echo -e "${GREEN}Backend deployed successfully!${NC}"
}

# Deploy Frontend
deploy_frontend() {
    echo -e "\n${GREEN}=== Deploying Frontend ===${NC}"
    cd "$FRONTEND_DIR"
    
    # Install dependencies
    echo -e "${YELLOW}Installing npm dependencies...${NC}"
    npm install
    
    # Build frontend
    echo -e "${YELLOW}Building frontend...${NC}"
    npm run build
    
    # Install serve locally (as dev dependency) for serving static files
    echo -e "${YELLOW}Installing serve package locally...${NC}"
    npm install --save-dev serve
    
    # Create startup script for frontend
    cat > start_frontend.sh << EOF
#!/bin/bash
cd "\$(dirname "\$0")"
exec npx serve -s dist -l ${FRONTEND_PORT}
EOF
    chmod +x start_frontend.sh
    
    # Create PM2 ecosystem file for frontend (use .cjs extension for CommonJS)
    cat > ecosystem.frontend.config.cjs << EOF
module.exports = {
  apps: [{
    name: 'stocksense-frontend',
    script: './start_frontend.sh',
    cwd: '$(pwd)',
    instances: 1,
    autorestart: true,
    watch: false,
    max_memory_restart: '200M',
    env: {
      NODE_ENV: 'production'
    },
    error_file: './logs/frontend-error.log',
    out_file: './logs/frontend-out.log',
    log_date_format: 'YYYY-MM-DD HH:mm:ss Z',
    merge_logs: true
  }]
};
EOF
    
    # Create logs directory
    mkdir -p logs
    
    # Start frontend with PM2
    echo -e "${YELLOW}Starting frontend with PM2...${NC}"
    pm2 start ecosystem.frontend.config.cjs
    
    cd ..
    echo -e "${GREEN}Frontend deployed successfully!${NC}"
}

# Setup Nginx
setup_nginx() {
    echo -e "\n${GREEN}=== Setting up Nginx ===${NC}"
    
    # Check if nginx is installed
    if ! command -v nginx &> /dev/null; then
        echo -e "${YELLOW}Nginx is not installed. Installing nginx...${NC}"
        if command -v apt-get &> /dev/null; then
            sudo apt-get update
            sudo apt-get install -y nginx
        elif command -v yum &> /dev/null; then
            sudo yum install -y nginx
        elif command -v pacman &> /dev/null; then
            sudo pacman -S --noconfirm nginx
        else
            echo -e "${RED}Please install nginx manually${NC}"
            return 1
        fi
    fi
    
    # Create nginx config directory if it doesn't exist
    NGINX_CONF_DIR="/etc/nginx/sites-available"
    NGINX_ENABLE_DIR="/etc/nginx/sites-enabled"
    
    # Check if sites-available exists, if not use conf.d
    if [ ! -d "$NGINX_CONF_DIR" ]; then
        NGINX_CONF_DIR="/etc/nginx/conf.d"
        NGINX_ENABLE_DIR="/etc/nginx/conf.d"
    fi
    
    # Copy nginx config with correct paths
    if [ -f "nginx/stocksense.conf" ]; then
        # Check if SSL/HTTPS is already configured
        EXISTING_CONFIG="$NGINX_CONF_DIR/stocksense.conf"
        if [ -f "$EXISTING_CONFIG" ] && sudo grep -q "listen 443\|ssl_certificate" "$EXISTING_CONFIG" 2>/dev/null; then
            echo -e "${YELLOW}SSL/HTTPS already configured. Preserving SSL settings and updating paths only...${NC}"
            # SSL is configured - only update the frontend dist path and backend port without overwriting SSL
            FRONTEND_DIST_PATH="$(pwd)/frontend/dist"
            # Backup the existing config
            sudo cp "$EXISTING_CONFIG" "$EXISTING_CONFIG.backup"
            # Update only the frontend dist path in the existing config
            sudo sed -i "s|root /home/uttu28/Desktop/StockSense/frontend/dist|root $FRONTEND_DIST_PATH|g" "$EXISTING_CONFIG"
            sudo sed -i "s|root.*frontend/dist|root $FRONTEND_DIST_PATH|g" "$EXISTING_CONFIG"
            # Update backend proxy port if it's still pointing to 8000
            sudo sed -i "s|proxy_pass http://localhost:8000;|proxy_pass http://localhost:${BACKEND_PORT};|g" "$EXISTING_CONFIG"
        else
            echo -e "${YELLOW}Copying nginx configuration...${NC}"
            # Get absolute path to frontend dist
            FRONTEND_DIST_PATH="$(pwd)/frontend/dist"
            # Create temp config with correct path
            sed "s|/home/uttu28/Desktop/StockSense/frontend/dist|$FRONTEND_DIST_PATH|g" nginx/stocksense.conf > /tmp/stocksense-nginx.conf
            sudo cp /tmp/stocksense-nginx.conf "$NGINX_CONF_DIR/stocksense.conf"
            rm /tmp/stocksense-nginx.conf
        fi
        
        # If using sites-available/sites-enabled, create symlink
        if [ "$NGINX_CONF_DIR" != "$NGINX_ENABLE_DIR" ] && [ -d "$NGINX_ENABLE_DIR" ]; then
            sudo ln -sf "$NGINX_CONF_DIR/stocksense.conf" "$NGINX_ENABLE_DIR/stocksense.conf"
        fi
        
        # Test nginx configuration
        echo -e "${YELLOW}Testing nginx configuration...${NC}"
        if sudo nginx -t; then
            echo -e "${GREEN}Nginx configuration is valid${NC}"
            
            # Reload nginx
            echo -e "${YELLOW}Reloading nginx...${NC}"
            sudo systemctl reload nginx || sudo nginx -s reload
            
            # Enable nginx to start on boot
            if command -v systemctl &> /dev/null; then
                sudo systemctl enable nginx
            fi
            
            echo -e "${GREEN}Nginx configured successfully!${NC}"
            echo -e "${YELLOW}Note: After SSL setup with certbot, the config will be updated automatically.${NC}"
        else
            echo -e "${RED}Nginx configuration test failed. Please check the config file.${NC}"
            return 1
        fi
    else
        echo -e "${RED}Nginx config file not found at nginx/stocksense.conf${NC}"
        return 1
    fi
}

# Main deployment flow
main() {
    # Stop existing processes
    stop_existing
    
    # Deploy backend
    deploy_backend
    
    # Deploy frontend
    deploy_frontend
    
    # Setup nginx
    setup_nginx
    
    # Save PM2 configuration
    echo -e "\n${YELLOW}Saving PM2 configuration...${NC}"
    pm2 save
    
    # Show status
    echo -e "\n${GREEN}=== Deployment Complete ===${NC}\n"
    pm2 status
    
    echo -e "\n${GREEN}Services are running:${NC}"
    echo -e "  Backend API:  http://localhost:${BACKEND_PORT}"
    echo -e "  Frontend UI:  http://localhost:${FRONTEND_PORT} (PM2 fallback)"
    echo -e "  API Docs:     http://localhost:${BACKEND_PORT}/docs"
    echo -e "\n${GREEN}Public URLs (via Nginx):${NC}"
    echo -e "  Frontend UI:  http://stocksense.thatinsaneguy.com (https after SSL)"
    echo -e "  Backend API:  http://stocksense.thatinsaneguy.com/api/ (https after SSL)"
    echo -e "  API Docs:     http://stocksense.thatinsaneguy.com/api/docs (https after SSL)"
    echo -e "\n${YELLOW}⚠️  Make sure DNS is configured:${NC}"
    echo -e "  - stocksense.thatinsaneguy.com -> $(hostname -I | awk '{print $1}')"
    echo -e "\n${YELLOW}⚠️  For SSL/HTTPS setup (after DNS works):${NC}"
    echo -e "  sudo certbot --nginx -d stocksense.thatinsaneguy.com"
    echo -e "  (Certbot will automatically update the nginx config for HTTPS)"
    echo -e "\n${YELLOW}Useful PM2 commands:${NC}"
    echo -e "  pm2 status              - Check process status"
    echo -e "  pm2 logs                - View all logs"
    echo -e "  pm2 logs stocksense-backend   - View backend logs"
    echo -e "  pm2 logs stocksense-frontend   - View frontend logs"
    echo -e "  pm2 restart all         - Restart all processes"
    echo -e "  pm2 stop all            - Stop all processes"
    echo -e "  pm2 delete all           - Remove all processes"
    echo -e "\n${YELLOW}Nginx commands:${NC}"
    echo -e "  sudo nginx -t            - Test nginx configuration"
    echo -e "  sudo systemctl reload nginx  - Reload nginx"
    echo -e "  sudo systemctl status nginx  - Check nginx status"
    echo -e "  sudo tail -f /var/log/nginx/stocksense-*-error.log  - View nginx errors"
}

# Run main function
main


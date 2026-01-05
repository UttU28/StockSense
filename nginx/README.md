# Nginx Configuration for StockSense

This directory contains the nginx configuration for hosting StockSense.

## Domain Structure

- **Single Domain**: `stocksense.thatinsaneguy.com`
  - **Frontend UI**: `/` (serves static files from `frontend/dist`)
  - **Backend API**: `/api/` (proxies to `localhost:8001`)

Same structure as MemeMaker project for consistency.

## DNS Setup

Before deploying, make sure your DNS records are configured:

### A Record

Add the following A record pointing to your server's IP address:

```
stocksense.thatinsaneguy.com    A    YOUR_SERVER_IP
```

### Find Your Server IP

```bash
# Get your public IP
curl ifconfig.me

# Or get local IP
hostname -I
```

## Installation

The deployment script (`deploy.sh`) will automatically:
1. Install nginx if not present
2. Copy the configuration file
3. Test the configuration
4. Reload nginx

## Manual Setup

If you prefer to set up nginx manually:

```bash
# Copy config to nginx directory
sudo cp nginx/stocksense.conf /etc/nginx/sites-available/stocksense.conf

# Create symlink (if using sites-available/sites-enabled)
sudo ln -s /etc/nginx/sites-available/stocksense.conf /etc/nginx/sites-enabled/stocksense.conf

# Test configuration
sudo nginx -t

# Reload nginx
sudo systemctl reload nginx
```

## SSL/HTTPS Setup (Optional but Recommended)

For production, you should set up SSL certificates using Let's Encrypt:

```bash
# Install certbot
sudo apt-get install certbot python3-certbot-nginx

# Get certificate for the domain
sudo certbot --nginx -d stocksense.thatinsaneguy.com

# Certbot will automatically update nginx config for HTTPS
```

After SSL setup, update the nginx config to redirect HTTP to HTTPS and update backend CORS in `backend/app.py` to include `https://` origins.

## Troubleshooting

### Check Nginx Status
```bash
sudo systemctl status nginx
```

### View Nginx Logs
```bash
# Access logs
sudo tail -f /var/log/nginx/stocksense-access.log

# Error logs
sudo tail -f /var/log/nginx/stocksense-error.log
```

### Test Configuration
```bash
sudo nginx -t
```

### Reload Nginx
```bash
sudo systemctl reload nginx
```

### Check if Ports are Open
```bash
# Check if nginx is listening on port 80
sudo netstat -tlnp | grep :80
```

### Firewall Configuration
Make sure ports 80 (and 443 for HTTPS) are open:

```bash
# UFW
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp

# firewalld
sudo firewall-cmd --permanent --add-service=http
sudo firewall-cmd --permanent --add-service=https
sudo firewall-cmd --reload
```

## Configuration Details

- **Frontend**: Serves static files from `frontend/dist` at `/`
- **Backend API**: Proxies to `http://localhost:8001` at `/api/` (keeps `/api` prefix)
- **CORS**: Handled by both nginx and FastAPI
- **Static assets**: Cached for 1 year
- **Gzip compression**: Enabled
- **SSL/HTTPS**: Configured via certbot (commented out initially for HTTP setup)


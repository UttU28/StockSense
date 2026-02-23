#!/bin/bash
# Inject Stock Gita theme into Open WebUI

CONTAINER_ID=$(docker-compose ps -q open-webui)

# Find the main HTML template in Open WebUI
docker exec $CONTAINER_ID sh -c "
  # Inject CSS link into the main template
  find /app -name '*.html' -type f | while read file; do
    if grep -q '<head>' \$file; then
      if ! grep -q 'stock_gita_terminal_theme.css' \$file; then
        sed -i '/<\/head>/i\    <link rel=\"stylesheet\" href=\"/static/stock_gita_terminal_theme.css\">' \$file
        echo \"✅ Injected theme into: \$file\"
      fi
    fi
  done
"

#!/bin/bash
# Inject Iframe Sandbox Fix into Open WebUI

echo "Injecting Iframe Fix..."

CONTAINER_ID=$(docker-compose ps -q open-webui)

if [ -z "$CONTAINER_ID" ]; then
    echo "Error: Open WebUI container not found (is it running?)"
    exit 1
fi

echo "Found Open WebUI Container: $CONTAINER_ID"

# 1. Copy the JS file into the container (using /app/backend/data/static is a safe bet for persistence, 
#    but 'inject_theme' used direct Sed injection. We'll verify path.)
#    Let's put it in /app/build/ if possible or serve it inline?
#    To be safe, we will INLINE the JS content directly into the HTML to avoid 404s on static files.

JS_CONTENT=$(cat iframe_fix.js)
# Escape backslashes and double quotes for sed
ESCAPED_JS=$(echo "$JS_CONTENT" | sed 's/\\/\\\\/g' | sed 's/"/\\"/g' | tr '\n' ' ')

docker exec $CONTAINER_ID sh -c "
  # Find HTML files (usually index.html)
  find /app -name '*.html' -type f | while read file; do
    if grep -q '</body>' \$file; then
      if ! grep -q 'Stock Gita: Sandbox Fix Active' \$file; then
        # Inject script before </body>
        sed -i 's|</body>|<script>$ESCAPED_JS</script></body>|' \$file
        echo \"✅ Injected JS fix into: \$file\"
      else
        echo \"ℹ️ JS fix already present in: \$file\"
      fi
    fi
  done
"
echo "Injection Sequence Complete."

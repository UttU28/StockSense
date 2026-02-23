#!/bin/bash
# Fixed Injection Script
# Uses docker cp to avoid shell escaping hell

echo "Injecting Iframe Fix (V2)..."

CONTAINER_ID=$(docker-compose ps -q open-webui)

if [ -z "$CONTAINER_ID" ]; then
    echo "Error: Open WebUI container not found"
    exit 1
fi

echo "Target Container: $CONTAINER_ID"

# 1. Copy the JS file explicitly into the container temp dir
docker cp iframe_fix.js $CONTAINER_ID:/tmp/iframe_fix.js

# 2. Inject it by appending the file content wrapped in <script> tags
# We use a python one-liner inside the container to handle the insertion safely, or just sed with file reading
# Actually, let's just create a script file inside the container and cat it.

docker exec $CONTAINER_ID sh -c "
  # Prepare the script tag content
  echo '<script>' > /tmp/script_tag.html
  cat /tmp/iframe_fix.js >> /tmp/script_tag.html
  echo '</script>' >> /tmp/script_tag.html

  # Find HTML files
  find /app -name 'index.html' -type f | while read file; do
    if grep -q '</body>' \$file; then
      if ! grep -q 'Stock Gita: Sandbox Fix Active' \$file; then
        # Insert safe content before body end
        # We use a temp file strategy: head + script + tail
        
        # Calculate line number of </body>
        # sed -i ... is risky with multiline. 
        # Let's simple append to head or body.
        
        sed -i 's|</body>|</body>|' \$file # No-op check
        
        # Read the file, replace </body> with <script>...</script></body>
        # Actually, let's just append to the file if it's minified? No, must be inside html.
        # Safest: Replace </body> with marker, then sub marker.
        
        # Let's try the python approach if python exists, or perl.
        # Or simple sed with 'r' command to read file!
        
        sed -i '/<\/body>/e cat /tmp/script_tag.html' \$file
        # Note: 'e' is GNU sed specific. Alpine uses busybox sed?
        # Open WebUI is likely Debian (Python base) or Alpine.
        
        # Fallback: simple cat append if not found
        # Let's try standard sed substitution with file content is hard.
        
        # Simpler: Just copy the JS content variable safely
        # We will use the 'r' command to append file content after a match? 
        # No, 'r' appends *after* the line.
        
        sed -i '/<\/body>/i <script>' \$file
        sed -i '/<\/body>/r /tmp/iframe_fix.js' \$file
        sed -i '/<\/body>/i </script>' \$file
        
        echo \"✅ Injected JS fix into: \$file\"
      else
        echo \"ℹ️ JS fix already present in: \$file\"
      fi
    fi
  done
"

echo "Injection V2 Complete."

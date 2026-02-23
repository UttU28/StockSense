#!/bin/bash
# Patch Open WebUI Frontend to remove Sandbox Restrictions
# This unlocks the ability to run Interactive Charts (TradingView) in the chat

echo "Starting Sandbox Patch..."

CONTAINER_ID=$(docker-compose ps -q open-webui)

if [ -z "$CONTAINER_ID" ]; then
    echo "Error: Open WebUI container not found"
    exit 1
fi

echo "Target Container: $CONTAINER_ID"

docker exec $CONTAINER_ID sh -c "
  # Goal: Find JS files that set the sandbox attribute and open it up.
  
  # Pattern 1: setAttribute('sandbox', ...) or similar in minified code.
  # Often looks like: e.setAttribute(\"sandbox\",\"\")
  # We replace it with lax permissions.
  
  PERMS='allow-scripts allow-same-origin allow-popups allow-forms allow-modals'
  
  echo 'Patching JS files...'
  find /app/build -name '*.js' -type f | while read file; do
    # Check if file has 'sandbox'
    if grep -q 'sandbox' \$file; then
      echo \"  Found 'sandbox' in: \$file\"
      
      # 1. Replace empty sandbox assignment: sandbox=\"\" -> sandbox=\"PERMS\"
      # Note: Minified code uses double quotes or single quotes. We try both.
      
      sed -i \"s|sandbox=\\\\\"\\\\\"|sandbox=\\\\\"\$PERMS\\\\\"|g\" \$file
      sed -i \"s|sandbox=''|sandbox='\$PERMS'|g\" \$file
      
      # 2. Replace setAttribute(\"sandbox\", ...) 
      # Matches: .setAttribute(\"sandbox\",\"\")
      sed -i \"s|setAttribute(\\\\\"sandbox\\\\\",\\\\\"\\\\\"|setAttribute(\\\\\"sandbox\\\\\",\\\\\"\$PERMS\\\\\"|g\" \$file
      
      # 3. Replace direct property assignment: .sandbox=\"\"
      sed -i \"s|.sandbox=\\\\\"\u0000\\\\\"|.sandbox=\\\\\"\$PERMS\\\\\"|g\" \$file
      
      # 4. Specific Open WebUI pattern: sometimes it is 'sandbox',t or similar.
      # If we find specific restricted permissions, expand them.
      # Matches: sandbox=\"allow-popups\" -> sandbox=\"allow-popups allow-scripts...\"
      sed -i \"s|sandbox=\\\\\"allow-popups\\\\\"|sandbox=\\\\\"\$PERMS\\\\\"|g\" \$file
      
      echo \"  - Patched \$file\"
    fi
  done
  
  echo 'Patching Complete.'
"

echo "Restarting Open WebUI to flush cache..."
docker-compose restart open-webui

echo "Success. Sandbox should be unlocked."

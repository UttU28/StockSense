#!/bin/bash
# Patch Sandbox V2 (Reliable)

echo "Deploying Patch V2..."

CONTAINER_ID=$(docker-compose ps -q open-webui)
if [ -z "$CONTAINER_ID" ]; then echo "Container not found"; exit 1; fi

# Copy helper
docker cp internal_patch.sh $CONTAINER_ID:/tmp/internal_patch.sh

# Run helper
docker exec $CONTAINER_ID sh /tmp/internal_patch.sh

echo "Restarting Open WebUI..."
docker-compose restart open-webui

echo "Patch Sequence V2 Complete."

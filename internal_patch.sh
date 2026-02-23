#!/bin/sh
# Internal Patch Script (Running inside container)

echo "Starting Internal Sandbox Patch..."

PERMS="allow-scripts allow-same-origin allow-popups allow-forms allow-modals"

# Find JS files containing 'sandbox'
grep -lR "sandbox" /app/build | while read file; do
    echo "Patching: $file"
    
    # Check if writable (should be as root/app user)
    
    # 1. Replace empty sandbox: h.sandbox="" -> h.sandbox="perms"
    # Matches minified: e.sandbox=""  or  attribute("sandbox","")
    
    # Replace assignment .sandbox=""
    sed -i "s|\.sandbox=\"\"|.sandbox=\"$PERMS\"|g" "$file"
    sed -i "s|\.sandbox=''|.sandbox='$PERMS'|g" "$file"
    
    # Replace setAttribute("sandbox", "")
    sed -i "s|setAttribute(\"sandbox\",\"\")|setAttribute(\"sandbox\",\"$PERMS\")|g" "$file"
    sed -i "s|setAttribute('sandbox','')|setAttribute('sandbox','$PERMS')|g" "$file"
    
    # Replace attribute definition in Svelte/React compiled code often like:
    # {sandbox:""} or "sandbox":""
    sed -i "s|\"sandbox\":\"\"|\"sandbox\":\"$PERMS\"|g" "$file"
    sed -i "s|'sandbox':''|'sandbox':'$PERMS'|g" "$file"
    
    # Replace explicit restrictive 'allow-popups' only
    sed -i "s|\"sandbox\":\"allow-popups\"|\"sandbox\":\"$PERMS\"|g" "$file"
    sed -i "s|setAttribute(\"sandbox\",\"allow-popups\")|setAttribute(\"sandbox\",\"$PERMS\")|g" "$file"
    
done

echo "Internal Patch Complete."

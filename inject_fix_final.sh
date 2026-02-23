#!/bin/bash
# Final Injection Script mimicking inject_theme.sh logic exactly
# This is the most reliable way to hit the template files used by Open WebUI

echo "Injecting Iframe Sandbox Fix (Final)..."

CONTAINER_ID=$(docker-compose ps -q open-webui)

if [ -z "$CONTAINER_ID" ]; then
    echo "Error: Open WebUI container not found"
    exit 1
fi

echo "Target Container: $CONTAINER_ID"

# Minified JS Payload (No backticks!)
# We use single quotes for JS strings
JS_PAYLOAD="<script>(function(){console.log('Stock Gita: Sandbox Fix Active');const f=e=>{try{if(e.src&&(e.src.includes('chart_v2')||e.src.includes('chart'))){const s=e.getAttribute('sandbox')||'';if(!s.includes('allow-scripts')){console.log('Unlock',e.src);e.setAttribute('sandbox',(s+' allow-scripts allow-same-origin allow-popups allow-forms').trim());setTimeout(()=>e.src=e.src,10)}}}catch(e){console.error(e)}};document.querySelectorAll('iframe').forEach(f);const o=new MutationObserver(m=>{m.forEach(r=>{r.addedNodes.forEach(n=>{if(n.nodeType===1){if(n.tagName==='IFRAME')f(n);if(n.querySelectorAll)n.querySelectorAll('iframe').forEach(f)}})})});o.observe(document.body,{childList:!0,subtree:!0})})();</script>"

# Escape for sed (Only forward slashes need escaping if using / delimiter, but we can use |)
# JS_PAYLOAD contains no pipes |.
# However, we must be careful with bash expansion.

docker exec $CONTAINER_ID sh -c "
  # Find ALL html files
  find /app -name '*.html' -type f | while read file; do
    if grep -q '</head>' \$file; then
      if ! grep -q 'Stock Gita' \$file; then
        # Use sed with | delimiter to avoid slash conflicts
        # Use python or just careful sed.
        
        # We inject BEFORE </head>
        sed -i \"s|</head>|$JS_PAYLOAD</head>|\" \$file
        echo \"✅ Injected Fix into: \$file\"
      else
        echo \"ℹ️ Fix already present in: \$file\"
      fi
    fi
  done
"

echo "Final Injection Complete."

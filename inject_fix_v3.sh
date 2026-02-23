#!/bin/bash
# Force Injection Script V3
# Targets /app/build/index.html specifically

echo "Force Injecting Iframe Fix (V3)..."

CONTAINER_ID=$(docker-compose ps -q open-webui)
FILE_PATH="/app/build/index.html"

# JS Content (Minified slightly)
JS_FIX='<script>(function(){console.log("Stock Gita: Sandbox Fix Active");const f=e=>{try{if(e.src&&(e.src.includes("chart_v2")||e.src.includes("chart"))){const s=e.getAttribute("sandbox")||"";if(!s.includes("allow-scripts")){console.log("Unlock",e.src);e.setAttribute("sandbox",(s+" allow-scripts allow-same-origin allow-popups allow-forms").trim());setTimeout(()=>e.src=e.src,10)}}}catch(e){console.error(e)}};document.querySelectorAll("iframe").forEach(f);const o=new MutationObserver(m=>{m.forEach(r=>{r.addedNodes.forEach(n=>{if(n.nodeType===1){if(n.tagName==="IFRAME")f(n);if(n.querySelectorAll)n.querySelectorAll("iframe").forEach(f)}})})});o.observe(document.body,{childList:!0,subtree:!0})})();</script>'

docker exec $CONTAINER_ID sh -c "
  if grep -q 'Stock Gita' $FILE_PATH; then
    echo 'Fix already present.'
  else
    # Replace </html> with SCRIPT + </html>
    sed -i \"s|</html>|$JS_FIX</html>|\" $FILE_PATH
    echo '✅ Injected V3 Fix.'
  fi
"

echo "Complete."

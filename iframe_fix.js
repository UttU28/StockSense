(function () {
    console.log("Stock Gita: Sandbox Fix Active");

    const fixIframe = (iframe) => {
        try {
            if (iframe.src && (iframe.src.includes('chart_v2') || iframe.src.includes('chart'))) {
                const sandbox = iframe.getAttribute('sandbox') || '';
                // Open WebUI often forces a strict sandbox. We must ensure allow-scripts is present.
                if (!sandbox.includes('allow-scripts')) {
                    console.log("Stock Gita: Unlocking Iframe", iframe.src);
                    // We add broad permissions to ensure TradingView works
                    const newSandbox = (sandbox + ' allow-scripts allow-same-origin allow-popups allow-forms allow-modals').trim();
                    iframe.setAttribute('sandbox', newSandbox);

                    // Reload to apply the new sandbox flags
                    // We use a slight timeout to ensure it doesn't conflict with React rendering
                    setTimeout(() => {
                        iframe.src = iframe.src;
                    }, 10);
                }
            }
        } catch (e) {
            console.error("Stock Gita Iframe Fix Error:", e);
        }
    };

    // 1. Check existing iframes immediately
    document.querySelectorAll('iframe').forEach(fixIframe);

    // 2. Observe for new iframes (Chat stream)
    const observer = new MutationObserver((mutations) => {
        mutations.forEach((m) => {
            m.addedNodes.forEach((node) => {
                if (node.nodeType === 1) { // ELEMENT_NODE
                    if (node.tagName === 'IFRAME') fixIframe(node);
                    if (node.querySelectorAll) node.querySelectorAll('iframe').forEach(fixIframe);
                }
            });
        });
    });

    observer.observe(document.body, { childList: true, subtree: true });
})();

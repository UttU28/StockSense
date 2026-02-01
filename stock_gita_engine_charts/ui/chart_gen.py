def get_tradingview_chart(symbol: str, height: int = 500) -> str:
    """
    Generates the HTML for a TradingView Advanced Real-Time Chart Widget.
    Wraps the script in an iframe to ensure execution in Chainlit/Markdown.
    """
    return get_chart_html_content(symbol)

def get_chart_html_content(symbol: str) -> str:
    """
    Returns the raw HTML for the TradingView widget.
    """
    tv_symbol = symbol.upper()
    return f"""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="utf-8" />
        <meta name="viewport" content="width=device-width, initial-scale=1" />
        <title>TradingView Chart</title>
        <style>
            html, body {{
                margin: 0;
                padding: 0;
                width: 100%;
                height: 100%;
                overflow: hidden;
                background-color: #131722; /* Dark Theme Background */
                display: flex;
                flex-direction: column;
            }}
            .tradingview-widget-container {{
                flex: 1;
                width: 100%;
                height: 100%;
            }}
            #tradingview_widget {{
                width: 100%;
                height: 100%;
            }}
        </style>
    </head>
    <body>
        <div class="tradingview-widget-container">
          <div id="tradingview_widget"></div>
          <script type="text/javascript" src="https://s3.tradingview.com/tv.js"></script>
          <script type="text/javascript">
          console.log("Initializing TradingView Widget for {tv_symbol}...");
          try {{
              new TradingView.widget(
              {{
                "autosize": true,
                "symbol": "{tv_symbol}",
                "interval": "D",
                "timezone": "Etc/UTC",
                "theme": "dark",
                "style": "1",
                "locale": "en",
                "enable_publishing": false,
                "allow_symbol_change": true,
                "container_id": "tradingview_widget",
                "hide_side_toolbar": false
              }}
              );
              console.log("Widget initialized.");
          }} catch (e) {{
              console.error("Error initializing widget:", e);
              document.body.innerHTML = "<div style='color:red; padding:20px'>Error loading chart: " + e.message + "</div>";
          }}
          </script>
        </div>
    </body>
    </html>
    """

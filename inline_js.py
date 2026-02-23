import re
import os

try:
    js_content = open('stock_gita_deploy/lightweight-charts.js').read()
    with open('stock_gita_deploy/stock_gita_engine_charts/templates/chart.html', 'r') as f:
        html = f.read()

    # The tag might be subtly different. Let's look for the src url part.
    # <script src=https://unpkg.com/lightweight-charts/dist/lightweight-charts.standalone.production.js></script>
    
    # We will split by <head> and </head> to find the script or just replace the known line line-by-line.
    
    lines = html.splitlines()
    new_lines = []
    replaced = False
    
    for line in lines:
        if 'lightweight-charts' in line and '<script' in line:
            new_lines.append(f'<script>{js_content}</script>')
            replaced = True
        else:
            new_lines.append(line)
            
    if replaced:
        with open('stock_gita_deploy/stock_gita_engine_charts/templates/chart.html', 'w') as f:
            f.write('\n'.join(new_lines))
        print(f'Successfully inlined JS. Check size: {len(js_content)}')
    else:
        print('Target line not found.')
        # Fallback: Just insert it into head
        if '<head>' in html:
             new_html = html.replace('<head>', f'<head><script>{js_content}</script>')
             with open('stock_gita_deploy/stock_gita_engine_charts/templates/chart.html', 'w') as f:
                f.write(new_html)
             print('Fallback: Inserted into <head>')

except Exception as e:
    print(e)

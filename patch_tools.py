import os
import sys

file_path = 'stock_gita_deploy/stock_gita_engine_charts/llm/tools.py'

try:
    with open(file_path, 'r') as f:
        content = f.read()

    # The goal is to insert the Indicator Details table AFTER Phase 7.
    # Anchor: lines.append(f"| Trend | {inds.get('trend')} | — |")
    #         lines.append("\n---\n")
    
    anchor_point = 'lines.append(f"| Trend | {inds.get(\'trend\')} | — |")\n    lines.append("\\n---\\n")'
    
    # New Code Block
    new_code = """
    # --- DETAILED INDICATORS (User Requested) ---
    lines.append(f"### 🧪 Detailed Indicators\\n")
    lines.append("| Indicator | Period | Value |")
    lines.append("|-----------|--------|-------|")
    
    mas = inds.get('moving_averages', {})
    for k, v in mas.items():
        lines.append(f"| SMA/EMA | {k.replace('MA_', '')} | {round(v, 2)} |")
        
    bb = inds.get('bollinger_bands', {})
    if bb:
        lines.append(f"| BollBand | Upper | {round(bb.get('upper_band', 0), 2)} |")
        lines.append(f"| BollBand | Lower | {round(bb.get('lower_band', 0), 2)} |")
        lines.append(f"| BollBand | %B | {round(bb.get('position', 0), 2)} |")
        
    srsi = inds.get('srsi', {})
    if srsi:
        lines.append(f"| StochRSI | K | {round(srsi.get('srsi_k', 0).iloc[-1] if not srsi.get('srsi_k').empty else 0, 2)} |")
        lines.append(f"| StochRSI | D | {round(srsi.get('srsi_d', 0).iloc[-1] if not srsi.get('srsi_d').empty else 0, 2)} |")
        
    lines.append("\\n---\\n")
    """
    
    if "Detailed Indicators" not in content:
        if anchor_point in content:
            content = content.replace(anchor_point, anchor_point + new_code)
            with open(file_path, 'w') as f:
                f.write(content)
            print('Successfully patched tools.py with indicators')
        else:
            print('Anchor not found. File might vary structurally.')
            # Fallback: regex or fuzzy match specific line?
            # The line `lines.append(f"| Trend | {inds.get('trend')} | — |")` is very specific.
            # Let's verify python string escaping in my heredoc.
            pass
    else:
        print('Already patched.')

except Exception as e:
    print(f'Error patching: {e}')
    sys.exit(1)

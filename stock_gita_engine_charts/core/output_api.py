from datetime import datetime

class TradeSignalAPI:
    def __init__(self):
        pass

    def generate_json_output(self, analysis_results):
        """
        Generate final standardized JSON output.
        """
        signal_data = analysis_results.get('signal', {})
        
        response = {
            "meta": {
                "timestamp": datetime.utcnow().isoformat(),
                "system": "Stock Gita API v2.0 (11-Phase)",
                "status": "OK",
                **analysis_results.get('meta', {})
            },
            "timeframes": analysis_results.get('timeframes'), # RESTORED: Multi-timeframe data
            "phases": {
                "0_calendar": analysis_results.get('phase_0_calendar'),
                "1_history": analysis_results.get('phase_1_history'),
                "2_market": analysis_results.get('phase_2_market'),
                "3_independent": analysis_results.get('phase_3_independent'),
                "4_htf_trend": analysis_results.get('phase_4_htf'),
                "5_timeframe": analysis_results.get('phase_5_timeframe'),
                "6_sli": analysis_results.get('phase_6_sli'),
                "7_confluence": analysis_results.get('phase_7_confluence'),
                "8_9_signal": analysis_results.get('phase_8_9_signal'),
                "10_options": analysis_results.get('phase_10_options')
            },
            # Legacy/Shortcut Accessors
            "signal": signal_data,
            "options": analysis_results.get('options'),
            "qualification": analysis_results.get('qualification')
        }
        
        # Add basic narrative
        if signal_data.get('signal_generated'):
             d = signal_data['direction']
             s = signal_data['symbol']
             c = signal_data['confidence']
             narrative = f"{d} Signal generated for {s} with {c}% confidence. All 11 phases complete."
        else:
             narrative = f"No trade signal generated. Reason: {signal_data.get('reason', 'Unknown')}"
             
        response['narrative'] = narrative
        
        return response

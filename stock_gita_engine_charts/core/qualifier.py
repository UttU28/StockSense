from .gate_checks import check_sli_governance, check_timeframe_alignment

class PreTradeQualificationSystem:
    def __init__(self):
        pass

    def qualify_for_trade(self, indicators, calendar_data, sli_data, regime_data, timeframes, current_price):
        """
        Verify all Permisison Gates and Confluence Dimensions.
        """
        results = {}
        
        # --- PHASE 3: HARD GATES (Blocking) ---
        regime = regime_data.get('regime', 'SIDEWAYS')
        direction = 'NEUTRAL'
        if regime == 'BULLISH': direction = 'LONG'
        elif regime == 'BEARISH': direction = 'SHORT'
        
        # 1. SLI Governance Gate
        sli_zones = sli_data.get('zones', {})
        sli_gate = check_sli_governance(current_price, sli_zones, direction)
        results['GATE_1_SLI'] = sli_gate
        
        # 2. Timeframe Alignment Gate
        tf_gate = check_timeframe_alignment(timeframes)
        results['GATE_2_TIMEFRAME'] = tf_gate
        
        # BLOCK Logic
        if not sli_gate['passed']:
            return {
                'qualification_status': 'BLOCKED',
                'reason': f"SLI Gate Failed: {sli_gate['reason']}",
                'details': results,
                'passed_checks': 0,
                'total_checks': 7
            }
            
        if not tf_gate['passed']:
            return {
                'qualification_status': 'BLOCKED',
                'reason': f"Timeframe Gate Failed: {tf_gate['reason']}",
                'details': results,
                'passed_checks': 0,
                'total_checks': 7
            }

        # --- CONFLUENCE CHECKS (Scoring) ---
        
        # 1. Candle vs BB
        bb_pos = indicators['bollinger_bands'].get('position', 0.5)
        results['1_candle_vs_bb'] = {
            'passed': bb_pos < 0.2 or bb_pos > 0.8,
            'details': f"BB Position: {bb_pos:.2f}"
        }

        # 2. AutoWaves
        aw = indicators.get('autowaves', {})
        results['2_autowaves'] = {
            'passed': aw.get('wave_type', 'none') != 'none',
            'details': f"Wave: {aw.get('wave_type')}"
        }

        # 3. SRSI Extremes
        srsi = indicators.get('srsi', {})
        results['3_srsi_extremes'] = {
            'passed': srsi.get('extreme', False),
            'details': f"SRSI: {srsi.get('srsi_value', 0):.1f}"
        }

        # 4. MACD Expansion
        macd = indicators.get('macd', {})
        results['4_macd_expansion'] = {
            'passed': macd.get('histogram_expanding', False),
            'details': "Expanding" if macd.get('histogram_expanding') else "Contracting"
        }

        # 5. MA Lamination (simplified check)
        # Check proper ordering of 13, 21, 34, 55
        mas = indicators['moving_averages']
        m13 = mas.get('MA_13')
        m21 = mas.get('MA_21')
        m34 = mas.get('MA_34')
        m55 = mas.get('MA_55')
        
        lamination = False
        if m13 and m21 and m34 and m55:
            bullish_stack = m13 > m21 > m34 > m55
            bearish_stack = m13 < m21 < m34 < m55
            lamination = bullish_stack or bearish_stack
            
        results['5_ma_lamination'] = {
            'passed': lamination,
            'details': "Laminated" if lamination else "Mixed"
        }

        # 6. Support/Resistance (Reuse SLI)
        results['6_support_resistance'] = {
            'passed': True, # Hard Gate passed already
            'details': "SLI Validated"
        }

        # 7. Calendar Alignment
        cal_passed = False
        if calendar_data:
             is_exp = calendar_data.get('expansion_window', {}).get('active', False)
             is_risk = calendar_data.get('earnings_check', {}).get('is_sensitive', False)
             cal_passed = is_exp and not is_risk

        results['7_calendar_alignment'] = {
            'passed': cal_passed,
            'details': "Aligned" if cal_passed else "Misaligned"
        }

        # Count passed
        # Only count keys starting with digit
        passed_count = sum(1 for k, r in results.items() if k[0].isdigit() and r['passed'])
        
        return {
            'qualification_status': 'QUALIFIED' if passed_count >= 5 else 'UNQUALIFIED',
            'passed_checks': passed_count,
            'total_checks': 7,
            'details': results
        }

class ConfidenceScoringEngine:
    def __init__(self):
        self.base_confidence = 60

    def calculate_confidence(self, calendar_data, qual_data, regime_data, indicators):
        """
        Calculate weighted confidence score.
        """
        score = self.base_confidence
        adjustments = {}
        
        # 1. Calendar
        if calendar_data:
            if calendar_data.get('expansion_window', {}).get('active'):
                score += 10
                adjustments['Calendar Boost'] = "+10%"
            
            if calendar_data.get('earnings_check', {}).get('is_sensitive'):
                score -= 20
                adjustments['Earnings Risk'] = "-20%"

        # 2. Confluence (Qualification)
        passed = qual_data.get('passed_checks', 0)
        total = qual_data.get('total_checks', 7)
        missing = total - passed
        if missing > 0:
            penalty = missing * 5 
            score -= penalty
            adjustments[f'Missing Confluence ({missing})'] = f"-{penalty}%"

        # 3. Regime
        if regime_data['regime'] == 'TRANSITION':
            score -= 10
            adjustments['Regime Transition'] = "-10%"
        elif regime_data['regime'] == 'SIDEWAYS':
            score -= 20
            adjustments['Regime Sideways'] = "-20%"

        # 4. Trend Strength
        adx = indicators['directional_movement'].get('trend_strength', 0)
        if adx > 25:
            score += 10
            adjustments['Strong Trend (ADX>25)'] = "+10%"
        elif adx < 15:
            score -= 10
            adjustments['Weak Trend (ADX<15)'] = "-10%"

        # Final Bounds
        final_score = max(0, min(100, score))
        
        return {
            'final_confidence': final_score,
            'adjustments': adjustments,
            'is_approved': final_score >= 60
        }

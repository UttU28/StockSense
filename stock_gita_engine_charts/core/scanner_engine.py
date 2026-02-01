from ..data.usa_api import TwelveDataAPI
from .sli_detector import detect_sli
from ..config import INDICES

class MarketIndexScanner:
    def __init__(self):
        self.api = TwelveDataAPI()
        # self.sli = SLIDetector() removed
        self.primary_indexes = [INDICES['PRIMARY'], INDICES['IND'], INDICES['TECH']]
        # Hardcoded for now as per spec, usually in DB
        self.independent_stocks = ["NVDA", "TSLA", "MSFT", "META", "AAPL"]

    def _scan_index(self, symbol):
        df = self.api.get_live_data(symbol, interval="1day", outputsize=50)
        if df is None:
            return None
        
        zones = detect_sli(df)
        # Compatibility: Calculate if "sli_detected" based on proximity could be added here
        # For now, we return the structure expected, adapting to the boolean check
        # Let's assume if there are any levels, it's 'detected' or we just pass the dict 
        # but the caller expects a dict with 'sli_detected'.
        
        current_price = df.iloc[-1]['close']
        # Simple proximity check (within 1%)
        is_near_level = False
        for level in zones.get('support', []) + zones.get('resistance', []):
             if abs(current_price - level) / current_price < 0.01:
                 is_near_level = True
                 break
                 
        result = zones
        result['sli_detected'] = is_near_level
        result['current_price'] = current_price
        return result

    def check_independent_status(self, symbol):
        return symbol in self.independent_stocks

    def phase_2_3_scan(self, symbol):
        """
        Execute Phase 2 (Market Alignment) & Phase 3 (Independent Check)
        """
        results = {
            'phase_2': {},
            'phase_3': {}
        }
        
        # Phase 2: Market Alignment
        aligned_count = 0
        details = {}
        
        for idx in self.primary_indexes:
            res = self._scan_index(idx)
            if res:
                is_sli = res['sli_detected']
                details[idx] = res
                if is_sli:
                    aligned_count += 1
            else:
                details[idx] = {"error": "Failed to fetch data"}

        results['phase_2'] = {
            'aligned_indexes': aligned_count,
            'total_indexes': len(self.primary_indexes),
            'market_status': "Favorable" if aligned_count >= 2 else "Uncertain",
            'details': details
        }

        # Phase 3: Independent Check
        is_independent = self.check_independent_status(symbol)
        results['phase_3'] = {
            'symbol': symbol,
            'is_independent': is_independent,
            'override_market_check': is_independent
        }
        
        # Permission Logic
        # Allow if Market is Favorable (2+ indexes aligned) OR Symbol is Independent
        market_ok = (aligned_count >= 2)
        permission = market_ok or is_independent
        
        results['market_permission'] = permission
        
        return results

import pandas as pd
import numpy as np
from datetime import datetime, timedelta

class SeasonalityAnalyzer:
    def __init__(self, df: pd.DataFrame, earnings_df: pd.DataFrame = None):
        """
        df must have index as DatetimeIndex or a column 'date'.
        Columns required: [open, high, low, close] (lowercase)
        earnings_df: Index as DatetimeIndex (Earnings Dates)
        """
        self.df = df.copy()
        self.earnings_df = earnings_df.copy() if earnings_df is not None else None
        
        # Normalize Data
        if 'date' in self.df.columns:
            if not pd.api.types.is_datetime64_any_dtype(self.df['date']):
                 self.df['date'] = pd.to_datetime(self.df['date'])
            self.df.set_index('date', inplace=True)
            
        self.df.sort_index(inplace=True)
        self.df.columns = [c.lower() for c in self.df.columns]
        
    def analyze(self, start_year=2021, end_year=2025):
        """
        Main entry point. Generates the full report string.
        """
        report_sections = []
        
        # 1. Year-by-Year Tables (Table A)
        combined_stats = []
        
        # Filter for years present in data
        available_years = sorted(list(set(self.df.index.year)))
        target_years = [y for y in range(start_year, end_year + 1) if y in available_years]
        
        if not target_years:
            return "No data available for the requested years."

        for year in target_years:
            year_data = self._process_year(year)
            combined_stats.extend(year_data)
            table_a = self._format_table_a(year, year_data)
            report_sections.append(table_a)
            
        # 2. Earnings Behavior (Table B)
        # Prompt Compliance: If earnings dates provided, generate table. If not, skip.
        if self.earnings_df is not None and not self.earnings_df.empty:
            table_b = self._format_table_b(start_year, end_year)
        else:
            table_b = (
                "#### Output Table B — Quarterly Earnings Behavior\n\n"
                "*No earnings dates provided in dataset. Section skipped as per instruction.*"
            )
        report_sections.append(table_b)
        
        # 3. Combined Summary (Table C)
        table_c = self._format_table_c(combined_stats)
        report_sections.append(table_c)
        
        return "\n\n".join(report_sections)

    def _format_table_b(self, start_year, end_year):
        """
        Generates Table B: Quarterly Earnings Behavior.
        Analyses price reaction 1 day before to 1 day after.
        """
        md = "#### Output Table B — Quarterly Earnings Behavior\n"
        md += "| Date | Period | Move | Direction | Label |\n"
        md += "|---|---|---|---|---|\n"
        
        # Filter earnings in range
        # Ensure TZ-naive for comparison if pricing is TZ-naive
        e_dates = self.earnings_df.index
        if e_dates.tz is not None:
             e_dates = e_dates.tz_convert(None)
             
        # Filter Logic
        mask = (e_dates.year >= start_year) & (e_dates.year <= end_year)
        target_dates = e_dates[mask]
        target_dates = sorted(target_dates, reverse=True) # Newest first
        
        if len(target_dates) == 0:
            return md + "| No earnings dates found in range | - | - | - | - |\n"
            
        for ed in target_dates:
            # Find nearest trading day 
            # (Earnings could be Sat/Sun or Holiday, map to Next Trading Day for reaction, Prev for setup)
            # Simple logic: Lookup actual date in DF. If missing, look forward.
            
            try:
                # Find index of earnings date in price df
                # Use searchsorted to find insertion point
                idx = self.df.index.searchsorted(ed)
                
                if idx >= len(self.df) or idx <= 0:
                    continue
                    
                # We want reaction: Close(EarningsDay) vs Close(PrevDay) ??
                # Usually Earnings are Pre-Market or After-Hours.
                # If After-Hours: Reaction is Next Day.
                # If Pre-Market: Reaction is Same Day.
                # Simplify: Measure Day 0 to Day +1 (Immediate reaction)
                # Or Prev Close to Current Close?
                
                # Let's measure: Close(T) - Close(T-1) around the earnings date.
                # Safest: Close(T+1) - Close(T-1) captures both Pre/Post market volatility.
                
                t_minus_1_idx = idx - 1
                t_plus_1_idx = idx + 1
                
                if t_plus_1_idx >= len(self.df):
                    continue
                    
                price_prev = self.df.iloc[t_minus_1_idx]['close']
                price_post = self.df.iloc[t_plus_1_idx]['close']
                
                move = price_post - price_prev
                pct = (move / price_prev) * 100
                
                direction = "Up" if move > 0 else "Down"
                
                # Label
                abs_pct = abs(pct)
                if abs_pct > 10: label = "Explosive"
                elif abs_pct > 5: label = "Strong"
                elif abs_pct > 2: label = "Moderate"
                else: label = "Muted"
                
                d_str = ed.strftime('%Y-%m-%d')
                
                md += f"| {d_str} | T-1 to T+1 | {move:+.2f} ({pct:+.2f}%) | {direction} | {label} |\n"
                
            except Exception as e:
                continue
                
        return md

    # ... (Keep _process_year and _process_month and _calc_phase as is) ...
    # They already calculate 'buyers', we just need to use it in formatting.

    def _format_table_a(self, year, data):
        month_names = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", 
                       "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
                       
        md = f"#### {year}\n"
        # Prompt: Early (TD1-5): Direction, $Move, Buyers
        md += "| Month | Early (1-5) | Mid (6-15) | End (16+) | Base TF | Top Bull Opp | Top Bear Opp |\n"
        md += "|---|---|---|---|---|---|---|\n"
        
        for m_data in data:
            m_idx = m_data['month'] - 1
            m_name = month_names[m_idx]
            
            p = m_data['phases']
            
            # Format: "Up +$12.34 (Bullish)"
            early = f"{p['Early']['dir']} {p['Early']['move']} ({p['Early']['buyers']})"
            mid = f"{p['Mid']['dir']} {p['Mid']['move']} ({p['Mid']['buyers']})"
            end = f"{p['End']['dir']} {p['End']['move']} ({p['End']['buyers']})"
            
            # Base TF Reason
            # Prompt: "Base time frame + a one-line reason"
            # Since logic is deterministic (max volatility), reason is essentially static description of logic.
            base_tf = m_data['base_tf']
            reason = "Most volatile phase"
            base_tf_str = f"{base_tf}<br>*{reason}*"
            
            # Opps
            bull = m_data['opportunities']['bull']
            bear = m_data['opportunities']['bear']
            
            md += f"| {m_name} | {early} | {mid} | {end} | {base_tf_str} | {bull} | {bear} |\n"
            
        return md

    def _format_table_c(self, all_data):
        # Combined Summary
        md = "### Combined Summary (2021-2025)\n"
        md += "| Month | Typical Early | Typical Mid | Typical End | Common Base TF | Common Opp Type |\n"
        md += "|---|---|---|---|---|---|\n"
        
        from collections import Counter
        
        month_names = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", 
                       "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]

        for m in range(1, 13):
            # Get all entries for this month across years
            m_entries = [d for d in all_data if d['month'] == m]
            if not m_entries:
                continue
                
            # Most common direction
            e_dirs = [d['phases']['Early']['dir'] for d in m_entries]
            m_dirs = [d['phases']['Mid']['dir'] for d in m_entries]
            end_dirs = [d['phases']['End']['dir'] for d in m_entries]
            
            common_e = Counter(e_dirs).most_common(1)[0][0]
            common_m = Counter(m_dirs).most_common(1)[0][0]
            common_end = Counter(end_dirs).most_common(1)[0][0]
            
            # Common Base TF
            bfs = [d['base_tf'] for d in m_entries]
            common_bf = Counter(bfs).most_common(1)[0][0]
            
            # Common Opp Type (Bullish vs Bearish)
            avg_bull = np.mean([abs(d['opportunities']['bull_val']) for d in m_entries])
            avg_bear = np.mean([abs(d['opportunities']['bear_val']) for d in m_entries])
            
            if avg_bull > avg_bear:
                common_opp = "Bullish"
            else:
                common_opp = "Bearish"
            
            m_name = month_names[m-1]
            
            md += f"| {m_name} | {common_e} | {common_m} | {common_end} | {common_bf} | {common_opp} |\n"
            
        return md
        
    def _process_year(self, year):
        """
        Process all months in a year.
        Returns a list of dicts (one per month).
        """
        year_df = self.df[self.df.index.year == year]
        monthly_results = []
        
        for month in range(1, 13):
            month_df = year_df[year_df.index.month == month]
            if month_df.empty:
                continue
                
            res = self._process_month(month_df, year, month)
            monthly_results.append(res)
            
        return monthly_results

    def _process_month(self, month_df, year, month):
        """
        Process a single month dataframe to extract phases and opportunities.
        """
        # Trading Days Index (0-based internally, 1-based for user)
        # 0-4 (Days 1-5), 5-14 (Days 6-15), 15+ (Days 16-End)
        
        days = list(month_df.index)
        closes = month_df['close'].tolist()
        
        # --- Phases ---
        early_idx = slice(0, 5) # Days 1-5
        mid_idx = slice(5, 15)  # Days 6-15
        end_idx = slice(15, None) # Days 16-End (rest)
        
        phases = {
            "Early": self._calc_phase(month_df, early_idx),
            "Mid": self._calc_phase(month_df, mid_idx),
            "End": self._calc_phase(month_df, end_idx)
        }
        
        # --- Opportunities ---
        opps = self._find_opportunities(month_df)
        
        # --- Base Timeframe ---
        # Find which phase had the largest absolute move
        moves = {k: abs(v['move_val']) for k, v in phases.items()}
        base_tf = max(moves, key=moves.get) if moves else "None"
        
        return {
            "year": year,
            "month": month,
            "phases": phases,
            "opportunities": opps,
            "base_tf": base_tf
        }
        
    def _calc_phase(self, df, slice_idx):
        subset = df.iloc[slice_idx]
        if subset.empty or len(subset) < 2:
            return {"dir": "N/A", "move": "$0.00", "move_val": 0, "buyers": "N/A"}
            
        start_close = subset['close'].iloc[0]
        end_close = subset['close'].iloc[-1]
        move = end_close - start_close
        
        # Sideways Rule: < $1
        threshold = 1.0 
        
        if abs(move) < threshold:
            direction = "Sideways"
            buyers = "Balanced"
        elif move > 0:
            direction = "Up"
            buyers = "Bullish"
        else:
            direction = "Down"
            buyers = "Bearish"
            
        return {
            "dir": direction,
            "move": f"{move:+.2f}",
            "move_val": move,
            "buyers": buyers
        }

    def _find_opportunities(self, df):
        """
        Find best bullish layout and best bearish layout.
        Brute force all sub-windows? Or just scan.
        For simplicity and robustness: Check moves from Swing Low to Swing High (Bullish) and High to Low (Bearish).
        """
        if len(df) < 2:
            return {"bull": None, "bear": None}
            
        closes = df['close'].values
        dates = df.index
        
        best_bull = {"val": -999999, "start": None, "end": None}
        best_bear = {"val": 999999, "start": None, "end": None} # Move is negative
        
        # Scan all pairs (i, j) where j > i
        # Optimizable, but for <31 days O(N^2) is tiny.
        for i in range(len(df)):
            for j in range(i+1, len(df)):
                move = closes[j] - closes[i]
                start_date = dates[i]
                end_date = dates[j]
                
                if move > best_bull['val']:
                    best_bull = {"val": move, "start": start_date, "end": end_date}
                    
                if move < best_bear['val']:
                     best_bear = {"val": move, "start": start_date, "end": end_date}

        return {
            "bull": self._format_opp(best_bull, "Bullish"),
            "bear": self._format_opp(best_bear, "Bearish"),
            "bull_val": best_bull['val'],
            "bear_val": best_bear['val']
        }
        
    def _format_opp(self, opp, type_):
        if opp['start'] is None:
            return "N/A"
            
        move = opp['val']
        abs_move = abs(move)
        
        # Labels
        # Excellent: $45-$50 (Assuming $45+ based on prompt "45-50")
        # Good: $30-$35
        # OK: $15-$29.99
        # Weak: < $15
        
        if abs_move >= 45: label = "Excellent"
        elif abs_move >= 30: label = "Good"
        elif abs_move >= 15: label = "OK"
        else: label = "Weak"
        
        # Prompt says: "If below OK -> No-trade / Weak"
        if label == "Weak": 
            # Prompt: "still provide the 'best available' move"
            label = "No-trade"
            
        s_date = opp['start'].strftime('%m-%d')
        e_date = opp['end'].strftime('%m-%d')
        
        # Format: "MM-DD->MM-DD, +$45.00, Excellent"
        return f"{s_date}->{e_date}, {move:+.2f}, {label}"

    def _format_table_a(self, year, data):
        month_names = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", 
                       "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
                       
        md = f"#### {year}\n"
        md += "| Month | Early (1-5) | Mid (6-15) | End (16+) | Base TF | Top Bull Opp | Top Bear Opp |\n"
        md += "|---|---|---|---|---|---|---|\n"
        
        for m_data in data:
            m_idx = m_data['month'] - 1
            m_name = month_names[m_idx]
            
            p = m_data['phases']
            early = f"{p['Early']['dir']} {p['Early']['move']}"
            mid = f"{p['Mid']['dir']} {p['Mid']['move']}"
            end = f"{p['End']['dir']} {p['End']['move']}"
            
            # Opps
            bull = m_data['opportunities']['bull']
            bear = m_data['opportunities']['bear']
            
            md += f"| {m_name} | {early} | {mid} | {end} | {m_data['base_tf']} | {bull} | {bear} |\n"
            
        return md

    def _format_table_c(self, all_data):
        # Combined Summary
        md = "### Combined Summary (2021-2025)\n"
        md += "| Month | Typical Early | Typical Mid | Typical End | Common Base TF | Common Opp Type |\n"
        md += "|---|---|---|---|---|---|\n"
        
        from collections import Counter
        
        month_names = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", 
                       "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]

        for m in range(1, 13):
            # Get all entries for this month across years
            m_entries = [d for d in all_data if d['month'] == m]
            if not m_entries:
                continue
                
            # Most common direction
            e_dirs = [d['phases']['Early']['dir'] for d in m_entries]
            m_dirs = [d['phases']['Mid']['dir'] for d in m_entries]
            end_dirs = [d['phases']['End']['dir'] for d in m_entries]
            
            common_e = Counter(e_dirs).most_common(1)[0][0]
            common_m = Counter(m_dirs).most_common(1)[0][0]
            common_end = Counter(end_dirs).most_common(1)[0][0]
            
            # Common Base TF
            bfs = [d['base_tf'] for d in m_entries]
            common_bf = Counter(bfs).most_common(1)[0][0]
            
            # Common Opp Type (Bullish vs Bearish)
            # Calculate average magnitude to decide dominant opportunity
            avg_bull = np.mean([abs(d['opportunities']['bull_val']) for d in m_entries])
            avg_bear = np.mean([abs(d['opportunities']['bear_val']) for d in m_entries])
            
            if avg_bull > avg_bear:
                common_opp = "Bullish"
            else:
                common_opp = "Bearish"
            
            m_name = month_names[m-1]
            
            md += f"| {m_name} | {common_e} | {common_m} | {common_end} | {common_bf} | {common_opp} |\n"
            
        return md

// Use /api in production (via nginx proxy), or VITE_API_URL if set, or localhost for dev
const API_BASE_URL = import.meta.env.VITE_API_URL || 
  (import.meta.env.PROD ? '/api' : 'http://localhost:8001');

export interface AnalyzeRequest {
  symbol: string;
  account_size: number;
}

export interface AnalyzeResponse {
  success: boolean;
  symbol: string;
  account_size: number;
  analysis: {
    symbol: string;
    current_price: number;
    features: {
      daily_rsi?: number;
      daily_macd_regime?: string;
      daily_macd_hist?: number;
      atr_14?: number;
      structure_score?: string;
      sma_50?: number;
      sma_200?: number;
      is_hammer?: boolean;
      is_tweezer_bottom?: boolean;
      nearest_support?: number;
      nearest_resistance?: number;
    };
    bias: {
      bias: string;
      confidence: number;
      note?: string;
    };
    alerts: {
      alert_on: boolean;
      direction?: string;
      confidence?: number;
      triggers?: string[];
    };
    regime: {
      regime: string;
      action: string;
    };
    plan: {
      entry_analysis: {
        entry_allowed: boolean;
        entry_confidence: number;
        tier: string;
        checklist: string[];
      };
      options_strategy: {
        type: string;
        dte: string;
        strike_selection: string;
      };
    };
  };
  position: {
    units: number;
    entry: number;
    stop: number;
    stop_source: string;
    take_profit_1r: number;
    take_profit_1: number;
    take_profit_2: number;
    risk_amount: number;
    total_exposure: number;
  };
}

export interface BacktestRequest {
  symbol: string;
  account_size: number;
  days: number;
}

export interface Trade {
  entry_date: string;
  exit_date: string;
  duration_days?: number;
  units: number;
  entry_price: number;
  exit_price: number;
  pnl: number;
  reason: string;
  return_pct: number;
}

export interface BacktestResponse {
  success: boolean;
  symbol: string;
  account_size: number;
  days: number;
  results: {
    total_trades: number;
    win_rate: number;
    total_pnl: number;
    final_equity: number;
    trades: Trade[];
  };
}

export interface ScanRequest {
  symbols?: string[];
  account_size: number;
}

export interface Opportunity {
  symbol: string;
  bias: string;
  confidence: number;
  strategy: string;
  take_profit_1r: number;
  take_profit_2r: number;
  units: number;
  reason: string;
  current_price: number;
}

export interface ScanResponse {
  success: boolean;
  account_size: number;
  watchlist: string[];
  count: number;
  opportunities: Opportunity[];
}

export interface PriceResponse {
  success: boolean;
  symbol: string;
  price: number;
  date: string;
  open: number;
  high: number;
  low: number;
  volume: number;
}

export interface ChartDataPoint {
  date: string;
  open: number;
  high: number;
  low: number;
  close: number;
  volume: number;
}

export interface ChartResponse {
  success: boolean;
  symbol: string;
  days: number;
  data: ChartDataPoint[];
  current_price: number;
  price_change: number;
  price_change_pct: number;
}

class ApiService {
  private async request<T>(
    endpoint: string,
    options?: RequestInit
  ): Promise<T> {
    const response = await fetch(`${API_BASE_URL}${endpoint}`, {
      ...options,
      headers: {
        'Content-Type': 'application/json',
        ...options?.headers,
      },
    });

    if (!response.ok) {
      const error = await response.json().catch(() => ({ detail: 'Unknown error' }));
      throw new Error(error.detail || `HTTP error! status: ${response.status}`);
    }

    return response.json();
  }

  async analyze(data: AnalyzeRequest): Promise<AnalyzeResponse> {
    return this.request<AnalyzeResponse>('/analyze', {
      method: 'POST',
      body: JSON.stringify(data),
    });
  }

  async backtest(data: BacktestRequest): Promise<BacktestResponse> {
    return this.request<BacktestResponse>('/backtest', {
      method: 'POST',
      body: JSON.stringify(data),
    });
  }

  async scan(data: ScanRequest): Promise<ScanResponse> {
    return this.request<ScanResponse>('/scan', {
      method: 'POST',
      body: JSON.stringify(data),
    });
  }

  async getPrice(symbol: string): Promise<PriceResponse> {
    return this.request<PriceResponse>(`/symbols/${symbol}/price`);
  }

  async getChartData(symbol: string, days: number = 30): Promise<ChartResponse> {
    return this.request<ChartResponse>(`/symbols/${symbol}/chart?days=${days}`);
  }

  async getOptionsData(symbol: string): Promise<OptionsResponse> {
    return this.request<OptionsResponse>(`/symbols/${symbol}/options`);
  }

  async healthCheck(): Promise<{ status: string }> {
    return this.request<{ status: string }>('/health');
  }
}

export interface OptionsResponse {
  success: boolean;
  symbol: string;
  current_price: number;
  atr: number;
  chains: {
    current_price: number;
    expiration_date: string;
    days_to_expiry: number;
    volatility: number;
    options: {
      strike: number;
      call_price: number;
      put_price: number;
      call_intrinsic: number;
      put_intrinsic: number;
      call_time_value: number;
      put_time_value: number;
      moneyness: number;
    }[];
  }[];
}

export const api = new ApiService();


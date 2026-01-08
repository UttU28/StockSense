import { useState, useEffect, useCallback } from "react";
import { motion } from "framer-motion";
import { 
  TrendingUp, 
  BarChart3, 
  Search, 
  DollarSign,
  TrendingDown,
  AlertCircle,
  CheckCircle2,
  Loader2,
  RefreshCw
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Badge } from "@/components/ui/badge";
import { Skeleton } from "@/components/ui/skeleton";
import { Label } from "@/components/ui/label";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
  SelectGroup,
  SelectLabel,
} from "@/components/ui/select";
import { useToast } from "@/hooks/use-toast";
import { api, AnalyzeResponse, BacktestResponse, ScanResponse, Opportunity, ChartResponse } from "@/lib/api";
import { STOCKS, getStocksByCategory, WATCHLISTS } from "@/lib/stocks";
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, BarChart, Bar, Area, AreaChart } from "recharts";

export default function Home() {
  const [activeTab, setActiveTab] = useState("analyze");
  const [symbol, setSymbol] = useState("AAPL");
  const [accountSize, setAccountSize] = useState(10000);
  const [days, setDays] = useState(100);
  const [watchlist, setWatchlist] = useState("AAPL,TSLA,NVDA,MSFT,AMZN");
  
  const [analyzeData, setAnalyzeData] = useState<AnalyzeResponse | null>(null);
  const [backtestData, setBacktestData] = useState<BacktestResponse | null>(null);
  const [scanData, setScanData] = useState<ScanResponse | null>(null);
  const [chartData, setChartData] = useState<ChartResponse | null>(null);
  const [chartType, setChartType] = useState<"price" | "ohlc">("price");
  const [optionsData, setOptionsData] = useState<any>(null);
  const [selectedExpiration, setSelectedExpiration] = useState<number>(0);

  const [loading, setLoading] = useState(false);
  const [chartLoading, setChartLoading] = useState(false);
  const [optionsLoading, setOptionsLoading] = useState(false);
  const { toast } = useToast();

  const handleAnalyze = async () => {
    if (!symbol.trim()) {
      toast({
        title: "Error",
        description: "Please enter a symbol",
        variant: "destructive",
      });
      return;
    }

    setLoading(true);
    setChartLoading(true);
    setOptionsLoading(true);
    try {
      const [analysisData, chartDataResult, optionsResult] = await Promise.all([
        api.analyze({
          symbol: symbol.toUpperCase(),
          account_size: accountSize,
        }),
        api.getChartData(symbol.toUpperCase(), 30).catch(() => null),
        api.getOptionsData(symbol.toUpperCase()).catch(() => null)
      ]);
      
      setAnalyzeData(analysisData);
      if (chartDataResult) {
        setChartData(chartDataResult);
      }
      if (optionsResult) {
        setOptionsData(optionsResult);
        setSelectedExpiration(0);
      }
      toast({
        title: "Success",
        description: `Analysis completed for ${analysisData.symbol}`,
      });
    } catch (error: any) {
      toast({
        title: "Error",
        description: error.message || "Failed to analyze symbol",
        variant: "destructive",
      });
    } finally {
      setLoading(false);
      setChartLoading(false);
      setOptionsLoading(false);
    }
  };

  const handleBacktest = async () => {
    if (!symbol.trim()) {
      toast({
        title: "Error",
        description: "Please enter a symbol",
        variant: "destructive",
      });
      return;
    }

    setLoading(true);
    try {
      const data = await api.backtest({
        symbol: symbol.toUpperCase(),
        account_size: accountSize,
        days: days,
      });
      setBacktestData(data);
      toast({
        title: "Success",
        description: `Backtest completed for ${data.symbol}`,
      });
    } catch (error: any) {
      toast({
        title: "Error",
        description: error.message || "Failed to run backtest",
        variant: "destructive",
      });
    } finally {
      setLoading(false);
    }
  };

  const handleScan = async () => {
    setLoading(true);
    try {
      const symbols = watchlist.split(",").map(s => s.trim().toUpperCase()).filter(Boolean);
      const data = await api.scan({
        symbols: symbols.length > 0 ? symbols : undefined,
        account_size: accountSize,
      });
      setScanData(data);
      toast({
        title: "Success",
        description: `Found ${data.count} opportunities`,
      });
    } catch (error: any) {
      toast({
        title: "Error",
        description: error.message || "Failed to scan market",
        variant: "destructive",
      });
    } finally {
      setLoading(false);
    }
  };

  const getBiasColor = (bias: string) => {
    switch (bias) {
      case "BULLISH":
        return "bg-green-500/20 text-green-400 border-green-500/30";
      case "BEARISH":
        return "bg-red-500/20 text-red-400 border-red-500/30";
      default:
        return "bg-gray-500/20 text-gray-400 border-gray-500/30";
    }
  };

  const getTierColor = (tier: string) => {
    switch (tier) {
      case "S":
        return "bg-purple-500/20 text-purple-400 border-purple-500/30";
      case "A":
        return "bg-blue-500/20 text-blue-400 border-blue-500/30";
      case "B":
        return "bg-yellow-500/20 text-yellow-400 border-yellow-500/30";
      default:
        return "bg-gray-500/20 text-gray-400 border-gray-500/30";
    }
  };


  // Auto-load chart when symbol changes in analyze tab
  useEffect(() => {
    if (activeTab === "analyze" && symbol && !analyzeData) {
      handleAnalyze();
  }
  }, [activeTab, symbol]);

  return (
    <div className="min-h-screen p-6 md:p-12 lg:p-16 max-w-7xl mx-auto space-y-8">
      {/* Header */}
      <motion.div 
        initial={{ opacity: 0, y: -20 }}
        animate={{ opacity: 1, y: 0 }}
        className="space-y-4"
      >
          <h1 className="text-4xl md:text-5xl font-bold font-display bg-gradient-to-br from-white to-white/60 bg-clip-text text-transparent">
          GS Trading System
          </h1>
        <p className="text-muted-foreground text-lg max-w-2xl">
          Analyze stocks, run backtests, and scan the market for trading opportunities using advanced technical analysis.
          </p>
      </motion.div>

      {/* Main Tabs */}
      <Tabs value={activeTab} onValueChange={setActiveTab} className="space-y-6">
        <TabsList className="grid w-full grid-cols-3">
          <TabsTrigger value="analyze" className="flex items-center gap-2">
            <TrendingUp className="w-4 h-4" />
            Analyze
          </TabsTrigger>
          <TabsTrigger value="backtest" className="flex items-center gap-2">
            <BarChart3 className="w-4 h-4" />
            Backtest
          </TabsTrigger>
          <TabsTrigger value="scan" className="flex items-center gap-2">
            <Search className="w-4 h-4" />
            Scan Market
          </TabsTrigger>
        </TabsList>

        {/* Analyze Tab */}
        <TabsContent value="analyze" className="space-y-6">
          <div className="space-y-6">
            <div className="space-y-4">
              <div>
                <h2 className="text-2xl font-bold mb-1">Stock Analysis</h2>
                <p className="text-sm text-muted-foreground">Get detailed technical analysis and trading signals</p>
              </div>
              <div className="flex gap-4 items-end">
                <div className="flex-1 space-y-2">
                  <Label htmlFor="analyze-symbol">Stock Symbol</Label>
                  <Select value={symbol} onValueChange={setSymbol}>
                    <SelectTrigger id="analyze-symbol">
                      <SelectValue placeholder="Select a stock" />
                    </SelectTrigger>
                    <SelectContent className="max-h-[300px]">
                      {Object.entries(getStocksByCategory()).map(([category, stocks]) => (
                        <SelectGroup key={category}>
                          <SelectLabel>{category}</SelectLabel>
                          {stocks.map((stock) => (
                            <SelectItem key={stock.symbol} value={stock.symbol}>
                              {stock.symbol} - {stock.name}
                            </SelectItem>
                          ))}
                        </SelectGroup>
                      ))}
                    </SelectContent>
                  </Select>
                </div>
                <div className="w-40 space-y-2">
                  <Label htmlFor="analyze-account">Account Size ($)</Label>
                  <Input
                    id="analyze-account"
                    type="number"
                    placeholder="10000"
                    value={accountSize}
                    onChange={(e) => setAccountSize(Number(e.target.value))}
                  />
                </div>
                <Button onClick={handleAnalyze} disabled={loading} className="mb-0">
                  {loading ? <Loader2 className="w-4 h-4 mr-2 animate-spin" /> : <TrendingUp className="w-4 h-4 mr-2" />}
                  Analyze
                </Button>
              </div>
              <p className="text-xs text-muted-foreground">
                <strong>Required:</strong> Account size is used to calculate position sizing and risk management (1% risk per trade). Default: $10,000.
              </p>

              {loading && (
                <div className="space-y-4">
                  <Skeleton className="h-32 w-full" />
                  <Skeleton className="h-32 w-full" />
        </div>
              )}

              {analyzeData && (
        <motion.div 
                  initial={{ opacity: 0, y: 20 }}
                  animate={{ opacity: 1, y: 0 }}
                  className="space-y-6"
                >

                
                  {/* Charts with Toggle */}
                  {chartData && (
                    <div className="space-y-4">
                      <div className="flex items-center justify-between">
                        <h3 className="text-lg font-semibold">
                          {chartType === "price" ? `${chartData.symbol} Price Chart (30 Days)` : "OHLC Chart (Open, High, Low, Close)"}
                        </h3>
                        <div className="flex gap-2">
                          <Button
                            variant={chartType === "price" ? "default" : "outline"}
                            size="sm"
                            onClick={() => setChartType("price")}
                          >
                            Price Chart
                          </Button>
                          <Button
                            variant={chartType === "ohlc" ? "default" : "outline"}
                            size="sm"
                            onClick={() => setChartType("ohlc")}
                          >
                            OHLC Chart
                          </Button>
                        </div>
                      </div>
                      <div className="bg-muted/30 rounded-lg p-4">
                        {chartType === "price" ? (
                          <ResponsiveContainer width="100%" height={400}>
                            <AreaChart data={chartData.data}>
                              <defs>
                                <linearGradient id="colorPrice" x1="0" y1="0" x2="0" y2="1">
                                  <stop offset="5%" stopColor="#8884d8" stopOpacity={0.3}/>
                                  <stop offset="95%" stopColor="#8884d8" stopOpacity={0}/>
                                </linearGradient>
                              </defs>
                              <CartesianGrid strokeDasharray="3 3" stroke="#374151" />
                              <XAxis 
                                dataKey="date" 
                                stroke="#9ca3af"
                                tick={{ fill: '#9ca3af' }}
                                angle={-45}
                                textAnchor="end"
                                height={80}
                              />
                              <YAxis 
                                stroke="#9ca3af"
                                tick={{ fill: '#9ca3af' }}
                                domain={['dataMin - 5', 'dataMax + 5']}
                              />
                              <Tooltip
                                contentStyle={{
                                  backgroundColor: '#1f2937',
                                  border: '1px solid #374151',
                                  borderRadius: '8px',
                                  color: '#f3f4f6'
                                }}
                                formatter={(value: number) => [`$${value.toFixed(2)}`, 'Price']}
                                labelStyle={{ color: '#9ca3af' }}
                              />
                              <Area
                                type="monotone"
                                dataKey="close"
                                stroke="#8884d8"
                                fillOpacity={1}
                                fill="url(#colorPrice)"
                                strokeWidth={2}
                              />
                            </AreaChart>
                          </ResponsiveContainer>
                        ) : (
                          <>
                            <ResponsiveContainer width="100%" height={400}>
                              <LineChart data={chartData.data}>
                                <CartesianGrid strokeDasharray="3 3" stroke="#374151" />
                                <XAxis 
                                  dataKey="date" 
                                  stroke="#9ca3af"
                                  tick={{ fill: '#9ca3af' }}
                                  angle={-45}
                                  textAnchor="end"
                                  height={80}
                                />
                                <YAxis 
                                  stroke="#9ca3af"
                                  tick={{ fill: '#9ca3af' }}
                                  domain={['dataMin - 5', 'dataMax + 5']}
                                />
                                <Tooltip
                                  contentStyle={{
                                    backgroundColor: '#1f2937',
                                    border: '1px solid #374151',
                                    borderRadius: '8px',
                                    color: '#f3f4f6'
                                  }}
                                  formatter={(value: number) => `$${value.toFixed(2)}`}
                                  labelStyle={{ color: '#9ca3af' }}
                                />
                                <Line type="monotone" dataKey="open" stroke="#3b82f6" strokeWidth={2} dot={false} />
                                <Line type="monotone" dataKey="high" stroke="#10b981" strokeWidth={2} dot={false} />
                                <Line type="monotone" dataKey="low" stroke="#ef4444" strokeWidth={2} dot={false} />
                                <Line type="monotone" dataKey="close" stroke="#8884d8" strokeWidth={2} dot={false} />
                              </LineChart>
                            </ResponsiveContainer>
                            <div className="flex gap-4 mt-4 justify-center">
                              <div className="flex items-center gap-2">
                                <div className="w-4 h-4 bg-blue-500"></div>
                                <span className="text-sm text-muted-foreground">Open</span>
                              </div>
                              <div className="flex items-center gap-2">
                                <div className="w-4 h-4 bg-green-500"></div>
                                <span className="text-sm text-muted-foreground">High</span>
                              </div>
                              <div className="flex items-center gap-2">
                                <div className="w-4 h-4 bg-red-500"></div>
                                <span className="text-sm text-muted-foreground">Low</span>
                              </div>
                              <div className="flex items-center gap-2">
                                <div className="w-4 h-4 bg-purple-500"></div>
                                <span className="text-sm text-muted-foreground">Close</span>
                              </div>
                            </div>
                          </>
                        )}
                      </div>
                    </div>
                  )}
                  
                  {/* Summary Metrics */}
                  <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
                    <div className="space-y-1">
                      <div className="text-sm text-muted-foreground">Current Price</div>
                      <div className="text-2xl font-bold">${analyzeData.analysis.current_price?.toFixed(2)}</div>
                    </div>
                    <div className="space-y-1">
                      <div className="text-sm text-muted-foreground">Bias</div>
                      <Badge className={getBiasColor(analyzeData.analysis.bias.bias)}>
                        {analyzeData.analysis.bias.bias}
                      </Badge>
                    </div>
                    <div className="space-y-1">
                      <div className="text-sm text-muted-foreground">Entry Confidence</div>
                      <div className="text-2xl font-bold">{analyzeData.analysis.plan.entry_analysis.entry_confidence}/100</div>
                    </div>
                    <div className="space-y-1">
                      <div className="text-sm text-muted-foreground">Tier</div>
                      <Badge className={getTierColor(analyzeData.analysis.plan.entry_analysis.tier)}>
                        Tier {analyzeData.analysis.plan.entry_analysis.tier}
                      </Badge>
                    </div>
                  </div>


                  {/* Technical Indicators */}
                  <div className="space-y-4 pt-6 border-t border-border/50">
                    <h3 className="text-lg font-semibold">Technical Indicators</h3>
                    <div className="grid grid-cols-2 md:grid-cols-4 gap-6">
                      <div className="space-y-1">
                        <div className="text-sm text-muted-foreground">RSI (14)</div>
                        <div className="text-xl font-semibold">{analyzeData.analysis.features.daily_rsi?.toFixed(2) || "N/A"}</div>
                      </div>
                      <div className="space-y-1">
                        <div className="text-sm text-muted-foreground">MACD Regime</div>
                        <div className="text-xl font-semibold">{analyzeData.analysis.features.daily_macd_regime || "N/A"}</div>
                      </div>
                      <div className="space-y-1">
                        <div className="text-sm text-muted-foreground">ATR (14)</div>
                        <div className="text-xl font-semibold">{analyzeData.analysis.features.atr_14?.toFixed(2) || "N/A"}</div>
                      </div>
                      <div className="space-y-1">
                        <div className="text-sm text-muted-foreground">Structure</div>
                        <div className="text-xl font-semibold">{analyzeData.analysis.features.structure_score || "N/A"}</div>
                      </div>
                    </div>
                  </div>

                  {/* Position Sizing */}
                  <div className="space-y-4 pt-6 border-t border-border/50">
                    <h3 className="text-lg font-semibold">Position Sizing</h3>
                    <div className="grid grid-cols-2 md:grid-cols-4 gap-6">
                      <div className="space-y-1">
                        <div className="text-sm text-muted-foreground">Units</div>
                        <div className="text-xl font-semibold">{analyzeData.position.units}</div>
                      </div>
                      <div className="space-y-1">
                        <div className="text-sm text-muted-foreground">Stop Loss</div>
                        <div className="text-xl font-semibold">${analyzeData.position.stop.toFixed(2)}</div>
                      </div>
                      <div className="space-y-1">
                        <div className="text-sm text-muted-foreground">Take Profit (1R)</div>
                        <div className="text-xl font-semibold">${analyzeData.position.take_profit_1r.toFixed(2)}</div>
                      </div>
                      <div className="space-y-1">
                        <div className="text-sm text-muted-foreground">Take Profit (2R)</div>
                        <div className="text-xl font-semibold">${analyzeData.position.take_profit_1.toFixed(2)}</div>
                      </div>
                    </div>
                    <div className="mt-4 pt-4 border-t border-border/50">
                      <div className="text-sm text-muted-foreground">Risk Amount</div>
                      <div className="text-2xl font-bold text-yellow-400">${analyzeData.position.risk_amount.toFixed(2)}</div>
                    </div>
                  </div>

                  {/* Entry Analysis */}
                  <div className="space-y-3 pt-6 border-t border-border/50">
                    <h3 className="text-lg font-semibold">Entry Analysis</h3>
                    <div className="space-y-2">
                      <div className="flex items-center gap-2">
                        {analyzeData.analysis.plan.entry_analysis.entry_allowed ? (
                          <CheckCircle2 className="w-5 h-5 text-green-400" />
                        ) : (
                          <AlertCircle className="w-5 h-5 text-red-400" />
                        )}
                        <span className="font-semibold">
                          Entry: {analyzeData.analysis.plan.entry_analysis.entry_allowed ? "ALLOWED" : "WAIT"}
                        </span>
                      </div>
                      <div className="text-sm text-muted-foreground">
                        Checklist: {analyzeData.analysis.plan.entry_analysis.checklist.join(", ")}
                      </div>
                    </div>
                  </div>

                  {/* Options Chain */}
                  {optionsData && optionsData.chains && optionsData.chains.length > 0 && (
                    <div className="space-y-4 pt-6 border-t border-border/50">
                      <div className="flex items-center justify-between">
                        <h3 className="text-lg font-semibold">Options Chain</h3>
                        <Select value={selectedExpiration.toString()} onValueChange={(v) => setSelectedExpiration(Number(v))}>
                          <SelectTrigger className="w-48">
                            <SelectValue />
                          </SelectTrigger>
                          <SelectContent>
                            {optionsData.chains.map((chain: any, idx: number) => (
                              <SelectItem key={idx} value={idx.toString()}>
                                {chain.days_to_expiry} Days ({chain.expiration_date})
                              </SelectItem>
                            ))}
                          </SelectContent>
                        </Select>
                      </div>
                      <div className="bg-muted/30 rounded-lg p-4 overflow-x-auto">
                        <table className="w-full text-sm">
                          <thead>
                            <tr className="border-b border-border/50">
                              <th className="text-left p-2">Strike</th>
                              <th className="text-right p-2">Call</th>
                              <th className="text-right p-2">Put</th>
                              <th className="text-right p-2">Call IV</th>
                              <th className="text-right p-2">Put IV</th>
                            </tr>
                          </thead>
                          <tbody>
                            {optionsData.chains[selectedExpiration]?.options.map((opt: any, idx: number) => (
                              <tr key={idx} className="border-b border-border/30 hover:bg-muted/50">
                                <td className="p-2 font-medium">${opt.strike.toFixed(2)}</td>
                                <td className="p-2 text-right">
                                  <div className="font-semibold">${opt.call_price.toFixed(2)}</div>
                                  <div className="text-xs text-muted-foreground">
                                    I: ${opt.call_intrinsic.toFixed(2)} T: ${opt.call_time_value.toFixed(2)}
                                  </div>
                                </td>
                                <td className="p-2 text-right">
                                  <div className="font-semibold">${opt.put_price.toFixed(2)}</div>
                                  <div className="text-xs text-muted-foreground">
                                    I: ${opt.put_intrinsic.toFixed(2)} T: ${opt.put_time_value.toFixed(2)}
                                  </div>
                                </td>
                                <td className="p-2 text-right text-muted-foreground">
                                  {opt.moneyness > 1 ? "ITM" : opt.moneyness > 0.95 ? "ATM" : "OTM"}
                                </td>
                                <td className="p-2 text-right text-muted-foreground">
                                  {opt.moneyness < 1 ? "ITM" : opt.moneyness < 1.05 ? "ATM" : "OTM"}
                                </td>
                              </tr>
                            ))}
                          </tbody>
                        </table>
                        <div className="mt-4 text-xs text-muted-foreground">
                          <p>Current Price: ${optionsData.current_price.toFixed(2)} | Volatility: {optionsData.chains[selectedExpiration]?.volatility.toFixed(1)}% | Expiration: {optionsData.chains[selectedExpiration]?.expiration_date}</p>
                          <p className="mt-1">I = Intrinsic Value, T = Time Value</p>
                        </div>
                      </div>
                    </div>
                  )}

                </motion.div>
              )}
            </div>
          </div>
        </TabsContent>

        {/* Backtest Tab */}
        <TabsContent value="backtest" className="space-y-6">
          <div className="space-y-6">
            <div className="space-y-4">
              <div>
                <h2 className="text-2xl font-bold mb-1">Backtest Strategy</h2>
                <p className="text-sm text-muted-foreground">Test your strategy on historical data</p>
              </div>
              <div className="flex gap-4 items-end">
                <div className="flex-1 space-y-2">
                  <Label htmlFor="backtest-symbol">Stock Symbol</Label>
                  <Select value={symbol} onValueChange={setSymbol}>
                    <SelectTrigger id="backtest-symbol">
                      <SelectValue placeholder="Select a stock" />
                    </SelectTrigger>
                    <SelectContent className="max-h-[300px]">
                      {Object.entries(getStocksByCategory()).map(([category, stocks]) => (
                        <SelectGroup key={category}>
                          <SelectLabel>{category}</SelectLabel>
                          {stocks.map((stock) => (
                            <SelectItem key={stock.symbol} value={stock.symbol}>
                              {stock.symbol} - {stock.name}
                            </SelectItem>
                          ))}
                        </SelectGroup>
                      ))}
                    </SelectContent>
                  </Select>
                </div>
                <div className="w-40 space-y-2">
                  <Label htmlFor="backtest-account">Account Size ($)</Label>
                  <Input
                    id="backtest-account"
                    type="number"
                    placeholder="10000"
                    value={accountSize}
                    onChange={(e) => setAccountSize(Number(e.target.value))}
                  />
                </div>
                <div className="w-32 space-y-2">
                  <Label htmlFor="backtest-days">Days</Label>
                  <Input
                    id="backtest-days"
                    type="number"
                    placeholder="100"
                    value={days}
                    onChange={(e) => setDays(Number(e.target.value))}
                  />
                </div>
                <Button onClick={handleBacktest} disabled={loading} className="mb-0">
                  {loading ? <Loader2 className="w-4 h-4 mr-2 animate-spin" /> : <BarChart3 className="w-4 h-4 mr-2" />}
                  Backtest
                </Button>
              </div>
              <p className="text-xs text-muted-foreground">
                <strong>Required:</strong> Account size is the starting capital for backtesting. Days determines how many days of historical data to test. Default: $10,000 and 100 days.
              </p>

              {loading && (
                <div className="space-y-4">
                  <Skeleton className="h-64 w-full" />
                </div>
              )}

              {backtestData && (
                <motion.div
                  initial={{ opacity: 0, y: 20 }}
                  animate={{ opacity: 1, y: 0 }}
                  className="space-y-6"
                >
                  {/* Results Summary */}
                  <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
                    <div className="space-y-1">
                      <div className="text-sm text-muted-foreground">Total Trades</div>
                      <div className="text-2xl font-bold">{backtestData.results.total_trades}</div>
                    </div>
                    <div className="space-y-1">
                      <div className="text-sm text-muted-foreground">Win Rate</div>
                      <div className="text-2xl font-bold">{backtestData.results.win_rate.toFixed(1)}%</div>
                    </div>
                    <div className="space-y-1">
                      <div className="text-sm text-muted-foreground">Total PnL</div>
                      <div className={`text-2xl font-bold ${backtestData.results.total_pnl >= 0 ? 'text-green-400' : 'text-red-400'}`}>
                        ${backtestData.results.total_pnl.toFixed(2)}
                      </div>
                    </div>
                    <div className="space-y-1">
                      <div className="text-sm text-muted-foreground">Final Equity</div>
                      <div className="text-2xl font-bold">${backtestData.results.final_equity.toFixed(2)}</div>
                    </div>
                  </div>

                  {/* Equity Curve Chart */}
                  {backtestData.results.trades.length > 0 && (
                    <div className="space-y-4 pt-6 border-t border-border/50">
                      <h3 className="text-lg font-semibold">Trade Performance</h3>
                      <div className="bg-muted/30 rounded-lg p-4">
                        <ResponsiveContainer width="100%" height={300}>
                          <BarChart data={backtestData.results.trades}>
                            <CartesianGrid strokeDasharray="3 3" />
                            <XAxis dataKey="entry_date" />
                            <YAxis />
                            <Tooltip />
                            <Bar dataKey="pnl" fill="#8884d8" />
                          </BarChart>
                        </ResponsiveContainer>
                      </div>
                    </div>
                  )}

                  {/* Trade Log */}
                  <div className="space-y-4 pt-6 border-t border-border/50">
                    <h3 className="text-lg font-semibold">Trade Log</h3>
                    <div className="space-y-3">
                      {backtestData.results.trades.map((trade: any, idx: number) => (
                        <div key={idx} className="p-4 bg-muted/30 rounded-lg space-y-3">
                          <div className="flex items-center justify-between">
                            <div className="flex items-center gap-3">
                              <div className="text-xs font-medium text-muted-foreground">#{idx + 1}</div>
                              <div>
                                <div className="font-semibold text-sm">
                                  {trade.entry_date} → {trade.exit_date}
                                  {trade.duration_days !== undefined && (
                                    <span className="text-muted-foreground font-normal ml-2">
                                      ({trade.duration_days} {trade.duration_days === 1 ? 'day' : 'days'})
                                    </span>
                                  )}
                                </div>
                                <div className="flex items-center gap-2 mt-1">
                                  <Badge variant="outline" className="text-xs">
                                    {trade.action || 'BUY'}
                                  </Badge>
                                  <Badge variant="outline" className="text-xs">
                                    {trade.trade_type || 'STOCK'}
                                  </Badge>
                                  <Badge className={`text-xs ${trade.direction === 'BULLISH' ? 'bg-green-500/20 text-green-400 border-green-500/30' : trade.direction === 'BEARISH' ? 'bg-red-500/20 text-red-400 border-red-500/30' : 'bg-gray-500/20 text-gray-400 border-gray-500/30'}`}>
                                    {trade.direction || 'NEUTRAL'}
                                  </Badge>
                                  {trade.call_or_put && trade.call_or_put !== 'N/A' && (
                                    <Badge variant="outline" className="text-xs">
                                      {trade.call_or_put}
                                    </Badge>
                                  )}
                                </div>
                                <div className="text-xs text-muted-foreground mt-1">
                                  {trade.reason.replace(/_/g, ' ')}
                                  {trade.options_strategy && trade.options_strategy !== 'NONE' && (
                                    <span className="ml-2">• Suggested: {trade.options_strategy}</span>
                                  )}
                                </div>
                              </div>
                            </div>
                            <div className={`text-right font-bold text-lg ${trade.pnl >= 0 ? 'text-green-400' : 'text-red-400'}`}>
                              ${trade.pnl.toFixed(2)}
                              <div className={`text-xs font-normal ${trade.return_pct >= 0 ? 'text-green-400' : 'text-red-400'}`}>
                                {trade.return_pct >= 0 ? '+' : ''}{trade.return_pct.toFixed(2)}%
                              </div>
                            </div>
                          </div>
                          <div className="grid grid-cols-2 md:grid-cols-4 gap-4 pt-2 border-t border-border/30 text-sm">
                            <div>
                              <div className="text-xs text-muted-foreground">Entry Price</div>
                              <div className="font-semibold">${trade.entry_price?.toFixed(2) || 'N/A'}</div>
                            </div>
                            <div>
                              <div className="text-xs text-muted-foreground">Exit Price</div>
                              <div className="font-semibold">${trade.exit_price?.toFixed(2) || 'N/A'}</div>
                            </div>
                            <div>
                              <div className="text-xs text-muted-foreground">Units</div>
                              <div className="font-semibold">{trade.units}</div>
                            </div>
                            <div>
                              <div className="text-xs text-muted-foreground">Price Change</div>
                              <div className={`font-semibold ${trade.price_change >= 0 ? 'text-green-400' : 'text-red-400'}`}>
                                {trade.price_change >= 0 ? '+' : ''}${trade.price_change?.toFixed(2) || '0.00'} 
                                <span className="text-xs ml-1">
                                  ({trade.price_change_pct >= 0 ? '+' : ''}{trade.price_change_pct?.toFixed(2) || '0.00'}%)
                                </span>
                              </div>
                            </div>
                          </div>
                        </div>
                      ))}
                    </div>
                  </div>
                </motion.div>
              )}
            </div>
          </div>
        </TabsContent>

        {/* Scan Tab */}
        <TabsContent value="scan" className="space-y-6">
          <div className="space-y-6">
            <div className="space-y-4">
              <div>
                <h2 className="text-2xl font-bold mb-1">Market Scanner</h2>
                <p className="text-sm text-muted-foreground">Scan multiple stocks for trading opportunities</p>
              </div>
              <div className="space-y-3">
                <div className="flex gap-4 items-end">
                  <div className="flex-1 space-y-2">
                    <Label htmlFor="scan-symbols">Stock Symbols</Label>
                    <Input
                      id="scan-symbols"
                      placeholder="AAPL,TSLA,NVDA,MSFT,AMZN"
                      value={watchlist}
                      onChange={(e) => setWatchlist(e.target.value)}
                    />
                  </div>
                  <div className="w-40 space-y-2">
                    <Label htmlFor="scan-account">Account Size ($)</Label>
                    <Input
                      id="scan-account"
                      type="number"
                      placeholder="10000"
                      value={accountSize}
                      onChange={(e) => setAccountSize(Number(e.target.value))}
                    />
                  </div>
                  <Button onClick={handleScan} disabled={loading} className="mb-0">
                    {loading ? <Loader2 className="w-4 h-4 mr-2 animate-spin" /> : <Search className="w-4 h-4 mr-2" />}
                    Scan
                  </Button>
                </div>
                <p className="text-xs text-muted-foreground">
                  Enter comma-separated stock symbols or use quick select buttons below. <strong>Required:</strong> Account size is used for position sizing calculations. Default: $10,000.
                </p>
                <div className="flex flex-wrap gap-2">
                  <span className="text-sm text-muted-foreground self-center">Quick select:</span>
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={() => setWatchlist(WATCHLISTS.tech.join(","))}
                  >
                    Tech
                  </Button>
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={() => setWatchlist(WATCHLISTS.finance.join(","))}
                  >
                    Finance
                  </Button>
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={() => setWatchlist(WATCHLISTS.healthcare.join(","))}
                  >
                    Healthcare
                  </Button>
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={() => setWatchlist(WATCHLISTS.popular.join(","))}
                  >
                    Popular
                  </Button>
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={() => setWatchlist(WATCHLISTS.crypto.join(","))}
                  >
                    Crypto
                  </Button>
                </div>
              </div>

              {loading && (
                <div className="space-y-4">
                  <Skeleton className="h-32 w-full" />
                  <Skeleton className="h-32 w-full" />
                </div>
              )}

              {scanData && (
        <motion.div 
                  initial={{ opacity: 0, y: 20 }}
                  animate={{ opacity: 1, y: 0 }}
                  className="space-y-4"
                >
                  <div className="flex items-center justify-between">
                    <div className="text-lg font-semibold">
                      Found {scanData.count} Opportunities
                    </div>
                    <Badge variant="outline">{scanData.watchlist.length} symbols scanned</Badge>
                  </div>

                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    {scanData.opportunities.map((opp: Opportunity, idx: number) => (
                      <div key={idx} className="p-4 bg-muted/30 rounded-lg space-y-3">
                        <div className="flex items-center justify-between">
                          <h4 className="text-xl font-semibold">{opp.symbol}</h4>
                          <Badge className={getBiasColor(opp.bias)}>{opp.bias}</Badge>
                        </div>
                        <div className="space-y-2">
                          <div className="flex items-center justify-between">
                            <span className="text-sm text-muted-foreground">Confidence</span>
                            <span className="text-lg font-bold">{opp.confidence}/100</span>
                          </div>
                          <div className="flex items-center justify-between">
                            <span className="text-sm text-muted-foreground">Price</span>
                            <span className="text-lg font-semibold">${opp.current_price?.toFixed(2)}</span>
                          </div>
                          <div className="flex items-center justify-between">
                            <span className="text-sm text-muted-foreground">Units</span>
                            <span className="text-lg font-semibold">{opp.units}</span>
                          </div>
                          <div className="pt-2 border-t border-border/50">
                            <div className="text-xs text-muted-foreground mb-1">Strategy</div>
                            <div className="text-sm font-medium">{opp.strategy}</div>
                          </div>
                          <div className="text-xs text-muted-foreground">
                            {opp.reason}
                          </div>
                        </div>
                      </div>
                    ))}
                  </div>

                  {scanData.opportunities.length === 0 && (
                    <div className="text-center py-12 text-muted-foreground">
                      No opportunities found. Try different symbols or check back later.
          </div>
                  )}
        </motion.div>
      )}
            </div>
          </div>
        </TabsContent>
      </Tabs>
    </div>
  );
}

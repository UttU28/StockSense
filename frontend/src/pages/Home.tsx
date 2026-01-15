import { useState, useEffect } from "react";
import { motion } from "framer-motion";
import { TrendingUp, BarChart3, Search, Loader2 } from "lucide-react";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { useToast } from "@/hooks/use-toast";
import { api, AnalyzeResponse, BacktestResponse, ScanResponse, ChartResponse, OptionsResponse } from "@/lib/api";
import { AnalyzeTab } from "@/components/tabs/AnalyzeTab";
import { BacktestTab } from "@/components/tabs/BacktestTab";
import { ScanTab } from "@/components/tabs/ScanTab";

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
  const [optionsData, setOptionsData] = useState<OptionsResponse | null>(null);

  const [loading, setLoading] = useState(false);
  const { toast } = useToast();

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

  const handleAnalyze = async (symbolToAnalyze?: string) => {
    const symbolToUse = symbolToAnalyze || symbol;
    if (!symbolToUse.trim()) {
      toast({
        title: "Error",
        description: "Please enter a symbol",
        variant: "destructive",
      });
      return;
    }

    setLoading(true);
    try {
      const [analysisData, chartDataResult, optionsResult] = await Promise.all([
        api.analyze({
          symbol: symbolToUse.toUpperCase(),
          account_size: accountSize,
        }),
        api.getChartData(symbolToUse.toUpperCase(), 30).catch(() => null),
        api.getOptionsData(symbolToUse.toUpperCase()).catch(() => null)
      ]);
      
      setAnalyzeData(analysisData);
      if (chartDataResult) {
        setChartData(chartDataResult);
      }
      if (optionsResult) {
        setOptionsData(optionsResult);
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

  const handleSymbolChange = (newSymbol: string) => {
    setSymbol(newSymbol);
    if (activeTab === "analyze" && newSymbol.trim()) {
      handleAnalyze(newSymbol);
    }
  };

  // Auto-load analysis on initial page load and when switching to analyze tab
  useEffect(() => {
    if (activeTab === "analyze" && symbol && symbol.trim()) {
      const needsLoad = !analyzeData || analyzeData.symbol !== symbol.toUpperCase();
      if (needsLoad && !loading) {
        const timer = setTimeout(() => {
          handleAnalyze();
        }, 100);
        return () => clearTimeout(timer);
      }
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
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
        <TabsContent value="analyze">
          <AnalyzeTab
            symbol={symbol}
            accountSize={accountSize}
            loading={loading}
            analyzeData={analyzeData}
            chartData={chartData}
            optionsData={optionsData}
            onSymbolChange={handleSymbolChange}
            onAccountSizeChange={setAccountSize}
            onAnalyze={() => handleAnalyze()}
            getBiasColor={getBiasColor}
            getTierColor={getTierColor}
          />
        </TabsContent>

        {/* Backtest Tab */}
        <TabsContent value="backtest">
          <BacktestTab
            symbol={symbol}
            accountSize={accountSize}
            days={days}
            loading={loading}
            backtestData={backtestData}
            onSymbolChange={setSymbol}
            onAccountSizeChange={setAccountSize}
            onDaysChange={setDays}
            onBacktest={handleBacktest}
          />
        </TabsContent>

        {/* Scan Tab */}
        <TabsContent value="scan">
          <ScanTab
            watchlist={watchlist}
            accountSize={accountSize}
            loading={loading}
            scanData={scanData}
            onWatchlistChange={setWatchlist}
            onAccountSizeChange={setAccountSize}
            onScan={handleScan}
            getBiasColor={getBiasColor}
          />
        </TabsContent>
      </Tabs>
    </div>
  );
}

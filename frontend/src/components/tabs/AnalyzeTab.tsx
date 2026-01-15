import { useState } from "react";
import { motion } from "framer-motion";
import { TrendingUp, Loader2 } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Skeleton } from "@/components/ui/skeleton";
import { AnalyzeResponse, ChartResponse, OptionsResponse } from "@/lib/api";
import { StockSelector } from "@/components/StockSelector";
import { SummaryMetrics } from "@/components/SummaryMetrics";
import { PriceChart } from "@/components/PriceChart";
import { TechnicalIndicators } from "@/components/TechnicalIndicators";
import { PositionSizing } from "@/components/PositionSizing";
import { MarketContext } from "@/components/MarketContext";
import { AdditionalIndicators } from "@/components/AdditionalIndicators";
import { EntryAnalysis } from "@/components/EntryAnalysis";
import { OptionsChain } from "@/components/OptionsChain";

interface AnalyzeTabProps {
  symbol: string;
  accountSize: number;
  loading: boolean;
  analyzeData: AnalyzeResponse | null;
  chartData: ChartResponse | null;
  optionsData: OptionsResponse | null;
  onSymbolChange: (symbol: string) => void;
  onAccountSizeChange: (size: number) => void;
  onAnalyze: () => void;
  getBiasColor: (bias: string) => string;
  getTierColor: (tier: string) => string;
}

export function AnalyzeTab({
  symbol,
  accountSize,
  loading,
  analyzeData,
  chartData,
  optionsData,
  onSymbolChange,
  onAccountSizeChange,
  onAnalyze,
  getBiasColor,
  getTierColor,
}: AnalyzeTabProps) {
  const [chartType, setChartType] = useState<"price" | "ohlc">("price");

  return (
    <div className="space-y-6">
      <div className="space-y-4">
        <div>
          <h2 className="text-2xl font-bold mb-1">Stock Analysis</h2>
          <p className="text-sm text-muted-foreground">Get detailed technical analysis and trading signals</p>
        </div>
        <div className="flex gap-4 items-end">
          <StockSelector symbol={symbol} onSymbolChange={onSymbolChange} id="analyze-symbol" />
          <div className="w-40 space-y-2">
            <Label htmlFor="analyze-account">Account Size ($)</Label>
            <Input
              id="analyze-account"
              type="number"
              placeholder="10000"
              value={accountSize}
              onChange={(e) => onAccountSizeChange(Number(e.target.value))}
            />
          </div>
          <Button onClick={onAnalyze} disabled={loading} className="mb-0">
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
            {chartData && (
              <PriceChart 
                chartData={chartData} 
                chartType={chartType} 
                onChartTypeChange={setChartType}
              />
            )}
            
            <SummaryMetrics
              currentPrice={analyzeData.analysis.current_price}
              bias={analyzeData.analysis.bias.bias}
              entryConfidence={analyzeData.analysis.plan.entry_analysis.entry_confidence}
              tier={analyzeData.analysis.plan.entry_analysis.tier}
              getBiasColor={getBiasColor}
              getTierColor={getTierColor}
            />

            <TechnicalIndicators analyzeData={analyzeData} />
            <PositionSizing position={analyzeData.position} />
            <MarketContext analyzeData={analyzeData} getBiasColor={getBiasColor} />
            <AdditionalIndicators analyzeData={analyzeData} />
            <EntryAnalysis analyzeData={analyzeData} />
            
            {optionsData && <OptionsChain optionsData={optionsData} />}
          </motion.div>
        )}
      </div>
    </div>
  );
}

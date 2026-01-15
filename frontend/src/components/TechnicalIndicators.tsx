import { Badge } from "@/components/ui/badge";
import { AnalyzeResponse } from "@/lib/api";

interface TechnicalIndicatorsProps {
  analyzeData: AnalyzeResponse;
}

export function TechnicalIndicators({ analyzeData }: TechnicalIndicatorsProps) {
  const getRsiColor = (rsi: number | undefined) => {
    if (!rsi) return '';
    if (rsi >= 70) return 'text-red-400';
    if (rsi <= 30) return 'text-green-400';
    return '';
  };

  const getMacdRegimeBadge = (regime: string | undefined) => {
    if (!regime) return null;
    return (
      <Badge className={
        regime === "BULLISH" 
          ? "bg-green-500/20 text-green-400 border-green-500/50" 
          : regime === "BEARISH"
          ? "bg-red-500/20 text-red-400 border-red-500/50"
          : ""
      }>
        {regime}
      </Badge>
    );
  };

  const getStructureBadge = (structure: string | undefined) => {
    if (!structure) return null;
    return (
      <Badge className={
        structure === "HIGH" 
          ? "bg-green-500/20 text-green-400 border-green-500/50" 
          : structure === "LOW"
          ? "bg-red-500/20 text-red-400 border-red-500/50"
          : ""
      }>
        {structure}
      </Badge>
    );
  };

  const indicators = analyzeData.analysis.features.indicators;
  const features = analyzeData.analysis.features;

  return (
    <div className="space-y-6 pt-6 border-t border-border/50">
      <div className="flex items-center justify-between">
        <h3 className="text-lg font-semibold">Technical Indicators</h3>
        <div className="text-xs text-muted-foreground">
          Last Updated: {new Date(analyzeData.analysis.last_updated).toLocaleString()}
        </div>
      </div>
      
      {/* Daily Indicators */}
      <div className="space-y-3 bg-muted/20 rounded-lg p-4">
        <h4 className="text-sm font-medium">Daily Timeframe</h4>
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          <div className="space-y-1">
            <div className="text-xs text-muted-foreground">RSI</div>
            <div className={`text-lg font-semibold ${getRsiColor(indicators?.daily?.rsi || features.daily_rsi)}`}>
              {indicators?.daily?.rsi?.toFixed(2) || features.daily_rsi?.toFixed(2) || "N/A"}
            </div>
          </div>
          <div className="space-y-1">
            <div className="text-xs text-muted-foreground">MACD</div>
            <div className="text-lg font-semibold">{indicators?.daily?.macd?.toFixed(3) || "N/A"}</div>
          </div>
          <div className="space-y-1">
            <div className="text-xs text-muted-foreground">MACD Signal</div>
            <div className="text-lg font-semibold">{indicators?.daily?.macd_signal?.toFixed(3) || "N/A"}</div>
          </div>
          <div className="space-y-1">
            <div className="text-xs text-muted-foreground">MACD Hist</div>
            <div className="text-lg font-semibold">{indicators?.daily?.macd_hist?.toFixed(3) || features.daily_macd_hist?.toFixed(3) || "N/A"}</div>
          </div>
          <div className="space-y-1">
            <div className="text-xs text-muted-foreground">BB Upper</div>
            <div className="text-lg font-semibold">{indicators?.daily?.bb_upper?.toFixed(2) || "N/A"}</div>
          </div>
          <div className="space-y-1">
            <div className="text-xs text-muted-foreground">BB Middle</div>
            <div className="text-lg font-semibold">{indicators?.daily?.bb_middle?.toFixed(2) || "N/A"}</div>
          </div>
          <div className="space-y-1">
            <div className="text-xs text-muted-foreground">BB Lower</div>
            <div className="text-lg font-semibold">{indicators?.daily?.bb_lower?.toFixed(2) || "N/A"}</div>
          </div>
          <div className="space-y-1">
            <div className="text-xs text-muted-foreground">MACD Regime</div>
            {getMacdRegimeBadge(features.daily_macd_regime)}
          </div>
        </div>
      </div>

      {/* Weekly Indicators */}
      <div className="space-y-3 bg-muted/20 rounded-lg p-4">
        <h4 className="text-sm font-medium">Weekly Timeframe</h4>
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          <div className="space-y-1">
            <div className="text-xs text-muted-foreground">RSI</div>
            <div className={`text-lg font-semibold ${getRsiColor(indicators?.weekly?.rsi || features.weekly_rsi)}`}>
              {indicators?.weekly?.rsi?.toFixed(2) || features.weekly_rsi?.toFixed(2) || "N/A"}
            </div>
          </div>
          <div className="space-y-1">
            <div className="text-xs text-muted-foreground">MACD</div>
            <div className="text-lg font-semibold">{indicators?.weekly?.macd?.toFixed(3) || "N/A"}</div>
          </div>
          <div className="space-y-1">
            <div className="text-xs text-muted-foreground">MACD Signal</div>
            <div className="text-lg font-semibold">{indicators?.weekly?.macd_signal?.toFixed(3) || "N/A"}</div>
          </div>
          <div className="space-y-1">
            <div className="text-xs text-muted-foreground">MACD Hist</div>
            <div className="text-lg font-semibold">{indicators?.weekly?.macd_hist?.toFixed(3) || "N/A"}</div>
          </div>
          <div className="space-y-1">
            <div className="text-xs text-muted-foreground">BB Upper</div>
            <div className="text-lg font-semibold">{indicators?.weekly?.bb_upper?.toFixed(2) || "N/A"}</div>
          </div>
          <div className="space-y-1">
            <div className="text-xs text-muted-foreground">BB Middle</div>
            <div className="text-lg font-semibold">{indicators?.weekly?.bb_middle?.toFixed(2) || "N/A"}</div>
          </div>
          <div className="space-y-1">
            <div className="text-xs text-muted-foreground">BB Lower</div>
            <div className="text-lg font-semibold">{indicators?.weekly?.bb_lower?.toFixed(2) || "N/A"}</div>
          </div>
          <div className="space-y-1">
            <div className="text-xs text-muted-foreground">MACD Regime</div>
            {getMacdRegimeBadge(features.weekly_macd_regime)}
          </div>
        </div>
      </div>

      {/* Monthly Indicators */}
      <div className="space-y-3 bg-muted/20 rounded-lg p-4">
        <h4 className="text-sm font-medium">Monthly Timeframe</h4>
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          <div className="space-y-1">
            <div className="text-xs text-muted-foreground">RSI</div>
            <div className={`text-lg font-semibold ${getRsiColor(indicators?.monthly?.rsi)}`}>
              {indicators?.monthly?.rsi?.toFixed(2) || "N/A"}
            </div>
          </div>
          <div className="space-y-1">
            <div className="text-xs text-muted-foreground">MACD</div>
            <div className="text-lg font-semibold">{indicators?.monthly?.macd?.toFixed(3) || "N/A"}</div>
          </div>
          <div className="space-y-1">
            <div className="text-xs text-muted-foreground">MACD Signal</div>
            <div className="text-lg font-semibold">{indicators?.monthly?.macd_signal?.toFixed(3) || "N/A"}</div>
          </div>
          <div className="space-y-1">
            <div className="text-xs text-muted-foreground">MACD Hist</div>
            <div className="text-lg font-semibold">{indicators?.monthly?.macd_hist?.toFixed(3) || "N/A"}</div>
          </div>
          <div className="space-y-1">
            <div className="text-xs text-muted-foreground">BB Upper</div>
            <div className="text-lg font-semibold">{indicators?.monthly?.bb_upper?.toFixed(2) || "N/A"}</div>
          </div>
          <div className="space-y-1">
            <div className="text-xs text-muted-foreground">BB Middle</div>
            <div className="text-lg font-semibold">{indicators?.monthly?.bb_middle?.toFixed(2) || "N/A"}</div>
          </div>
          <div className="space-y-1">
            <div className="text-xs text-muted-foreground">BB Lower</div>
            <div className="text-lg font-semibold">{indicators?.monthly?.bb_lower?.toFixed(2) || "N/A"}</div>
          </div>
        </div>
      </div>

      {/* SMAs and Other Indicators */}
      <div className="space-y-3 bg-muted/20 rounded-lg p-4">
        <h4 className="text-sm font-medium">Moving Averages & Other</h4>
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          <div className="space-y-1">
            <div className="text-xs text-muted-foreground">SMA 55</div>
            <div className="text-lg font-semibold">{indicators?.sma?.sma_55?.toFixed(2) || features.sma_55?.toFixed(2) || "N/A"}</div>
          </div>
          <div className="space-y-1">
            <div className="text-xs text-muted-foreground">SMA 89</div>
            <div className="text-lg font-semibold">{indicators?.sma?.sma_89?.toFixed(2) || features.sma_89?.toFixed(2) || "N/A"}</div>
          </div>
          <div className="space-y-1">
            <div className="text-xs text-muted-foreground">SMA 144</div>
            <div className="text-lg font-semibold">{indicators?.sma?.sma_144?.toFixed(2) || features.sma_144?.toFixed(2) || "N/A"}</div>
          </div>
          <div className="space-y-1">
            <div className="text-xs text-muted-foreground">SMA 233</div>
            <div className="text-lg font-semibold">{indicators?.sma?.sma_233?.toFixed(2) || features.sma_233?.toFixed(2) || "N/A"}</div>
          </div>
          <div className="space-y-1">
            <div className="text-xs text-muted-foreground">ATR (14)</div>
            <div className="text-lg font-semibold">{features.atr_14?.toFixed(2) || "N/A"}</div>
          </div>
          <div className="space-y-1">
            <div className="text-xs text-muted-foreground">Structure</div>
            {getStructureBadge(features.structure_score)}
          </div>
        </div>
      </div>
    </div>
  );
}

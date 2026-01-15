import { AnalyzeResponse } from "@/lib/api";

interface AdditionalIndicatorsProps {
  analyzeData: AnalyzeResponse;
}

export function AdditionalIndicators({ analyzeData }: AdditionalIndicatorsProps) {
  const { features, daily_bars } = analyzeData.analysis;

  return (
    <div className="space-y-4 pt-6 border-t border-border/50">
      <h3 className="text-lg font-semibold">Additional Indicators</h3>
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <div className="space-y-1">
          <div className="text-xs text-muted-foreground">StochRSI K</div>
          <div className="text-lg font-semibold">
            {features.daily_stoch_k?.toFixed(2) || "N/A"}
          </div>
        </div>
        <div className="space-y-1">
          <div className="text-xs text-muted-foreground">StochRSI D</div>
          <div className="text-lg font-semibold">
            {features.daily_stoch_d?.toFixed(2) || "N/A"}
          </div>
        </div>
        <div className="space-y-1">
          <div className="text-xs text-muted-foreground">RSI Zone</div>
          <div className="text-lg font-semibold">
            {features.daily_rsi_zone || "N/A"}
          </div>
        </div>
        <div className="space-y-1">
          <div className="text-xs text-muted-foreground">Volume (Latest)</div>
          <div className="text-lg font-semibold">
            {daily_bars?.[0]?.volume?.toLocaleString() || "N/A"}
          </div>
        </div>
      </div>
    </div>
  );
}

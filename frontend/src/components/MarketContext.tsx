import { Badge } from "@/components/ui/badge";
import { AnalyzeResponse } from "@/lib/api";

interface MarketContextProps {
  analyzeData: AnalyzeResponse;
  getBiasColor: (bias: string) => string;
}

export function MarketContext({ analyzeData, getBiasColor }: MarketContextProps) {
  const { bias, regime, alerts, features } = analyzeData.analysis;

  return (
    <div className="space-y-4 pt-6 border-t border-border/50">
      <h3 className="text-lg font-semibold">Market Context</h3>
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <div className="space-y-4">
          <div>
            <div className="text-sm text-muted-foreground mb-2">Bias & Confidence</div>
            <div className="flex items-center gap-3">
              <Badge className={getBiasColor(bias.bias)}>
                {bias.bias}
              </Badge>
              <span className="text-sm text-muted-foreground">
                Confidence: {bias.confidence || 0}%
              </span>
              {bias.note && (
                <span className="text-xs text-muted-foreground italic">
                  ({bias.note})
                </span>
              )}
            </div>
          </div>
          <div>
            <div className="text-sm text-muted-foreground mb-2">Regime</div>
            <div className="flex items-center gap-2">
              <Badge variant="outline">
                {regime.regime || "N/A"}
              </Badge>
              <span className="text-sm text-muted-foreground">
                → {regime.action || "N/A"}
              </span>
            </div>
          </div>
          {alerts?.alert_on && (
            <div>
              <div className="text-sm text-muted-foreground mb-2">Alerts</div>
              <div className="flex flex-wrap gap-2">
                {alerts.triggers?.map((trigger: string, idx: number) => (
                  <Badge key={idx} variant="destructive" className="text-xs">
                    {trigger}
                  </Badge>
                ))}
              </div>
            </div>
          )}
        </div>
        <div className="space-y-4">
          <div>
            <div className="text-sm text-muted-foreground mb-2">Key Levels</div>
            <div className="grid grid-cols-2 gap-4">
              <div>
                <div className="text-xs text-muted-foreground">Support</div>
                <div className="text-lg font-semibold text-green-400">
                  ${features.nearest_support?.toFixed(2) || "N/A"}
                </div>
              </div>
              <div>
                <div className="text-xs text-muted-foreground">Resistance</div>
                <div className="text-lg font-semibold text-red-400">
                  ${features.nearest_resistance?.toFixed(2) || "N/A"}
                </div>
              </div>
            </div>
          </div>
          <div>
            <div className="text-sm text-muted-foreground mb-2">Candle Patterns</div>
            <div className="flex flex-wrap gap-2">
              {features.is_hammer && (
                <Badge variant="outline" className="text-xs">🔨 HAMMER</Badge>
              )}
              {features.is_tweezer_bottom && (
                <Badge variant="outline" className="text-xs">📊 TWEEZER BOTTOM</Badge>
              )}
              {!features.is_hammer && !features.is_tweezer_bottom && (
                <span className="text-sm text-muted-foreground">None detected</span>
              )}
            </div>
          </div>
          {features.days_to_earnings !== null && features.days_to_earnings !== undefined && (
            <div>
              <div className="text-sm text-muted-foreground mb-2">Earnings</div>
              <div className="flex items-center gap-2">
                <Badge variant={features.days_to_earnings <= 7 ? "destructive" : "outline"}>
                  {features.days_to_earnings} days
                </Badge>
                <span className="text-xs text-muted-foreground">
                  ({features.earnings_status || "N/A"})
                </span>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

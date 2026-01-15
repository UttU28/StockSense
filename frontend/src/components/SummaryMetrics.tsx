import { Badge } from "@/components/ui/badge";

interface SummaryMetricsProps {
  currentPrice: number;
  bias: string;
  entryConfidence: number;
  tier: string;
  getBiasColor: (bias: string) => string;
  getTierColor: (tier: string) => string;
}

export function SummaryMetrics({
  currentPrice,
  bias,
  entryConfidence,
  tier,
  getBiasColor,
  getTierColor,
}: SummaryMetricsProps) {
  return (
    <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
      <div className="space-y-1">
        <div className="text-sm text-muted-foreground">Current Price</div>
        <div className="text-2xl font-bold">${currentPrice?.toFixed(2)}</div>
      </div>
      <div className="space-y-1">
        <div className="text-sm text-muted-foreground">Bias</div>
        <Badge className={getBiasColor(bias)}>
          {bias}
        </Badge>
      </div>
      <div className="space-y-1">
        <div className="text-sm text-muted-foreground">Entry Confidence</div>
        <div className="text-2xl font-bold">{entryConfidence}/100</div>
      </div>
      <div className="space-y-1">
        <div className="text-sm text-muted-foreground">Tier</div>
        <Badge className={getTierColor(tier)}>
          Tier {tier}
        </Badge>
      </div>
    </div>
  );
}

import { AnalyzeResponse } from "@/lib/api";

interface PositionSizingProps {
  position: AnalyzeResponse["position"];
}

export function PositionSizing({ position }: PositionSizingProps) {
  return (
    <div className="space-y-4 pt-6 border-t border-border/50">
      <h3 className="text-lg font-semibold">Position Sizing</h3>
      <div className="grid grid-cols-2 md:grid-cols-4 gap-6">
        <div className="space-y-1">
          <div className="text-sm text-muted-foreground">Units</div>
          <div className="text-xl font-semibold">{position.units}</div>
        </div>
        <div className="space-y-1">
          <div className="text-sm text-muted-foreground">Stop Loss</div>
          <div className="text-xl font-semibold">${position.stop.toFixed(2)}</div>
        </div>
        <div className="space-y-1">
          <div className="text-sm text-muted-foreground">Take Profit (1R)</div>
          <div className="text-xl font-semibold">${position.take_profit_1r.toFixed(2)}</div>
        </div>
        <div className="space-y-1">
          <div className="text-sm text-muted-foreground">Take Profit (2R)</div>
          <div className="text-xl font-semibold">${position.take_profit_1.toFixed(2)}</div>
        </div>
      </div>
      <div className="mt-4 pt-4 border-t border-border/50">
        <div className="text-sm text-muted-foreground">Risk Amount</div>
        <div className="text-2xl font-bold text-yellow-400">${position.risk_amount.toFixed(2)}</div>
      </div>
    </div>
  );
}

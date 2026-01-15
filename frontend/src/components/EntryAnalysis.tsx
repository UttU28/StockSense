import { Badge } from "@/components/ui/badge";
import { CheckCircle2, AlertCircle } from "lucide-react";
import { AnalyzeResponse } from "@/lib/api";

interface EntryAnalysisProps {
  analyzeData: AnalyzeResponse;
}

export function EntryAnalysis({ analyzeData }: EntryAnalysisProps) {
  const { entry_analysis, options_strategy } = analyzeData.analysis.plan;

  return (
    <div className="space-y-3 pt-6 border-t border-border/50">
      <h3 className="text-lg font-semibold">Entry Analysis</h3>
      <div className="space-y-3">
        <div className="flex items-center gap-2">
          {entry_analysis.entry_allowed ? (
            <CheckCircle2 className="w-5 h-5 text-green-400" />
          ) : (
            <AlertCircle className="w-5 h-5 text-red-400" />
          )}
          <span className="font-semibold">
            Entry: {entry_analysis.entry_allowed ? "ALLOWED" : "WAIT"}
          </span>
        </div>
        {entry_analysis.checklist && entry_analysis.checklist.length > 0 && (
          <div>
            <div className="text-sm text-muted-foreground mb-2">Checklist</div>
            <div className="flex flex-wrap gap-2">
              {entry_analysis.checklist.map((item: string, idx: number) => (
                <Badge key={idx} variant="outline" className="text-xs">
                  ✓ {item}
                </Badge>
              ))}
            </div>
          </div>
        )}
        {options_strategy && (
          <div>
            <div className="text-sm text-muted-foreground mb-2">Options Strategy</div>
            <div className="flex items-center gap-2">
              <Badge variant="outline">
                {options_strategy.type || "N/A"}
              </Badge>
              <span className="text-sm text-muted-foreground">
                {options_strategy.dte || "N/A"} DTE
              </span>
              <span className="text-xs text-muted-foreground">
                • {options_strategy.strike_selection || "N/A"}
              </span>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}

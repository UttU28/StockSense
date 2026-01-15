import { motion } from "framer-motion";
import { Search, Loader2 } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Skeleton } from "@/components/ui/skeleton";
import { Badge } from "@/components/ui/badge";
import { ScanResponse, Opportunity } from "@/lib/api";
import { WATCHLISTS } from "@/lib/stocks";

interface ScanTabProps {
  watchlist: string;
  accountSize: number;
  loading: boolean;
  scanData: ScanResponse | null;
  onWatchlistChange: (watchlist: string) => void;
  onAccountSizeChange: (size: number) => void;
  onScan: () => void;
  getBiasColor: (bias: string) => string;
}

export function ScanTab({
  watchlist,
  accountSize,
  loading,
  scanData,
  onWatchlistChange,
  onAccountSizeChange,
  onScan,
  getBiasColor,
}: ScanTabProps) {
  return (
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
                onChange={(e) => onWatchlistChange(e.target.value)}
              />
            </div>
            <div className="w-40 space-y-2">
              <Label htmlFor="scan-account">Account Size ($)</Label>
              <Input
                id="scan-account"
                type="number"
                placeholder="10000"
                value={accountSize}
                onChange={(e) => onAccountSizeChange(Number(e.target.value))}
              />
            </div>
            <Button onClick={onScan} disabled={loading} className="mb-0">
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
              onClick={() => onWatchlistChange(WATCHLISTS.tech.join(","))}
            >
              Tech
            </Button>
            <Button
              variant="outline"
              size="sm"
              onClick={() => onWatchlistChange(WATCHLISTS.finance.join(","))}
            >
              Finance
            </Button>
            <Button
              variant="outline"
              size="sm"
              onClick={() => onWatchlistChange(WATCHLISTS.crypto.join(","))}
            >
              Crypto
            </Button>
            <Button
              variant="outline"
              size="sm"
              onClick={() => onWatchlistChange(WATCHLISTS.all.join(","))}
            >
              All
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
  );
}

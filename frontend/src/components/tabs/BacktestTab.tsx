import { motion } from "framer-motion";
import { BarChart3, Loader2 } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Skeleton } from "@/components/ui/skeleton";
import { Badge } from "@/components/ui/badge";
import { ResponsiveContainer, BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip } from "recharts";
import { BacktestResponse } from "@/lib/api";
import { StockSelector } from "@/components/StockSelector";

interface BacktestTabProps {
  symbol: string;
  accountSize: number;
  days: number;
  loading: boolean;
  backtestData: BacktestResponse | null;
  onSymbolChange: (symbol: string) => void;
  onAccountSizeChange: (size: number) => void;
  onDaysChange: (days: number) => void;
  onBacktest: () => void;
}

export function BacktestTab({
  symbol,
  accountSize,
  days,
  loading,
  backtestData,
  onSymbolChange,
  onAccountSizeChange,
  onDaysChange,
  onBacktest,
}: BacktestTabProps) {
  return (
    <div className="space-y-6">
      <div className="space-y-4">
        <div>
          <h2 className="text-2xl font-bold mb-1">Backtest Strategy</h2>
          <p className="text-sm text-muted-foreground">Test your strategy on historical data</p>
        </div>
        <div className="flex gap-4 items-end">
          <StockSelector symbol={symbol} onSymbolChange={onSymbolChange} id="backtest-symbol" />
          <div className="w-40 space-y-2">
            <Label htmlFor="backtest-account">Account Size ($)</Label>
            <Input
              id="backtest-account"
              type="number"
              placeholder="10000"
              value={accountSize}
              onChange={(e) => onAccountSizeChange(Number(e.target.value))}
            />
          </div>
          <div className="w-32 space-y-2">
            <Label htmlFor="backtest-days">Days</Label>
            <Input
              id="backtest-days"
              type="number"
              placeholder="100"
              value={days}
              onChange={(e) => onDaysChange(Number(e.target.value))}
            />
          </div>
          <Button onClick={onBacktest} disabled={loading} className="mb-0">
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
  );
}

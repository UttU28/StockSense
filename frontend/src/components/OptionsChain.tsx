import { useState } from "react";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { OptionsResponse } from "@/lib/api";

interface OptionsChainProps {
  optionsData: OptionsResponse;
}

export function OptionsChain({ optionsData }: OptionsChainProps) {
  const [selectedExpiration, setSelectedExpiration] = useState<number>(0);

  if (!optionsData.chains || optionsData.chains.length === 0) {
    return null;
  }

  return (
    <div className="space-y-4 pt-6 border-t border-border/50">
      <div className="flex items-center justify-between">
        <h3 className="text-lg font-semibold">Options Chain</h3>
        <Select value={selectedExpiration.toString()} onValueChange={(v) => setSelectedExpiration(Number(v))}>
          <SelectTrigger className="w-48">
            <SelectValue />
          </SelectTrigger>
          <SelectContent>
            {optionsData.chains.map((chain: any, idx: number) => (
              <SelectItem key={idx} value={idx.toString()}>
                {chain.days_to_expiry} Days ({chain.expiration_date})
              </SelectItem>
            ))}
          </SelectContent>
        </Select>
      </div>
      <div className="bg-muted/30 rounded-lg p-4 overflow-x-auto">
        <table className="w-full text-sm">
          <thead>
            <tr className="border-b border-border/50">
              <th className="text-left p-2">Strike</th>
              <th className="text-right p-2">Call</th>
              <th className="text-right p-2">Put</th>
              <th className="text-right p-2">Call IV</th>
              <th className="text-right p-2">Put IV</th>
            </tr>
          </thead>
          <tbody>
            {optionsData.chains[selectedExpiration]?.options.map((opt: any, idx: number) => (
              <tr key={idx} className="border-b border-border/30 hover:bg-muted/50">
                <td className="p-2 font-medium">${opt.strike.toFixed(2)}</td>
                <td className="p-2 text-right">
                  <div className="font-semibold">${opt.call_price.toFixed(2)}</div>
                  <div className="text-xs text-muted-foreground">
                    I: ${opt.call_intrinsic.toFixed(2)} T: ${opt.call_time_value.toFixed(2)}
                  </div>
                </td>
                <td className="p-2 text-right">
                  <div className="font-semibold">${opt.put_price.toFixed(2)}</div>
                  <div className="text-xs text-muted-foreground">
                    I: ${opt.put_intrinsic.toFixed(2)} T: ${opt.put_time_value.toFixed(2)}
                  </div>
                </td>
                <td className="p-2 text-right text-muted-foreground">
                  {opt.moneyness > 1 ? "ITM" : opt.moneyness > 0.95 ? "ATM" : "OTM"}
                </td>
                <td className="p-2 text-right text-muted-foreground">
                  {opt.moneyness < 1 ? "ITM" : opt.moneyness < 1.05 ? "ATM" : "OTM"}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
        <div className="mt-4 text-xs text-muted-foreground">
          <p>Current Price: ${optionsData.current_price.toFixed(2)} | Volatility: {optionsData.chains[selectedExpiration]?.volatility.toFixed(1)}% | Expiration: {optionsData.chains[selectedExpiration]?.expiration_date}</p>
          <p className="mt-1">I = Intrinsic Value, T = Time Value</p>
        </div>
      </div>
    </div>
  );
}

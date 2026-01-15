import { Label } from "@/components/ui/label";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
  SelectGroup,
  SelectLabel,
} from "@/components/ui/select";
import { getStocksByCategory } from "@/lib/stocks";

interface StockSelectorProps {
  symbol: string;
  onSymbolChange: (symbol: string) => void;
  id?: string;
}

export function StockSelector({ symbol, onSymbolChange, id = "stock-selector" }: StockSelectorProps) {
  return (
    <div className="flex-1 space-y-2">
      <Label htmlFor={id}>Stock Symbol</Label>
      <Select value={symbol} onValueChange={onSymbolChange}>
        <SelectTrigger id={id}>
          <SelectValue placeholder="Select a stock" />
        </SelectTrigger>
        <SelectContent className="max-h-[300px]">
          {Object.entries(getStocksByCategory()).map(([category, stocks]) => (
            <SelectGroup key={category}>
              <SelectLabel>{category}</SelectLabel>
              {stocks.map((stock) => (
                <SelectItem key={stock.symbol} value={stock.symbol}>
                  {stock.index}. {stock.symbol} - {stock.name}
                </SelectItem>
              ))}
            </SelectGroup>
          ))}
        </SelectContent>
      </Select>
    </div>
  );
}

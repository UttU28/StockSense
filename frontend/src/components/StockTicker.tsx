import { useEffect, useMemo, useState } from "react";

type TickerItem = { symbol: string; price: string; up: boolean };

const TICKER_SYMBOLS = ["AAPL","MSFT","GOOGL","NVDA","AMZN","META","TSLA","JPM","V","JNJ","UNH","PG","XOM","HD","MA","PFE","DIS","BAC","KO"];
const TICKER_BATCH_URL = `/api/ticker/batch/${TICKER_SYMBOLS.join(",")}`;


export function StockTicker() {
  const [items, setItems] = useState<TickerItem[] | null>(null);

  useEffect(() => {
    let cancelled = false;
    const fetchTickers = async () => {
      try {
        const res = await fetch(TICKER_BATCH_URL);
        if (!res.ok) return;
        const json = await res.json();
        const data = json?.data ?? {};
        if (cancelled) return;
        const list: TickerItem[] = TICKER_SYMBOLS.map((symbol) => {
          const t = data[symbol];
          const price = t?.currentPrice ?? 0;
          const change = t?.change ?? 0;
          return {
            symbol,
            price: price > 0 ? price.toFixed(2) : "—",
            up: change >= 0,
          };
        });
        setItems(list);
      } catch {
        if (!cancelled) setItems(null);
      }
    };
    fetchTickers();
    const interval = setInterval(fetchTickers, 120_000);
    return () => {
      cancelled = true;
      clearInterval(interval);
    };
  }, []);

  const marqueeItems = useMemo(() => {
    if (items && items.length > 0) return [...items, ...items];
    return [
      ...TICKER_SYMBOLS.map((s) => ({ symbol: s, price: "—", up: true })),
      ...TICKER_SYMBOLS.map((s) => ({ symbol: s, price: "—", up: true })),
    ];
  }, [items]);

  return (
    <div className="fixed bottom-0 left-0 right-0 border-t border-border/50 bg-card/60 backdrop-blur-sm overflow-hidden py-3 z-30">
      <div className="max-w-6xl mx-auto">
        <div className="flex w-max marquee-track">
          {marqueeItems.map((item, i) => (
            <div
              key={`${item.symbol}-${i}`}
              className="flex items-center gap-4 shrink-0 px-6 border-r border-border/30 last:border-r-0"
            >
              <span className="font-display font-semibold text-foreground">{item.symbol}</span>
              <span className={item.up ? "text-emerald-500/90" : "text-red-400/90"}>
                ${item.price}
              </span>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}


import { useState, useEffect, useMemo } from "react";
import { motion } from "framer-motion";
import { BarChart3, ScanSearch, Calendar, ArrowRight } from "lucide-react";
import { Link } from "wouter";
import { Button } from "@/components/ui/button";
import { useAuth } from "@/contexts/AuthContext";
import { AppNavbar } from "@/components/AppNavbar";

const TICKER_SYMBOLS = ["AAPL", "MSFT", "GOOGL", "NVDA", "AMZN", "META", "TSLA", "JPM", "V", "JNJ"];
const TICKER_BATCH_URL = `/api/ticker/batch/${TICKER_SYMBOLS.join(",")}`;

type TickerItem = { symbol: string; price: string; up: boolean };

const features = [
  {
    icon: BarChart3,
    title: "AI stock analysis",
    description: "Get full technical reports, trend and levels, and buy/sell signals for any symbol.",
  },
  {
    icon: ScanSearch,
    title: "Market scan",
    description: "Find opportunities across the market with AI-powered screening and filters.",
  },
  {
    icon: Calendar,
    title: "Seasonality",
    description: "Monthly breakdowns and historical patterns to time entries and exits.",
  },
];

export default function Home() {
  const [tickerItems, setTickerItems] = useState<TickerItem[] | null>(null);
  const { user } = useAuth();

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
        setTickerItems(list);
      } catch {
        if (!cancelled) setTickerItems(null);
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
    if (tickerItems && tickerItems.length > 0) return [...tickerItems, ...tickerItems];
    return [...TICKER_SYMBOLS.map((s) => ({ symbol: s, price: "—", up: true })), ...TICKER_SYMBOLS.map((s) => ({ symbol: s, price: "—", up: true }))];
  }, [tickerItems]);

  return (
    <div className="min-h-screen flex flex-col">
      <AppNavbar />

      <div className="flex-1 p-6 md:p-12 lg:p-16 max-w-6xl mx-auto flex flex-col w-full">
        {/* Hero */}
        <motion.section
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.5 }}
          className="flex flex-col items-center text-center pt-12 md:pt-20 pb-16"
        >
          <h1 className="text-4xl md:text-6xl lg:text-7xl font-bold font-display bg-gradient-to-br from-white to-white/70 bg-clip-text text-transparent tracking-tight mb-4">
            Stock Gita
          </h1>
          <p className="text-muted-foreground text-lg md:text-xl max-w-xl mb-10">
            Chat with Stock Gita for reports, signals, and seasonality. Analyze symbols, scan the market, and size risk—all in one place.
          </p>
          <div className="flex flex-wrap items-center justify-center gap-3">
            {user && (
              <Link href="/chat">
                <Button size="lg" className="glow-button gap-2 h-12 px-8 text-base">
                  Open Chat
                  <ArrowRight className="w-4 h-4" />
                </Button>
              </Link>
            )}
            <Link href="/pricing">
              <Button size="lg" variant="outline" className="h-12 px-8 text-base border-border">
                Pricing
              </Button>
            </Link>
            {!user && (
              <Link href="/auth">
                <Button size="lg" variant="outline" className="h-12 px-8 text-base border-border">
                  Log in / Sign up
                </Button>
              </Link>
            )}
          </div>
        </motion.section>

        {/* Feature cards */}
        <motion.section
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ delay: 0.2, duration: 0.5 }}
          className="grid grid-cols-1 md:grid-cols-3 gap-6 pb-20"
        >
          {features.map((feature, i) => (
            <motion.div
              key={feature.title}
              initial={{ opacity: 0, y: 24 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.3 + i * 0.1, duration: 0.4 }}
              whileHover={{ y: -4, transition: { duration: 0.2 } }}
              className="group glass-card rounded-2xl p-6 relative overflow-hidden transition-all duration-300 hover:shadow-primary/10 hover:border-primary/20"
            >
              <div className="absolute top-0 right-0 p-6 opacity-0 group-hover:opacity-100 transition-opacity duration-300 text-primary/10">
                <feature.icon className="w-20 h-20 -mr-6 -mt-6 rotate-12" />
              </div>
              <div className="relative z-10">
                <div className="w-12 h-12 rounded-xl bg-primary/10 border border-primary/20 flex items-center justify-center mb-4 text-primary">
                  <feature.icon className="w-6 h-6" />
                </div>
                <h3 className="text-lg font-bold font-display text-foreground mb-2 group-hover:text-primary transition-colors">
                  {feature.title}
                </h3>
                <p className="text-muted-foreground text-sm leading-relaxed">
                  {feature.description}
                </p>
              </div>
            </motion.div>
          ))}
        </motion.section>

        {/* Bottom CTA */}
        <motion.section
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ delay: 0.6, duration: 0.4 }}
          className="mt-auto pt-8 text-center"
        >
          <p className="text-muted-foreground text-sm mb-6">
            Try: “Analyze AAPL”, “Scan market”, “Seasonality for NVDA”, “Risk 10000 on GOOGL”
          </p>
        </motion.section>
      </div>

      {/* Stock ticker marquee – full width */}
      <div className="w-full border-t border-border/50 bg-card/40 backdrop-blur-sm overflow-hidden py-3">
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

import { motion } from "framer-motion";
import { BarChart3, ScanSearch, Calendar, ArrowRight, DollarSign, User as UserIcon } from "lucide-react";
import { Link } from "wouter";
import { Button } from "@/components/ui/button";
import { useAuth } from "@/contexts/AuthContext";
import { AppNavbar } from "@/components/AppNavbar";
import { StockTicker } from "@/components/StockTicker";
import logoImg from "@/assets/icon.svg";

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
  const { user } = useAuth();

  return (
    <div className="min-h-screen flex flex-col">
      <AppNavbar />

      <div className="flex-1 p-6 md:p-12 lg:p-16 pb-24 max-w-6xl mx-auto flex flex-col w-full">
        {/* Hero */}
        <motion.section
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.5 }}
          className="flex flex-col items-center text-center pt-12 md:pt-20 pb-16"
        >
          <img src={logoImg} alt="Stock Sense" className="h-16 w-16 md:h-20 md:w-20 mb-4 object-contain" />
          <h1 className="text-4xl md:text-6xl lg:text-7xl font-bold font-display text-foreground tracking-tight mb-4">
            Stock Sense
          </h1>
          <p className="text-muted-foreground text-lg md:text-xl max-w-xl mb-10">
            Chat with Stock Sense for reports, signals, and seasonality. Analyze symbols, scan the market, and size risk—all in one place.
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
              <Button size="lg" variant="outline" className="h-12 px-8 text-base border-border gap-2">
                <DollarSign className="w-4 h-4 text-muted-foreground" />
                <span>Pricing</span>
              </Button>
            </Link>
            {!user && (
              <Link href="/auth">
                <Button size="lg" variant="outline" className="h-12 px-8 text-base border-border gap-2">
                  <UserIcon className="w-4 h-4 text-muted-foreground" />
                  <span>Log in / Sign up</span>
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
          className="mt-auto pt-0 text-center"
        >
          <p className="text-muted-foreground text-sm mb-6">
            Try: “Analyze AAPL”, “Scan market”, “Seasonality for NVDA”, “Risk 10000 on GOOGL”
          </p>
        </motion.section>
      </div>

      <StockTicker />
    </div>
  );
}

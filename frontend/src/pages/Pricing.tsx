import { useState } from "react";
import { motion } from "framer-motion";
import { Link, useLocation } from "wouter";
import { Button } from "@/components/ui/button";
import { Check, Coins, ArrowLeft } from "lucide-react";
import { AppNavbar } from "@/components/AppNavbar";
import { StockTicker } from "@/components/StockTicker";
import { useAuth } from "@/contexts/AuthContext";
import { createCheckoutSession } from "@/lib/credits-api";
import { toast } from "@/hooks/use-toast";

const plans = [
  {
    name: "Starter",
    price: 20,
    credits: "150,000",
    perCredit: "7,500",
    description: "One-time credit recharge to get started.",
    features: ["AI analysis & reports", "Market scan", "Seasonality", "Usage dashboard"],
  },
  {
    name: "Pro",
    price: 50,
    credits: "500,000",
    perCredit: "10,000",
    savePercent: 33,
    description: "Better value — more credits per dollar.",
    features: ["Everything in Starter", "~33% more credits per $", "Priority support"],
    recommended: true,
  },
  {
    name: "Growth",
    price: 100,
    credits: "1,400,000",
    perCredit: "14,000",
    savePercent: 87,
    description: "Best value — biggest discount on credits.",
    features: ["Everything in Pro", "~87% more credits per $", "Dedicated support"],
  },
];

export default function Pricing() {
  const { user, idToken } = useAuth();
  const [, setLocation] = useLocation();
  const [loadingTier, setLoadingTier] = useState<string | null>(null);

  const handleBuyNow = async (tier: (typeof plans)[0]) => {
    if (!user || !idToken) {
      setLocation("/auth");
      return;
    }
    const priceCents = tier.price * 100;
    setLoadingTier(tier.name);
    try {
      const { url } = await createCheckoutSession(idToken, priceCents);
      window.location.href = url;
    } catch (e) {
      const msg = e instanceof Error ? e.message : "Checkout failed";
      toast({ title: "Checkout failed", description: msg, variant: "destructive" });
      setLoadingTier(null);
    }
  };

  return (
    <div className="min-h-screen flex flex-col w-full">
      <AppNavbar />

      <div className="flex-1 p-6 md:p-12 lg:p-16 pb-24 max-w-6xl mx-auto flex flex-col w-full">
        <motion.section
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.4 }}
          className="text-center mb-12 md:mb-16"
        >
          <h1 className="text-3xl md:text-5xl font-bold font-display text-foreground tracking-tight mb-3">
            Pricing
          </h1>
          <p className="text-muted-foreground text-lg max-w-xl mx-auto">
            Recharge credits once. More you buy, more you save.
          </p>
        </motion.section>

        <motion.section
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.1, duration: 0.4 }}
          className="mb-12"
        >
          <div className="flex items-center justify-center gap-2 text-muted-foreground text-sm mb-8">
            <Coins className="w-4 h-4" />
            <span>One-time recharge — higher packs get a better rate</span>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            {plans.map((tier, i) => (
              <motion.div
                key={tier.name}
                initial={{ opacity: 0, y: 16 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: 0.15 + i * 0.06, duration: 0.4 }}
                className={`relative rounded-2xl p-5 glass-card border transition-all duration-300 hover:border-primary/20 ${
                  tier.recommended ? "border-primary/40 shadow-lg shadow-primary/10" : "border-border"
                }`}
              >
                {tier.recommended && (
                  <div className="absolute -top-2.5 left-1/2 -translate-x-1/2 px-2.5 py-1 rounded-full bg-primary/20 border border-primary/30 text-primary text-xs font-medium">
                    Recommended
                  </div>
                )}
                <h2 className="text-lg font-bold font-display text-foreground mt-1 mb-0.5">
                  {tier.name}
                </h2>
                {tier.savePercent != null && (
                  <p className="text-xs font-medium text-emerald-500/90 mb-1">
                    Save ~{tier.savePercent}%
                  </p>
                )}
                <p className="text-2xl font-bold text-foreground mb-0.5">
                  ${tier.price}
                  <span className="text-sm font-normal text-muted-foreground"> one-time</span>
                </p>
                <p className="text-sm text-primary font-medium mb-0.5">
                  {tier.credits} credits
                </p>
                <p className="text-xs text-muted-foreground mb-4">
                  {tier.perCredit} credits per $
                </p>
                <p className="text-sm text-muted-foreground mb-4">
                  {tier.description}
                </p>
                <ul className="space-y-2 mb-5">
                  {tier.features.map((f) => (
                    <li key={f} className="flex items-center gap-2 text-sm text-muted-foreground">
                      <Check className="w-3.5 h-3.5 shrink-0 text-emerald-500/80" />
                      {f}
                    </li>
                  ))}
                </ul>
                <Button
                  variant={tier.recommended ? "default" : "outline"}
                  className={tier.recommended ? "w-full glow-button" : "w-full border-border"}
                  size="sm"
                  onClick={() => handleBuyNow(tier)}
                  disabled={!!loadingTier}
                >
                  {loadingTier === tier.name ? "Redirecting…" : user ? "Buy now" : "Sign in to buy"}
                </Button>
              </motion.div>
            ))}
          </div>
        </motion.section>

        <motion.footer
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ delay: 0.3 }}
          className="mt-auto pt-8 pb-4 text-center border-t border-border/50"
        >
          <Link href="/" className="inline-flex items-center justify-center gap-1.5 mt-4 text-sm text-primary hover:underline">
            <ArrowLeft className="w-3.5 h-3.5" />
            <span>Back to home</span>
          </Link>
        </motion.footer>
      </div>
      <StockTicker />
    </div>
  );
}

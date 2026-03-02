import { useState } from "react";
import { motion } from "framer-motion";
import { Link, useLocation } from "wouter";
import { Button } from "@/components/ui/button";
import { Check, ArrowLeft, Target, Brain, KeyRound, Sparkles } from "lucide-react";
import { AppNavbar } from "@/components/AppNavbar";
import { StockTicker } from "@/components/StockTicker";
import { useAuth } from "@/contexts/AuthContext";
import { createCheckoutSession } from "@/lib/credits-api";
import { toast } from "@/hooks/use-toast";

type TierPlan = {
  id: string;
  name: string;
  subtitle: string;
  aliasNames: string[];
  price: number;
  recommended?: boolean;
  whoItsFor: string[];
  deliverables: string[];
  limitations?: string[];
  keyFraming: string;
  upgradePsychology?: string;
  additionalBenefits?: { title: string; items: string[] }[];
};

const tiers: TierPlan[] = [
  {
    id: "tier1",
    name: "Tier 1",
    subtitle: "Stock Bias Engine (Version 1)",
    aliasNames: ["Core Market Engine", "Structured Equity Plan", "Regime-Aware Stock Signals", "Foundation Plan"],
    price: 20,
    whoItsFor: [
      "Swing traders",
      "Equity-only investors",
      "Beginners to intermediate traders",
      "People who don't want complexity",
    ],
    deliverables: [
      "Market regime assessment",
      "Trade bias (Long / Short / Skip)",
      "When to trade / when NOT to trade",
      "Multi-timeframe validation",
      "Calendar alignment filtering",
      "Entry / invalidation levels",
      "Expected trade duration",
    ],
    limitations: [
      "No options strategy access",
      "No advanced strike/expiry modeling",
      "No personalized adaptation",
      "Email-only support",
    ],
    keyFraming: "Structured Equity Execution Without Derivatives Risk",
  },
  {
    id: "tier2",
    name: "Tier 2",
    subtitle: "Options & Advanced Structure (Version 2)",
    aliasNames: [],
    price: 50,
    recommended: true,
    whoItsFor: [
      "Traders ready to use leverage",
      "Options traders",
      "People who want expiry precision",
      "Traders who understand risk modeling",
    ],
    deliverables: [
      "Everything in Tier 1 PLUS:",
      "Options trade eligibility detection",
      "Expiry window modeling",
      "Strike selection logic",
      "Bid/ask quality assessment",
      "Spread suitability",
      "Multi-timeframe alignment engine",
      "Structured options duration logic",
      "Volatility-aware execution filtering",
    ],
    keyFraming: "That's the mental jump.",
    upgradePsychology: "Tier 1: “I know when to trade stocks.” → Tier 2: “I know how to structure leveraged exposure correctly.”",
  },
  {
    id: "tier3",
    name: "Tier 3",
    subtitle: "Personalized Architecture (Version 3)",
    aliasNames: [],
    price: 100,
    whoItsFor: [
      "Advanced traders",
      "High-capital traders",
      "Business owners",
      "People managing serious money",
      "Traders who want personalization",
    ],
    deliverables: [
      "Everything in Tier 2 PLUS:",
      "Personalized Strategy Profile:",
      "Risk tolerance modeling",
      "Short vs long-term focus",
      "Tax preference input",
      "Capital allocation structure",
      "Trade frequency preference",
      "Volatility comfort level",
    ],
    keyFraming: "The system adapts output style to your profile.",
    additionalBenefits: [
      {
        title: "Allocation Modulation",
        items: ["Signals don't change — sizing guidance does. That's sophisticated."],
      },
      {
        title: "Beta Access — Inner circle",
        items: ["Early strategy patches", "New algorithm releases", "Experimental integrations", "Direct feedback loop"],
      },
      {
        title: "24-Hour Direct Access — White-glove",
        items: ["Direct communication", "Priority issue handling", "Strategy clarification", "Feedback integration"],
      },
    ],
  },
];

export default function Pricing() {
  const { user, idToken } = useAuth();
  const [, setLocation] = useLocation();
  const [loadingTier, setLoadingTier] = useState<string | null>(null);

  const handleGetStarted = async (tier: TierPlan) => {
    if (!user || !idToken) {
      setLocation("/auth");
      return;
    }
    const priceCents = tier.price * 100;
    setLoadingTier(tier.id);
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
            Choose the tier that fits your trading style. Structured decisions, not signals. Billed monthly.
          </p>
        </motion.section>

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {tiers.map((tier, i) => (
            <motion.div
              key={tier.id}
              initial={{ opacity: 0, y: 16 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.1 + i * 0.08, duration: 0.4 }}
              className={`relative rounded-2xl border transition-all duration-300 overflow-hidden ${
                tier.recommended
                  ? "border-primary/40 shadow-lg shadow-primary/10 bg-card"
                  : "border-border bg-card/80 hover:border-primary/20"
              }`}
            >
              {tier.recommended && (
                <div className="absolute top-0 left-0 right-0 py-1.5 bg-primary/20 border-b border-primary/30 text-center">
                  <span className="text-xs font-semibold text-primary">Recommended — Mass adoption entry</span>
                </div>
              )}

              <div className={`p-6 ${tier.recommended ? "pt-10" : ""}`}>
                {/* Header */}
                <div className="mb-6">
                  <h2 className="text-xl font-bold font-display text-foreground">
                    {tier.name}
                  </h2>
                  <p className="text-sm font-semibold text-primary mt-0.5">{tier.subtitle}</p>
                  {tier.aliasNames.length > 0 && (
                    <p className="text-xs text-muted-foreground mt-2">
                      Also: {tier.aliasNames.join(" • ")}
                    </p>
                  )}
                  <div className="mt-4 flex items-baseline gap-1">
                    <span className="text-3xl font-bold text-foreground">${tier.price}</span>
                    <span className="text-sm font-medium text-muted-foreground">/ month</span>
                  </div>
                  <p className="text-xs text-muted-foreground mt-1">Billed monthly</p>
                </div>

                {/* Who it's for */}
                <div className="mb-5">
                  <div className="flex items-center gap-2 mb-2">
                    <Target className="w-4 h-4 text-primary" />
                    <h3 className="text-sm font-semibold text-foreground">Who it's for</h3>
                  </div>
                  <ul className="space-y-1">
                    {tier.whoItsFor.map((item) => (
                      <li key={item} className="flex items-center gap-2 text-sm text-muted-foreground">
                        <Check className="w-3 h-3 shrink-0 text-primary/80" />
                        {item}
                      </li>
                    ))}
                  </ul>
                </div>

                {/* What it delivers */}
                <div className="mb-5">
                  <div className="flex items-center gap-2 mb-2">
                    <Brain className="w-4 h-4 text-primary" />
                    <h3 className="text-sm font-semibold text-foreground">
                      {tier.id === "tier1" ? "What it delivers" : tier.id === "tier2" ? "What changes from Tier 1" : "What changes from Tier 2"}
                    </h3>
                  </div>
                  {tier.id === "tier1" && (
                    <p className="text-sm font-medium text-foreground mb-2">Not just "buy/sell signals."</p>
                  )}
                  <ul className="space-y-1">
                    {tier.deliverables.map((item, j) => (
                      <li
                        key={j}
                        className={`flex items-start gap-2 text-sm ${
                          item.endsWith(":") || item.endsWith("PLUS:") ? "font-medium text-foreground mt-1 first:mt-0" : "text-muted-foreground"
                        }`}
                      >
                        <Check className="w-3 h-3 shrink-0 text-primary/80 mt-0.5" />
                        {item}
                      </li>
                    ))}
                  </ul>
                  {tier.id === "tier1" && (
                    <p className="text-xs text-muted-foreground mt-2 pl-5 border-l-2 border-muted">
                      But only for STOCKS. No options logic, expiry modeling, volatility modeling, or options pricing guidance.
                    </p>
                  )}
                  {tier.id === "tier2" && (
                    <p className="text-xs font-medium text-foreground mt-2 italic">This is not just "stocks + options."</p>
                  )}
                </div>

                {/* Tier 1: Limitations */}
                {tier.limitations && tier.limitations.length > 0 && (
                  <div className="mb-5">
                    <p className="text-xs font-medium text-muted-foreground mb-1">Limitation (framed positively)</p>
                    <ul className="space-y-1">
                      {tier.limitations.map((item) => (
                        <li key={item} className="flex items-center gap-2 text-xs text-muted-foreground">
                          <span className="w-1 h-1 rounded-full bg-muted-foreground" />
                          {item}
                        </li>
                      ))}
                    </ul>
                  </div>
                )}

                {/* Tier 2: Upgrade psychology */}
                {tier.upgradePsychology && (
                  <div className="mb-5 p-3 rounded-lg bg-primary/5 border border-primary/20">
                    <p className="text-xs font-medium text-foreground italic">"{tier.upgradePsychology}"</p>
                  </div>
                )}

                {/* Tier 3: Additional benefits */}
                {tier.additionalBenefits && tier.additionalBenefits.length > 0 && (
                  <div className="space-y-4 mb-5">
                    {tier.additionalBenefits.map((benefit) => (
                      <div key={benefit.title}>
                        <div className="flex items-center gap-2 mb-1">
                          <Sparkles className="w-4 h-4 text-primary" />
                          <h4 className="text-sm font-semibold text-foreground">{benefit.title}</h4>
                        </div>
                        <ul className="space-y-1">
                          {benefit.items.map((item) => (
                            <li key={item} className="flex items-center gap-2 text-sm text-muted-foreground pl-6">
                              <Check className="w-3 h-3 shrink-0 text-primary/80" />
                              {item}
                            </li>
                          ))}
                        </ul>
                      </div>
                    ))}
                  </div>
                )}

                {/* Key framing */}
                <div className="mb-6">
                  <div className="flex items-center gap-2 mb-1">
                    <KeyRound className="w-4 h-4 text-primary" />
                    <h3 className="text-sm font-semibold text-foreground">Key framing</h3>
                  </div>
                  <p className="text-sm font-medium text-foreground pl-6">{tier.keyFraming}</p>
                </div>

                {/* CTA */}
                <Button
                  variant={tier.recommended ? "default" : "outline"}
                  className={tier.recommended ? "w-full glow-button" : "w-full border-border"}
                  size="sm"
                  onClick={() => handleGetStarted(tier)}
                  disabled={!!loadingTier}
                >
                  {loadingTier === tier.id
                    ? "Redirecting…"
                    : user
                      ? "Get started"
                      : "Sign in to get started"}
                </Button>
              </div>
            </motion.div>
          ))}
        </div>

        <motion.footer
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ delay: 0.4 }}
          className="mt-12 pt-8 pb-4 text-center border-t border-border/50"
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

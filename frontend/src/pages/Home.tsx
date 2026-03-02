import { motion } from "framer-motion";
import {
  ArrowRight,
  DollarSign,
  User as UserIcon,
  TrendingUp,
  Calendar,
  BarChart3,
  Target,
  Shield,
  X,
  Check,
  MessageSquare,
  LineChart,
} from "lucide-react";
import {
  Accordion,
  AccordionContent,
  AccordionItem,
  AccordionTrigger,
} from "@/components/ui/accordion";
import { Link } from "wouter";
import { Button } from "@/components/ui/button";
import { useAuth } from "@/contexts/AuthContext";
import { AppNavbar } from "@/components/AppNavbar";
import { StockTicker } from "@/components/StockTicker";
import logoImg from "@/assets/icon.svg";

function HeroMockup() {
  return (
    <span className="text-lg font-semibold text-muted-foreground mt-8 pt-4 block">
      {"''BASICALLY AN IMAGE OF THE CHAT BOX AND THE CHART WITH THE INDICATORS''"}
    </span>
  );
}

/* -----------------------------------------------------------------------------
   SECTION 2 ILLUSTRATION — Why most bots fail
   ----------------------------------------------------------------------------- */
function BotsFailIllustration() {
  const failures = [
    { icon: BarChart3, label: "Single timeframe" },
    { icon: X, label: "Indicator crossovers" },
    { icon: Calendar, label: "No macro regime" },
    { icon: Target, label: "Treat breakouts same" },
    { icon: TrendingUp, label: "Overtrade low-vol" },
  ];
  return (
    <motion.div
      initial={{ opacity: 0, scale: 0.95 }}
      whileInView={{ opacity: 1, scale: 1 }}
      viewport={{ once: true }}
      transition={{ duration: 0.4 }}
      className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-5 gap-3"
    >
      {failures.map((f, i) => (
        <div
          key={f.label}
          className="flex flex-col items-center p-4 rounded-xl border border-destructive/30 bg-destructive/5"
        >
          <f.icon className="w-8 h-8 text-destructive/70 mb-2" />
          <span className="text-xs font-medium text-muted-foreground text-center">{f.label}</span>
        </div>
      ))}
    </motion.div>
  );
}

/* -----------------------------------------------------------------------------
   LAYERED FRAMEWORK STACK (Accordion)
   ----------------------------------------------------------------------------- */
const frameworkLayers = [
  {
    num: 1,
    title: "Macro Regime",
    desc: "Presidential Cycle Integration",
    detail:
      "We integrate where we are in the presidential cycle — year 1 vs year 4 behavior differs dramatically. Macro regime sets the top-level bias before any symbol-specific logic runs.",
  },
  {
    num: 2,
    title: "Seasonal Movement Zones",
    desc: "Jan–May / May–Oct / Oct–Jan",
    detail:
      "Markets move differently in compression vs expansion phases. We segment the year into seasonal zones and adjust exposure and aggression accordingly.",
  },
  {
    num: 3,
    title: "Calendar Expansion Windows",
    desc: "Volatility & timing",
    detail:
      "Certain windows (e.g., FOMC, earnings season, Super-6) statistically expand volatility. We know when to lean in vs step back.",
  },
  {
    num: 4,
    title: "Market Index SLI Confirmation",
    desc: "Index alignment",
    detail:
      "Individual symbols must align with broader market structure. If SPY/QQQ SLI disagrees, the signal is downgraded.",
  },
  {
    num: 5,
    title: "Multi-Timeframe Agreement",
    desc: "Weekly, 8D, Monthly",
    detail:
      "Weekly, 8-day, and monthly timeframes must agree on direction. No forcing trades when higher timeframes conflict.",
  },
  {
    num: 6,
    title: "Predictive Criteria Gate",
    desc: "Signal validation",
    detail:
      "Before execution, signals pass through a validation gate. Weak or conflicting criteria = skip, not force.",
  },
  {
    num: 7,
    title: "Bias & Execution Logic",
    desc: "Final decision",
    detail:
      "Long, Short, or Skip. Entry, risk, and target levels. This is where all layers converge into a single, structured decision.",
  },
];

/* -----------------------------------------------------------------------------
   USER OUTPUTS
   ----------------------------------------------------------------------------- */
const userOutputs = [
  "Market Condition Assessment (Bull / Bear / Transition / Sideways)",
  "Trade Bias (Long / Short / Skip)",
  "Confidence Grade",
  "Key Price Levels (Entry / Risk / Target)",
  "Calendar Alignment Status",
  "Earnings Sensitivity Flag",
  "Options Structure Guidance (if applicable)",
  "Expected Trade Duration",
];

/* -----------------------------------------------------------------------------
   SLI COMPONENTS
   ----------------------------------------------------------------------------- */
const sliComponents = [
  "Directional Movement",
  "MACD momentum",
  "StochRSI exhaustion",
  "Bollinger/MA positioning",
];

/* -----------------------------------------------------------------------------
   CALENDAR INTELLIGENCE ITEMS
   ----------------------------------------------------------------------------- */
const calendarFeatures = [
  "Expansion windows",
  "Super-6 behavior",
  "Earnings window volatility filters",
  "Presidential cycle bias modulation",
];

/* -----------------------------------------------------------------------------
   WHAT WE ARE NOT
   ----------------------------------------------------------------------------- */
const notList = [
  "A high-frequency trading bot",
  "Trading every day",
  "Taking low-quality setups",
  "Ignoring compression zones",
  "Overriding macro conflicts",
];

export default function Home() {
  const { user } = useAuth();

  return (
    <div className="min-h-screen flex flex-col">
      <AppNavbar />

      <div className="flex-1 p-6 md:p-12 lg:p-16 pb-24 max-w-5xl mx-auto flex flex-col w-full">
        {/* ========== SECTION 1 — Hero ========== */}
        <motion.section
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.5 }}
          className="flex flex-col items-center text-center pt-8 md:pt-16 pb-16"
        >
          <img src={logoImg} alt="Stock Sense" className="h-14 w-14 md:h-16 md:w-16 mb-4 object-contain" />
          <h1 className="text-3xl md:text-5xl lg:text-6xl font-bold font-display text-foreground tracking-tight mb-4">
            Institutional-Level Market Structure. Simplified.
          </h1>
          <p className="text-muted-foreground text-base md:text-lg max-w-2xl mb-6 space-y-1">
            <span className="block">Multi-timeframe alignment.</span>
            <span className="block">Calendar intelligence.</span>
            <span className="block">Macro regime filtering.</span>
            <span className="block font-medium text-foreground">One structured decision engine.</span>
          </p>
          <div className="flex flex-wrap items-center justify-center gap-3">
            {user && (
              <Link href="/chat">
                <Button size="lg" className="glow-button gap-2 h-12 px-8 text-base">
                  Analyze a Symbol
                  <ArrowRight className="w-4 h-4" />
                </Button>
              </Link>
            )}
            <Link href="/pricing">
              <Button size="lg" variant="outline" className="h-12 px-8 text-base border-border gap-2">
                <DollarSign className="w-4 h-4 text-muted-foreground" />
                View Pricing
              </Button>
            </Link>
            {!user && (
              <Link href="/auth">
                <Button size="lg" variant="outline" className="h-12 px-8 text-base border-border gap-2">
                  <UserIcon className="w-4 h-4 text-muted-foreground" />
                  Log in / Sign up
                </Button>
              </Link>
            )}
          </div>

          <HeroMockup />
        </motion.section>

        {/* ========== SECTION 2 — Why Most Trading Bots Fail ========== */}
        <motion.section
          initial={{ opacity: 0 }}
          whileInView={{ opacity: 1 }}
          viewport={{ once: true }}
          transition={{ duration: 0.5 }}
          className="py-16 md:py-24 border-t border-border"
        >
          <h2 className="text-2xl md:text-4xl font-bold font-display text-foreground text-center mb-6">
            Why Most Trading Bots Fail
          </h2>
          <ul className="space-y-3 mb-10 max-w-2xl mx-auto text-muted-foreground text-center flex flex-col items-center">
            {[
              "They trade every market regime the same way",
              "They ignore seasonal compression zones",
              "They treat all breakouts equally",
              "They lack higher-timeframe confirmation",
              "They overtrade during low-volatility months",
            ].map((item, i) => (
              <li key={i} className="flex items-center justify-center gap-2">
                <X className="w-4 h-4 shrink-0 text-destructive/80" />
                {item}
              </li>
            ))}
          </ul>
          <p className="text-center text-foreground font-medium mb-10">
            Stock Sense was built to solve structural blind spots.
          </p>
          <BotsFailIllustration />
        </motion.section>

        {/* ========== SECTION 3 — Architecture ========== */}
        <motion.section
          initial={{ opacity: 0 }}
          whileInView={{ opacity: 1 }}
          viewport={{ once: true }}
          transition={{ duration: 0.5 }}
          className="py-16 md:py-24 border-t border-border"
        >
          <h2 className="text-2xl md:text-4xl font-bold font-display text-foreground text-center mb-4">
            A Layered Market Decision Framework
          </h2>
          <p className="text-muted-foreground text-center max-w-2xl mx-auto mb-12">
            Trades are only allowed when higher layers agree with lower layers. If macro conflicts with
            signal, signal is downgraded — not forced. That separates us from 95% of retail bots.
          </p>

          <motion.div
            initial={{ opacity: 0, y: 12 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
            transition={{ duration: 0.4 }}
            className="max-w-xl mx-auto"
          >
            <Accordion type="single" collapsible className="space-y-2">
              {frameworkLayers.map((layer) => (
                <AccordionItem
                  key={layer.num}
                  value={`layer-${layer.num}`}
                  className="border-b-0 rounded-xl border border-border bg-card/60 px-4 data-[state=open]:bg-card/80 data-[state=open]:border-primary/20 transition-colors"
                >
                  <AccordionTrigger className="hover:no-underline [&[data-state=open]>svg]:rotate-180">
                    <div className="flex items-start gap-4 text-left">
                      <span className="flex items-center justify-center w-8 h-8 rounded-lg bg-primary/20 text-primary font-bold text-sm shrink-0">
                        {layer.num}
                      </span>
                      <div>
                        <h3 className="font-semibold text-foreground">{layer.title}</h3>
                        <p className="text-sm text-muted-foreground font-normal">{layer.desc}</p>
                      </div>
                    </div>
                  </AccordionTrigger>
                  <AccordionContent>
                    <p className="text-sm text-muted-foreground pl-12">{layer.detail}</p>
                  </AccordionContent>
                </AccordionItem>
              ))}
            </Accordion>
          </motion.div>
        </motion.section>

        {/* ========== SECTION 4 — What Users Get ========== */}
        <motion.section
          initial={{ opacity: 0 }}
          whileInView={{ opacity: 1 }}
          viewport={{ once: true }}
          transition={{ duration: 0.5 }}
          className="py-16 md:py-24 border-t border-border"
        >
          <h2 className="text-2xl md:text-4xl font-bold font-display text-foreground text-center mb-4">
            What You Actually Get
          </h2>
          <p className="text-muted-foreground text-center max-w-2xl mx-auto mb-10">
            For any symbol, you receive:
          </p>
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 max-w-3xl mx-auto">
            {userOutputs.map((item, i) => (
              <div
                key={i}
                className="flex items-center justify-center gap-2 rounded-xl border border-border bg-card/60 px-4 py-3 text-center"
              >
                <Check className="w-5 h-5 shrink-0 text-primary" />
                <span className="text-sm text-foreground">{item}</span>
              </div>
            ))}
          </div>
        </motion.section>

        {/* ========== SECTION 5 — SLI ========== */}
        <motion.section
          initial={{ opacity: 0 }}
          whileInView={{ opacity: 1 }}
          viewport={{ once: true }}
          transition={{ duration: 0.5 }}
          className="py-16 md:py-24 border-t border-border"
        >
          <h2 className="text-2xl md:text-4xl font-bold font-display text-foreground text-center mb-4">
            Straight Line Information (SLI)
          </h2>
          <p className="text-muted-foreground text-center max-w-2xl mx-auto mb-6">
            SLI detects structured directional shifts across:
          </p>
          <div className="flex flex-wrap justify-center gap-2 mb-6">
            {sliComponents.map((c) => (
              <span
                key={c}
                className="px-3 py-1.5 rounded-lg bg-primary/15 border border-primary/30 text-sm font-medium text-foreground"
              >
                {c}
              </span>
            ))}
          </div>
          <p className="text-center text-foreground font-medium max-w-2xl mx-auto">
            A trade is only valid when SLI aligns across multiple timeframes. That's our moat.
          </p>
        </motion.section>

        {/* ========== SECTION 6 — Calendar Intelligence ========== */}
        <motion.section
          initial={{ opacity: 0 }}
          whileInView={{ opacity: 1 }}
          viewport={{ once: true }}
          transition={{ duration: 0.5 }}
          className="py-16 md:py-24 border-t border-border"
        >
          <h2 className="text-2xl md:text-4xl font-bold font-display text-foreground text-center mb-4">
            Calendar Intelligence
          </h2>
          <p className="text-muted-foreground text-center max-w-2xl mx-auto mb-6">
            Very few systems integrate:
          </p>
          <ul className="space-y-2 max-w-md mx-auto mb-8 flex flex-col items-center text-center">
            {calendarFeatures.map((f) => (
              <li key={f} className="flex items-center justify-center gap-2 text-foreground">
                <Calendar className="w-4 h-4 shrink-0 text-primary" />
                {f}
              </li>
            ))}
          </ul>
          <p className="text-center text-foreground font-medium max-w-2xl mx-auto">
            The system knows when markets statistically expand — not just how. That's a powerful
            positioning statement.
          </p>
        </motion.section>

        {/* ========== SECTION 7 — Risk & Transparency ========== */}
        <motion.section
          initial={{ opacity: 0 }}
          whileInView={{ opacity: 1 }}
          viewport={{ once: true }}
          transition={{ duration: 0.5 }}
          className="py-16 md:py-24 border-t border-border"
        >
          <h2 className="text-2xl md:text-4xl font-bold font-display text-foreground text-center mb-4">
            What Stock Sense Is Not
          </h2>
          <p className="text-muted-foreground text-center max-w-2xl mx-auto mb-8">
            Professionals skip trades. Amateurs force trades.
          </p>
          <ul className="space-y-3 max-w-xl mx-auto mb-10 flex flex-col items-center text-center">
            {notList.map((item) => (
              <li key={item} className="flex items-center justify-center gap-2 text-muted-foreground">
                <X className="w-4 h-4 shrink-0 text-muted-foreground" />
                It is not {item}
              </li>
            ))}
          </ul>
          <div className="rounded-2xl border-2 border-primary/40 bg-primary/10 p-6 md:p-8 text-center">
            <Shield className="w-12 h-12 text-primary mx-auto mb-3" />
            <p className="text-lg md:text-xl font-bold font-display text-foreground">
              We believe in quality trades, not quantity trades.
            </p>
          </div>
        </motion.section>

        {/* Bottom CTA */}
        <motion.section
          initial={{ opacity: 0 }}
          whileInView={{ opacity: 1 }}
          viewport={{ once: true }}
          className="mt-12 pt-12 text-center"
        >
          <p className="text-muted-foreground text-sm mb-6">
            Other bots look at one timeframe. Use indicator crossovers. Ignore macro regime. We don't.
          </p>
          {user ? (
            <Link href="/chat">
              <Button size="lg" className="glow-button gap-2">
                Start Analyzing
                <ArrowRight className="w-4 h-4" />
              </Button>
            </Link>
          ) : (
            <Link href="/auth">
              <Button size="lg" className="glow-button gap-2">
                Get Started
                <ArrowRight className="w-4 h-4" />
              </Button>
            </Link>
          )}
        </motion.section>
      </div>

      <StockTicker />
    </div>
  );
}

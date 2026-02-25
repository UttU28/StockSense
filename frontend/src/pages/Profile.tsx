import { useState, useEffect } from "react";
import { Link, useLocation } from "wouter";
import { motion } from "framer-motion";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Card } from "@/components/ui/card";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from "@/components/ui/dialog";
import { Eye, EyeOff, Coins, Receipt, BarChart3, ArrowLeft, Plus, Mail, KeyRound, ChevronDown, ChevronUp, Pencil } from "lucide-react";
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  Tooltip,
  ResponsiveContainer,
  CartesianGrid,
} from "recharts";
import { useAuth } from "@/contexts/AuthContext";
import { AppNavbar } from "@/components/AppNavbar";
import { toast } from "@/hooks/use-toast";
import { getMe, getTransactions, getUsageHistory, type Transaction, type UsageDay } from "@/lib/credits-api";
import logoImg from "@/assets/icon.svg";

export default function Profile() {
  const { user, idToken, loading: authLoading, updatePassword, updateDisplayName } = useAuth();
  const [, setLocation] = useLocation();
  const [currentPassword, setCurrentPassword] = useState("");
  const [newPassword, setNewPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [showPasswords, setShowPasswords] = useState(false);
  const [passwordLoading, setPasswordLoading] = useState(false);
  const [credits, setCredits] = useState<number | null>(null);
  const [transactions, setTransactions] = useState<Transaction[]>([]);
  const [transactionsLoading, setTransactionsLoading] = useState(false);
  const [usagePeriod, setUsagePeriod] = useState<"7d" | "30d">("30d");
  const [usageData, setUsageData] = useState<UsageDay[]>([]);
  const [usageLoading, setUsageLoading] = useState(false);
  const [passwordOpen, setPasswordOpen] = useState(false);
  const [nameOpen, setNameOpen] = useState(false);
  const [nameInput, setNameInput] = useState("");
  const [nameLoading, setNameLoading] = useState(false);
  const [transactionsExpanded, setTransactionsExpanded] = useState(false);

  useEffect(() => {
    if (!authLoading && !user) setLocation("/auth");
  }, [authLoading, user, setLocation]);

  useEffect(() => {
    const search = new URLSearchParams(window.location.search);
    if (search.get("success") === "1") {
      toast({ title: "Payment successful", description: "Your credits have been added." });
      window.history.replaceState({}, "", "/profile");
    }
  }, []);

  useEffect(() => {
    if (!idToken) return;
    getMe(idToken)
      .then((me) => setCredits(me.credits))
      .catch(() => setCredits(0));
  }, [idToken]);

  useEffect(() => {
    if (!idToken) return;
    setTransactionsLoading(true);
    getTransactions(idToken)
      .then(setTransactions)
      .catch(() => setTransactions([]))
      .finally(() => setTransactionsLoading(false));
  }, [idToken]);

  useEffect(() => {
    if (!idToken) return;
    setUsageLoading(true);
    getUsageHistory(idToken, usagePeriod)
      .then(setUsageData)
      .catch(() => setUsageData([]))
      .finally(() => setUsageLoading(false));
  }, [idToken, usagePeriod]);

  const isEmailUser = user?.email && user?.providerData?.some((p) => p.providerId === "password");

  const handleUpdateName = async (e: React.FormEvent) => {
    e.preventDefault();
    const name = nameInput.trim();
    if (!name) {
      toast({ title: "Name required", description: "Please enter a name.", variant: "destructive" });
      return;
    }
    setNameLoading(true);
    try {
      await updateDisplayName(name);
      toast({ title: "Name updated", description: "Your display name has been updated." });
      setNameOpen(false);
      setNameInput("");
    } catch (err: unknown) {
      toast({ title: "Update failed", description: err instanceof Error ? err.message : "Could not update name", variant: "destructive" });
    } finally {
      setNameLoading(false);
    }
  };

  const handleUpdatePassword = async (e: React.FormEvent) => {
    e.preventDefault();
    if (newPassword !== confirmPassword) {
      toast({ title: "Passwords don't match", description: "New password and confirmation must match.", variant: "destructive" });
      return;
    }
    if (newPassword.length < 6) {
      toast({ title: "Password too short", description: "Use at least 6 characters.", variant: "destructive" });
      return;
    }
    setPasswordLoading(true);
    try {
      await updatePassword(currentPassword, newPassword);
      setCurrentPassword("");
      setNewPassword("");
      setConfirmPassword("");
      setPasswordOpen(false);
      toast({ title: "Password updated", description: "Your password has been changed successfully." });
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : "Failed to update password";
      toast({ title: "Update failed", description: msg, variant: "destructive" });
    } finally {
      setPasswordLoading(false);
    }
  };

  if (authLoading) {
    return (
      <div className="min-h-screen flex flex-col">
        <AppNavbar />
        <main className="flex-1 flex items-center justify-center p-6 md:p-12 lg:p-16">
          <div className="flex flex-col items-center gap-3">
            <div className="h-8 w-8 animate-spin rounded-full border-2 border-primary border-t-transparent" />
            <p className="text-muted-foreground text-sm">Loading profile…</p>
          </div>
        </main>
      </div>
    );
  }

  if (!user) return null;

  return (
    <div className="min-h-screen flex flex-col">
      <AppNavbar />
      <main className="flex-1 p-4 sm:p-6 md:p-12 lg:p-16 max-w-6xl mx-auto w-full">
        <motion.div
          initial={{ opacity: 0, y: 16 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.4 }}
          className="space-y-8"
        >
          {/* Profile hero with credits on right */}
          <motion.section
            initial={{ opacity: 0, y: 12 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.1, duration: 0.4 }}
            className="glass-card rounded-2xl p-4 sm:p-6 md:p-8 relative overflow-hidden border-border transition-all duration-300 hover:border-primary/20"
          >
            <div className="absolute top-0 right-0 w-64 h-64 bg-primary/5 rounded-full -translate-y-1/2 translate-x-1/2" />
            <div className="relative flex flex-col sm:flex-row items-center sm:items-center justify-between gap-5 sm:gap-6">
              <div className="flex items-center gap-3 sm:gap-6 w-full sm:w-auto justify-center sm:justify-start">
                <div className="flex-shrink-0 w-14 h-14 sm:w-20 sm:h-20 rounded-xl sm:rounded-2xl bg-primary/10 border border-primary/20 flex items-center justify-center overflow-hidden">
                  <img src={logoImg} alt="" className="w-8 h-8 sm:w-12 sm:h-12 object-contain" />
                </div>
                <div className="text-center sm:text-left min-w-0 flex-1">
                  <div className="flex items-center justify-center sm:justify-start gap-2 flex-wrap">
                    <h1 className="text-xl sm:text-2xl md:text-3xl font-display font-bold text-foreground truncate">
                      {user.displayName || "Member"}
                    </h1>
                    <Dialog open={nameOpen} onOpenChange={(open) => { setNameOpen(open); if (open) setNameInput(user.displayName || ""); }}>
                      <DialogTrigger asChild>
                        <button
                          type="button"
                          className="p-1.5 rounded-lg text-muted-foreground hover:text-foreground hover:bg-muted/50 transition-colors shrink-0"
                          aria-label="Edit name"
                        >
                          <Pencil className="w-4 h-4" />
                        </button>
                      </DialogTrigger>
                      <DialogContent className="sm:max-w-md p-8 glass-card border-border/50 shadow-xl shadow-primary/5 font-sans">
                        <DialogHeader>
                          <div className="flex flex-col items-center gap-3 mb-6">
                            <img src={logoImg} alt="Stock Sense" className="h-12 w-12 object-contain" />
                            <h2 className="font-display font-bold text-2xl sm:text-3xl text-center text-foreground tracking-tight">
                              Stock Sense
                            </h2>
                          </div>
                          <div className="text-center mb-6">
                            <DialogTitle className="font-display font-bold text-xl sm:text-2xl text-foreground tracking-tight">
                              Edit name
                            </DialogTitle>
                            <p className="mt-1.5 text-sm text-muted-foreground font-sans">
                              Update your display name. This will be shown in the navbar and profile.
                            </p>
                          </div>
                        </DialogHeader>
                        <form onSubmit={handleUpdateName} className="space-y-4">
                          <div>
                            <Label htmlFor="display-name" className="font-medium text-foreground">Name</Label>
                            <Input
                              id="display-name"
                              type="text"
                              placeholder="Your name"
                              value={nameInput}
                              onChange={(e) => setNameInput(e.target.value)}
                              className="mt-1.5 transition-all focus:ring-2 focus:ring-primary/20"
                              maxLength={50}
                            />
                          </div>
                          <Button type="submit" disabled={nameLoading} className="w-full glow-button">
                            {nameLoading ? "Saving…" : "Save"}
                          </Button>
                        </form>
                      </DialogContent>
                    </Dialog>
                  </div>
                  <p className="text-muted-foreground mt-0.5 text-sm sm:text-base flex items-center justify-center sm:justify-start gap-2 truncate">
                    <Mail className="w-3.5 h-3.5 sm:w-4 sm:h-4 shrink-0" />
                    <span className="truncate">{user.email || "—"}</span>
                  </p>
                  <p className="text-sm text-muted-foreground/80 mt-1.5 sm:mt-2 flex flex-wrap items-center justify-center sm:justify-start gap-1.5">
                    {isEmailUser ? (
                      <Dialog open={passwordOpen} onOpenChange={setPasswordOpen}>
                          <DialogTrigger asChild>
                            <button
                              type="button"
                              className="inline-flex items-center gap-1.5 text-primary hover:underline font-medium"
                            >
                              <KeyRound className="w-3.5 h-3.5" />
                              Change Password?
                            </button>
                          </DialogTrigger>
                          <DialogContent className="sm:max-w-md p-8 glass-card border-border/50 shadow-xl shadow-primary/5 font-sans">
                        <DialogHeader>
                          {/* Match Auth page: logo + title + heading + description */}
                          <div className="flex flex-col items-center gap-3 mb-6">
                            <img src={logoImg} alt="Stock Sense" className="h-12 w-12 object-contain" />
                            <h2 className="font-display font-bold text-2xl sm:text-3xl text-center text-foreground tracking-tight">
                              Stock Sense
                            </h2>
                          </div>
                          <div className="text-center mb-6">
                            <DialogTitle className="font-display font-bold text-xl sm:text-2xl text-foreground tracking-tight">
                              Change password
                            </DialogTitle>
                            <p className="mt-1.5 text-sm text-muted-foreground font-sans">
                              Update your account password.
                            </p>
                          </div>
                        </DialogHeader>
                        <form onSubmit={handleUpdatePassword} className="space-y-4">
                          <div>
                            <Label htmlFor="current-password" className="font-medium text-foreground">Current password</Label>
                            <div className="relative mt-1.5">
                              <Input
                                id="current-password"
                                type={showPasswords ? "text" : "password"}
                                placeholder="••••••••"
                                value={currentPassword}
                                onChange={(e) => setCurrentPassword(e.target.value)}
                                required
                                className="pr-10 transition-all focus:ring-2 focus:ring-primary/20"
                              />
                              <button
                                type="button"
                                onClick={() => setShowPasswords((p) => !p)}
                                className="absolute right-2 top-1/2 -translate-y-1/2 p-1.5 rounded-md text-muted-foreground hover:text-foreground hover:bg-muted/50 transition-colors"
                                aria-label={showPasswords ? "Hide password" : "Show password"}
                              >
                                {showPasswords ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
                              </button>
                            </div>
                          </div>
                          <div>
                            <Label htmlFor="new-password" className="font-medium text-foreground">New password</Label>
                            <Input
                              id="new-password"
                              type={showPasswords ? "text" : "password"}
                              placeholder="••••••••"
                              value={newPassword}
                              onChange={(e) => setNewPassword(e.target.value)}
                              minLength={6}
                              className="mt-1.5 transition-all focus:ring-2 focus:ring-primary/20"
                            />
                          </div>
                          <div>
                            <Label htmlFor="confirm-password" className="font-medium text-foreground">Confirm new password</Label>
                            <Input
                              id="confirm-password"
                              type={showPasswords ? "text" : "password"}
                              placeholder="••••••••"
                              value={confirmPassword}
                              onChange={(e) => setConfirmPassword(e.target.value)}
                              minLength={6}
                              className="mt-1.5 transition-all focus:ring-2 focus:ring-primary/20"
                            />
                          </div>
                          <Button type="submit" disabled={passwordLoading} className="w-full glow-button">
                            {passwordLoading ? "Updating…" : "Update password"}
                          </Button>
                        </form>
                          </DialogContent>
                        </Dialog>
                    ) : (
                      "You signed in with Google. Password changes aren't available for Google accounts."
                    )}
                  </p>
                </div>
              </div>
              <div className="flex flex-col items-center sm:items-end gap-2 shrink-0 w-full sm:w-auto pt-2 sm:pt-0 border-t border-border/50 sm:border-t-0 sm:border-none">
                <div className="flex items-center gap-2">
                  <Coins className="w-5 h-5 text-primary shrink-0" />
                  <span className="text-xl sm:text-2xl md:text-3xl font-bold text-primary">
                    {credits !== null ? credits.toLocaleString() : "—"}
                  </span>
                  <span className="text-sm text-muted-foreground">credits</span>
                </div>
                <Link href="/pricing" className="w-full sm:w-auto">
                  <Button size="sm" className="glow-button gap-2 w-full sm:w-auto">
                    <Plus className="w-4 h-4" />
                    Buy more
                  </Button>
                </Link>
              </div>
            </div>
          </motion.section>

          {/* Usage chart & Transactions side by side */}
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 items-start">
            <motion.div
              initial={{ opacity: 0, y: 12 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.2, duration: 0.4 }}
            >
              <Card className="glass-card rounded-2xl p-6 border-border transition-all duration-300 hover:border-primary/20">
                <div className="flex items-center justify-between mb-4">
                  <div className="flex items-center gap-3">
                    <div className="w-10 h-10 rounded-xl bg-muted/60 flex items-center justify-center">
                      <BarChart3 className="w-5 h-5 text-muted-foreground" />
                    </div>
                    <div>
                      <h2 className="text-lg font-display font-semibold text-foreground">Usage</h2>
                      <p className="text-xs text-muted-foreground">Credits used over time</p>
                    </div>
                  </div>
                  <div className="flex gap-1.5">
                    <Button
                      variant={usagePeriod === "7d" ? "default" : "ghost"}
                      size="sm"
                      onClick={() => setUsagePeriod("7d")}
                      className={usagePeriod === "7d" ? "glow-button h-8" : "h-8"}
                    >
                      7d
                    </Button>
                    <Button
                      variant={usagePeriod === "30d" ? "default" : "ghost"}
                      size="sm"
                      onClick={() => setUsagePeriod("30d")}
                      className={usagePeriod === "30d" ? "glow-button h-8" : "h-8"}
                    >
                      30d
                    </Button>
                  </div>
                </div>
                {usageLoading ? (
                  <div className="h-48 flex items-center justify-center">
                    <div className="h-6 w-6 animate-spin rounded-full border-2 border-primary border-t-transparent" />
                  </div>
                ) : usageData.length === 0 ? (
                  <div className="h-48 flex items-center justify-center rounded-xl bg-muted/30 border border-dashed border-border">
                    <p className="text-sm text-muted-foreground">No usage in this period</p>
                  </div>
                ) : (
                  <div className="h-48 w-full">
                    <ResponsiveContainer width="100%" height="100%">
                      <BarChart data={usageData} margin={{ top: 8, right: 8, left: 0, bottom: 0 }}>
                        <CartesianGrid strokeDasharray="3 3" className="stroke-muted/40" vertical={false} />
                        <XAxis
                          dataKey="date"
                          tick={{ fontSize: 10, fill: "hsl(var(--muted-foreground))" }}
                          tickFormatter={(v) => (v ? new Date(v).toLocaleDateString(undefined, { month: "short", day: "numeric" }) : "")}
                        />
                        <YAxis
                          tick={{ fontSize: 10, fill: "hsl(var(--muted-foreground))" }}
                          allowDecimals={false}
                          width={28}
                        />
                        <Tooltip
                          contentStyle={{
                            backgroundColor: "hsl(var(--card))",
                            border: "1px solid hsl(var(--border))",
                            borderRadius: "10px",
                            boxShadow: "0 4px 12px rgba(0,0,0,0.1)",
                          }}
                          labelFormatter={(v) => (v ? new Date(v).toLocaleDateString() : "")}
                          formatter={(value: number) => [`${value.toLocaleString()} credits`, "Used"]}
                        />
                        <Bar dataKey="creditsUsed" fill="hsl(var(--primary))" radius={[6, 6, 0, 0]} name="Credits used" />
                      </BarChart>
                    </ResponsiveContainer>
                  </div>
                )}
              </Card>
            </motion.div>
            <motion.div
              initial={{ opacity: 0, y: 12 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.3, duration: 0.4 }}
            >
              <Card className="glass-card rounded-2xl p-6 border-border transition-all duration-300 hover:border-primary/20">
                <div className="flex items-center gap-3 mb-5">
                  <div className="w-10 h-10 rounded-xl bg-muted/60 flex items-center justify-center">
                    <Receipt className="w-5 h-5 text-muted-foreground" />
                  </div>
                  <h2 className="text-lg font-display font-semibold text-foreground">Past transactions</h2>
                </div>
                {transactionsLoading ? (
                  <div className="py-8 flex justify-center">
                    <div className="h-6 w-6 animate-spin rounded-full border-2 border-primary border-t-transparent" />
                  </div>
                ) : transactions.length === 0 ? (
                  <div className="py-8 rounded-xl bg-muted/20 border border-dashed border-border text-center">
                    <p className="text-sm text-muted-foreground">No payments yet</p>
                    <Link href="/pricing">
                      <Button variant="ghost" size="sm" className="mt-2 text-primary hover:text-primary/90">
                        View pricing →
                      </Button>
                    </Link>
                  </div>
                ) : (
                  <>
                    <ul className="space-y-0 divide-y divide-border/50">
                      {(transactionsExpanded ? transactions : transactions.slice(0, 4)).map((tx) => (
                        <li
                          key={tx.id}
                          className="flex items-center justify-between py-3 first:pt-0 text-sm hover:bg-muted/30 -mx-2 px-2 rounded-lg transition-colors"
                        >
                          <span className="text-foreground font-medium">
                            ${(tx.amountCents / 100).toFixed(2)}
                          </span>
                          <span className="text-muted-foreground">
                            {tx.credits.toLocaleString()} credits
                          </span>
                          <span className="text-muted-foreground text-xs">
                            {tx.createdAt ? new Date(tx.createdAt).toLocaleDateString() : "—"}
                          </span>
                        </li>
                      ))}
                    </ul>
                    {transactions.length > 4 && (
                      <button
                        type="button"
                        onClick={() => setTransactionsExpanded((e) => !e)}
                        className="mt-3 w-full py-2 flex items-center justify-center gap-1.5 text-sm text-primary hover:underline font-medium"
                      >
                        {transactionsExpanded ? (
                          <>
                            <ChevronUp className="w-4 h-4" />
                            Show less
                          </>
                        ) : (
                          <>
                            <ChevronDown className="w-4 h-4" />
                            {transactions.length - 4} more
                          </>
                        )}
                      </button>
                    )}
                  </>
                )}
              </Card>
            </motion.div>
          </div>

          {/* Back link - matches Pricing footer */}
          <motion.footer
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            transition={{ delay: 0.4 }}
            className="mt-auto pt-8 pb-4 text-center border-t border-border/50"
          >
            <Link href="/" className="inline-flex items-center justify-center gap-1.5 mt-4 text-sm text-primary hover:underline">
              <ArrowLeft className="w-3.5 h-3.5" />
              <span>Back to home</span>
            </Link>
          </motion.footer>
        </motion.div>
      </main>
    </div>
  );
}

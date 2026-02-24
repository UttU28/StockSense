import { useState, useEffect } from "react";
import { Link, useLocation } from "wouter";
import { motion } from "framer-motion";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Card } from "@/components/ui/card";
import { Eye, EyeOff, User, Coins, Receipt, BarChart3, ArrowLeft, Plus } from "lucide-react";
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

export default function Profile() {
  const { user, idToken, loading: authLoading, updatePassword } = useAuth();
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
        <main className="flex-1 flex items-center justify-center p-6 md:p-12 lg:p-16 max-w-6xl mx-auto w-full">
          <p className="text-muted-foreground">Loading…</p>
        </main>
      </div>
    );
  }

  if (!user) return null;

  return (
    <div className="min-h-screen flex flex-col">
      <AppNavbar />
      <main className="flex-1 p-6 md:p-12 lg:p-16 max-w-6xl mx-auto w-full">
        <motion.div
          initial={{ opacity: 0, y: 12 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.3 }}
          className="space-y-8 max-w-2xl mx-auto"
        >
          <div>
            <h1 className="text-2xl font-display font-bold text-foreground flex items-center gap-2">
              <User className="w-7 h-7" />
              Profile
            </h1>
            <p className="text-muted-foreground mt-1">View your details and manage your account.</p>
          </div>

          <Card className="p-6 border-border bg-card">
            <h2 className="text-lg font-semibold text-foreground mb-4">Account details</h2>
            <dl className="space-y-3">
              <div>
                <dt className="text-sm text-muted-foreground">Display name</dt>
                <dd className="text-foreground font-medium">{user.displayName || "—"}</dd>
              </div>
              <div>
                <dt className="text-sm text-muted-foreground">Email</dt>
                <dd className="text-foreground font-medium">{user.email || "—"}</dd>
              </div>
            </dl>
          </Card>

          <Card className="p-6 border-border bg-card">
            <h2 className="text-lg font-semibold text-foreground mb-4 flex items-center gap-2">
              <Coins className="w-5 h-5 text-primary" />
              Credits
            </h2>
            <p className="text-2xl font-bold text-primary mb-4">
              {credits !== null ? credits.toLocaleString() : "—"} <span className="text-sm font-normal text-muted-foreground">available</span>
            </p>
            <Link href="/pricing">
              <Button size="sm" className="gap-2">
                <Plus className="w-4 h-4" />
                <span>Buy more credits</span>
              </Button>
            </Link>
          </Card>

          <Card className="p-6 border-border bg-card">
            <h2 className="text-lg font-semibold text-foreground mb-4 flex items-center gap-2">
              <BarChart3 className="w-5 h-5 text-muted-foreground" />
              Credits used over time
            </h2>
            <div className="flex gap-2 mb-4">
              <Button
                variant={usagePeriod === "7d" ? "default" : "outline"}
                size="sm"
                onClick={() => setUsagePeriod("7d")}
                className="border-border"
              >
                7 days
              </Button>
              <Button
                variant={usagePeriod === "30d" ? "default" : "outline"}
                size="sm"
                onClick={() => setUsagePeriod("30d")}
                className="border-border"
              >
                30 days
              </Button>
            </div>
            {usageLoading ? (
              <p className="text-muted-foreground text-sm">Loading…</p>
            ) : usageData.length === 0 ? (
              <p className="text-muted-foreground text-sm">No usage in this period.</p>
            ) : (
              <div className="h-64 w-full">
                <ResponsiveContainer width="100%" height="100%">
                  <BarChart data={usageData} margin={{ top: 8, right: 8, left: 0, bottom: 0 }}>
                    <CartesianGrid strokeDasharray="3 3" className="stroke-muted/50" />
                    <XAxis
                      dataKey="date"
                      tick={{ fontSize: 11, fill: "hsl(var(--muted-foreground))" }}
                      tickFormatter={(v) => (v ? new Date(v).toLocaleDateString(undefined, { month: "short", day: "numeric" }) : "")}
                    />
                    <YAxis
                      tick={{ fontSize: 11, fill: "hsl(var(--muted-foreground))" }}
                      allowDecimals={false}
                    />
                    <Tooltip
                      contentStyle={{ backgroundColor: "hsl(var(--card))", border: "1px solid hsl(var(--border))", borderRadius: "8px" }}
                      labelFormatter={(v) => (v ? new Date(v).toLocaleDateString() : "")}
                      formatter={(value: number) => [`${value.toLocaleString()} credits`, "Used"]}
                    />
                    <Bar dataKey="creditsUsed" fill="hsl(var(--primary))" radius={[4, 4, 0, 0]} name="Credits used" />
                  </BarChart>
                </ResponsiveContainer>
              </div>
            )}
          </Card>

          <Card className="p-6 border-border bg-card">
            <h2 className="text-lg font-semibold text-foreground mb-4 flex items-center gap-2">
              <Receipt className="w-5 h-5 text-muted-foreground" />
              Past transactions
            </h2>
            {transactionsLoading ? (
              <p className="text-muted-foreground text-sm">Loading…</p>
            ) : transactions.length === 0 ? (
              <p className="text-muted-foreground text-sm">No payments yet.</p>
            ) : (
              <ul className="space-y-2">
                {transactions.map((tx) => (
                  <li key={tx.id} className="flex items-center justify-between py-2 border-b border-border/50 last:border-0 text-sm">
                    <span className="text-muted-foreground">
                      ${(tx.amountCents / 100).toFixed(2)} · {tx.credits.toLocaleString()} credits
                    </span>
                    <span className="text-muted-foreground">
                      {tx.createdAt ? new Date(tx.createdAt).toLocaleDateString() : "—"}
                    </span>
                  </li>
                ))}
              </ul>
            )}
          </Card>

          {isEmailUser ? (
            <Card className="p-6 border-border bg-card">
              <h2 className="text-lg font-semibold text-foreground mb-4">Change password</h2>
              <form onSubmit={handleUpdatePassword} className="space-y-4">
                <div>
                  <Label htmlFor="current-password" className="text-foreground">Current password</Label>
                  <div className="relative mt-1.5">
                    <Input
                      id="current-password"
                      type={showPasswords ? "text" : "password"}
                      placeholder="••••••••"
                      value={currentPassword}
                      onChange={(e) => setCurrentPassword(e.target.value)}
                      required
                      className="pr-10"
                    />
                    <button
                      type="button"
                      onClick={() => setShowPasswords((p) => !p)}
                      className="absolute right-2 top-1/2 -translate-y-1/2 p-1.5 rounded-md text-muted-foreground hover:text-foreground"
                      aria-label={showPasswords ? "Hide password" : "Show password"}
                    >
                      {showPasswords ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
                    </button>
                  </div>
                </div>
                <div>
                  <Label htmlFor="new-password" className="text-foreground">New password</Label>
                  <Input
                    id="new-password"
                    type={showPasswords ? "text" : "password"}
                    placeholder="••••••••"
                    value={newPassword}
                    onChange={(e) => setNewPassword(e.target.value)}
                    minLength={6}
                    className="mt-1.5"
                  />
                </div>
                <div>
                  <Label htmlFor="confirm-password" className="text-foreground">Confirm new password</Label>
                  <Input
                    id="confirm-password"
                    type={showPasswords ? "text" : "password"}
                    placeholder="••••••••"
                    value={confirmPassword}
                    onChange={(e) => setConfirmPassword(e.target.value)}
                    minLength={6}
                    className="mt-1.5"
                  />
                </div>
                <Button type="submit" disabled={passwordLoading}>
                  {passwordLoading ? "Updating…" : "Update password"}
                </Button>
              </form>
            </Card>
          ) : (
            <Card className="p-6 border-border bg-card">
              <p className="text-muted-foreground text-sm">
                You signed in with Google. Password change is only available for accounts that use email and password.
              </p>
            </Card>
          )}

          <div className="pt-4">
            <Link href="/">
              <Button variant="outline" className="border-border gap-2">
                <ArrowLeft className="w-4 h-4" />
                <span>Back to Home</span>
              </Button>
            </Link>
          </div>
        </motion.div>
      </main>
    </div>
  );
}

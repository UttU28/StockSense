import { useState } from "react";
import { useLocation } from "wouter";
import { motion, AnimatePresence } from "framer-motion";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Card } from "@/components/ui/card";
import { Eye, EyeOff, Chrome } from "lucide-react";
import { useAuth } from "@/contexts/AuthContext";
import { toast } from "@/hooks/use-toast";
import { AppNavbar } from "@/components/AppNavbar";

type Mode = "login" | "signup";

const formVariants = {
  initial: { opacity: 0, y: 12 },
  animate: { opacity: 1, y: 0 },
  exit: { opacity: 0, y: -8 },
};

export default function Auth() {
  const [mode, setMode] = useState<Mode>("login");
  const [name, setName] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);
  const [showPassword, setShowPassword] = useState(false);
  const { signUp, signIn, signInWithGoogle } = useAuth();
  const [, setLocation] = useLocation();

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError("");
    setLoading(true);
    try {
      if (mode === "signup") {
        await signUp(name, email, password);
      } else {
        await signIn(email, password);
      }
      setLocation("/");
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : mode === "signup" ? "Sign up failed" : "Login failed";
      setError(msg);
    } finally {
      setLoading(false);
    }
  };

  const handleGoogle = async () => {
    setError("");
    setLoading(true);
    try {
      await signInWithGoogle();
      setLocation("/");
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : "Google sign-in failed";
      setError(msg);
      toast({ title: "Google sign-in failed", description: msg, variant: "destructive" });
    } finally {
      setLoading(false);
    }
  };

  const switchMode = () => {
    setMode((m) => (m === "login" ? "signup" : "login"));
    setError("");
  };

  return (
    <div className="min-h-screen flex flex-col">
      <AppNavbar />

      <main className="flex-1 flex items-center justify-center p-6 md:p-12 lg:p-16">
        <div className="w-full max-w-6xl mx-auto flex justify-center">
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.4 }}
            className="w-full max-w-md relative"
          >
          <Card className="p-8 glass-card border-border/50 shadow-xl shadow-primary/5">
            {/* Stock Sense title at top of card */}
            <h2 className="font-display font-bold text-2xl sm:text-3xl text-center text-foreground tracking-tight mb-6">
              Stock Sense
            </h2>
            {/* Title for selected service */}
            <div className="text-center mb-6">
              <AnimatePresence mode="wait">
                <motion.h1
                  key={mode}
                  initial={{ opacity: 0, y: -6 }}
                  animate={{ opacity: 1, y: 0 }}
                  exit={{ opacity: 0, y: 6 }}
                  transition={{ duration: 0.2 }}
                  className="font-display font-bold text-xl sm:text-2xl text-foreground tracking-tight"
                >
                  {mode === "login" ? "Log in to your account" : "Create your account"}
                </motion.h1>
              </AnimatePresence>
              <p className="mt-1.5 text-sm text-muted-foreground font-sans">
                {mode === "login" ? "Enter your email and password to continue." : "Sign up with your name, email and password."}
              </p>
            </div>

            <AnimatePresence mode="wait">
              {mode === "login" ? (
                <motion.form
                  key="login"
                  variants={formVariants}
                  initial="initial"
                  animate="animate"
                  exit="exit"
                  transition={{ duration: 0.25 }}
                  onSubmit={handleSubmit}
                  className="space-y-4 font-sans"
                >
                  <div>
                    <Label htmlFor="auth-email" className="font-medium text-foreground">Email</Label>
                    <Input
                      id="auth-email"
                      type="email"
                      placeholder="you@example.com"
                      value={email}
                      onChange={(e) => setEmail(e.target.value)}
                      required
                      className="mt-1.5 transition-all focus:ring-2 focus:ring-primary/20"
                    />
                  </div>
                  <div>
                    <Label htmlFor="auth-password" className="font-medium text-foreground">Password</Label>
                    <div className="relative mt-1.5">
                      <Input
                        id="auth-password"
                        type={showPassword ? "text" : "password"}
                        placeholder="••••••••"
                        value={password}
                        onChange={(e) => setPassword(e.target.value)}
                        required
                        className="pr-10 transition-all focus:ring-2 focus:ring-primary/20"
                      />
                      <button
                        type="button"
                        onClick={() => setShowPassword((p) => !p)}
                        className="absolute right-2 top-1/2 -translate-y-1/2 p-1.5 rounded-md text-muted-foreground hover:text-foreground hover:bg-muted/50 transition-colors"
                        aria-label={showPassword ? "Hide password" : "Show password"}
                      >
                        {showPassword ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
                      </button>
                    </div>
                  </div>
                  {error && (
                    <motion.p
                      initial={{ opacity: 0 }}
                      animate={{ opacity: 1 }}
                      className="text-sm text-destructive"
                    >
                      {error}
                    </motion.p>
                  )}
                  <Button type="submit" className="w-full glow-button" disabled={loading}>
                    {loading ? "Signing in…" : "Sign in"}
                  </Button>
                </motion.form>
              ) : (
                <motion.form
                  key="signup"
                  variants={formVariants}
                  initial="initial"
                  animate="animate"
                  exit="exit"
                  transition={{ duration: 0.25 }}
                  onSubmit={handleSubmit}
                  className="space-y-4 font-sans"
                >
                  <div>
                    <Label htmlFor="auth-name" className="font-medium text-foreground">Name</Label>
                    <Input
                      id="auth-name"
                      type="text"
                      placeholder="Your name"
                      value={name}
                      onChange={(e) => setName(e.target.value)}
                      required
                      className="mt-1.5 transition-all focus:ring-2 focus:ring-primary/20"
                    />
                  </div>
                  <div>
                    <Label htmlFor="auth-email-up" className="font-medium text-foreground">Email</Label>
                    <Input
                      id="auth-email-up"
                      type="email"
                      placeholder="you@example.com"
                      value={email}
                      onChange={(e) => setEmail(e.target.value)}
                      required
                      className="mt-1.5 transition-all focus:ring-2 focus:ring-primary/20"
                    />
                  </div>
                  <div>
                    <Label htmlFor="auth-password-up" className="font-medium text-foreground">Password</Label>
                    <div className="relative mt-1.5">
                      <Input
                        id="auth-password-up"
                        type={showPassword ? "text" : "password"}
                        placeholder="••••••••"
                        value={password}
                        onChange={(e) => setPassword(e.target.value)}
                        required
                        minLength={6}
                        className="pr-10 transition-all focus:ring-2 focus:ring-primary/20"
                      />
                      <button
                        type="button"
                        onClick={() => setShowPassword((p) => !p)}
                        className="absolute right-2 top-1/2 -translate-y-1/2 p-1.5 rounded-md text-muted-foreground hover:text-foreground hover:bg-muted/50 transition-colors"
                        aria-label={showPassword ? "Hide password" : "Show password"}
                      >
                        {showPassword ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
                      </button>
                    </div>
                  </div>
                  {error && (
                    <motion.p
                      initial={{ opacity: 0 }}
                      animate={{ opacity: 1 }}
                      className="text-sm text-destructive"
                    >
                      {error}
                    </motion.p>
                  )}
                  <Button type="submit" className="w-full glow-button" disabled={loading}>
                    {loading ? "Creating account…" : "Create account"}
                  </Button>
                </motion.form>
              )}
            </AnimatePresence>

            <div className="relative my-6">
              <span className="absolute inset-0 flex items-center">
                <span className="w-full border-t border-border/50" />
              </span>
              <span className="relative flex justify-center text-xs font-medium uppercase tracking-wider text-muted-foreground bg-card px-2 font-sans">
                Or continue with
              </span>
            </div>

            <Button
              type="button"
              variant="outline"
              className="w-full border-border hover:bg-muted/50 flex items-center justify-center gap-2"
              onClick={handleGoogle}
              disabled={loading}
            >
              <Chrome className="w-4 h-4" />
              <span>Google</span>
            </Button>

            <p className="mt-6 text-center text-sm text-muted-foreground font-sans">
              {mode === "login" ? "Don't have an account?" : "Already have an account?"}{" "}
              <button
                type="button"
                onClick={switchMode}
                className="text-primary hover:underline font-medium"
              >
                {mode === "login" ? "Sign up" : "Log in"}
              </button>
            </p>
          </Card>
          </motion.div>
        </div>
      </main>
    </div>
  );
}

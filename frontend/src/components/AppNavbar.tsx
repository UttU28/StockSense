import { Link, useLocation } from "wouter";
import { Home, MessageCircle, Menu, Moon, SunMedium, User, LogOut, DollarSign } from "lucide-react";
import logoImg from "@/assets/icon.svg";
import { Button } from "@/components/ui/button";
import { Sheet, SheetContent, SheetTrigger, SheetClose } from "@/components/ui/sheet";
import { useAuth } from "@/contexts/AuthContext";
import { useEffect, useState } from "react";

export function AppNavbar({ fixed = false }: { fixed?: boolean }) {
  const { user, loading: authLoading, signOut } = useAuth();
  const [location, setLocation] = useLocation();
  const [theme, setTheme] = useState<"light" | "dark">("light");
  const [mobileOpen, setMobileOpen] = useState(false);

  useEffect(() => {
    const current = (document.documentElement.getAttribute("data-theme") as "light" | "dark" | null) ?? "light";
    setTheme(current);
  }, []);

  const toggleTheme = () => {
    const next: "light" | "dark" = theme === "dark" ? "light" : "dark";
    setTheme(next);
    document.documentElement.setAttribute("data-theme", next);
    localStorage.setItem("theme", next);
  };

  const handleLogout = async () => {
    await signOut();
    setLocation("/");
  };

  return (
    <header className={`${fixed ? "fixed top-0 left-0 right-0" : "sticky top-0"} z-50 flex-none border-b border-border bg-card/80 backdrop-blur-sm`}>
      <div className="w-full px-4 sm:px-6 lg:px-8">
        <div className="flex items-center justify-between h-14">
          <div className="flex items-center gap-3 sm:gap-6">
            <Link href="/" className="flex items-center gap-2 text-foreground hover:text-primary transition-colors shrink-0">
              <img src={logoImg} alt="Stock Sense" className="h-8 w-8 object-contain" />
              <span className="font-display font-bold text-lg">Stock Sense</span>
            </Link>
            {/* Desktop nav links */}
            <nav className="hidden md:flex items-center gap-6">
              <Link href="/" className={`text-sm font-medium ${location === "/" ? "text-primary" : "text-muted-foreground hover:text-foreground"}`}>
                Home
              </Link>
              <Link href="/pricing" className={`text-sm font-medium ${location === "/pricing" ? "text-primary" : "text-muted-foreground hover:text-foreground"}`}>
                Pricing
              </Link>
              {user && (
                <>
                  <Link href="/chat" className={`text-sm font-medium ${location === "/chat" ? "text-primary" : "text-muted-foreground hover:text-foreground"}`}>
                    Chat
                  </Link>
                  <Link href="/profile" className={`text-sm font-medium ${location === "/profile" ? "text-primary" : "text-muted-foreground hover:text-foreground"}`}>
                    Profile
                  </Link>
                </>
              )}
            </nav>
          </div>
          <div className="flex items-center gap-2">
            {/* Desktop auth area */}
            {!authLoading && (
              user ? (
                <div className="hidden sm:flex items-center gap-4">
                  <Link
                    href="/profile"
                    className="flex items-center gap-1.5 text-sm font-bold text-foreground hover:text-primary transition-colors truncate max-w-[140px] sm:max-w-[200px]"
                    title={user.email ?? undefined}
                  >
                    <User className="w-4 h-4 shrink-0" />
                    {user.displayName || user.email || "User"}
                  </Link>
                  <button
                    type="button"
                    onClick={handleLogout}
                    className="flex items-center gap-1.5 text-sm font-medium text-destructive hover:text-destructive/80 transition-colors"
                  >
                    <LogOut className="w-4 h-4" />
                    <span className="hidden sm:inline">Log out</span>
                  </button>
                </div>
              ) : (
                <Link href="/auth" className="hidden sm:inline-flex">
                  <Button size="sm" className="h-9">Log in / Sign up</Button>
                </Link>
              )
            )}
            <Button
              type="button"
              variant="ghost"
              size="icon"
              className="h-9 w-9 rounded-lg hover:bg-muted/50 transition-colors focus-visible:ring-0 focus-visible:ring-offset-0"
              onClick={toggleTheme}
              aria-label={theme === "dark" ? "Switch to light theme" : "Switch to dark theme"}
            >
              {theme === "dark" ? (
                <SunMedium className="h-4 w-4 text-foreground" />
              ) : (
                <Moon className="h-4 w-4 text-foreground" />
              )}
            </Button>
            {/* Mobile menu */}
            <Sheet open={mobileOpen} onOpenChange={setMobileOpen}>
              <SheetTrigger asChild>
                <Button
                  type="button"
                  variant="ghost"
                  size="icon"
                  className="md:hidden h-8 w-8 rounded-full border border-border/60"
                  aria-label="Open navigation menu"
                >
                  <Menu className="h-4 w-4" />
                </Button>
              </SheetTrigger>
              <SheetContent side="top" className="w-full max-w-none px-4 pt-16 pb-6">
                <div className="mb-4 flex items-center gap-2">
                  <img src={logoImg} alt="Stock Sense" className="h-9 w-9 object-contain" />
                  <span className="font-display font-semibold text-2xl text-foreground">
                    Stock Sense
                  </span>
                </div>
                <nav className="flex flex-col gap-3">
                  <SheetClose asChild>
                    <Link
                      href="/"
                      className={`flex items-center gap-2 text-sm font-medium px-2 py-1.5 rounded-md ${
                        location === "/" ? "text-primary bg-primary/10" : "text-foreground hover:bg-muted/70"
                      }`}
                    >
                      <Home className="h-4 w-4 text-muted-foreground" />
                      <span>Home</span>
                    </Link>
                  </SheetClose>
                  <SheetClose asChild>
                    <Link
                      href="/pricing"
                      className={`flex items-center gap-2 text-sm font-medium px-2 py-1.5 rounded-md ${
                        location === "/pricing" ? "text-primary bg-primary/10" : "text-foreground hover:bg-muted/70"
                      }`}
                    >
                      <DollarSign className="h-4 w-4 text-muted-foreground" />
                      <span>Pricing</span>
                    </Link>
                  </SheetClose>
                  {user && (
                    <>
                      <SheetClose asChild>
                        <Link
                          href="/chat"
                          className={`flex items-center gap-2 text-sm font-medium px-2 py-1.5 rounded-md ${
                            location === "/chat" ? "text-primary bg-primary/10" : "text-foreground hover:bg-muted/70"
                          }`}
                        >
                          <MessageCircle className="h-4 w-4 text-muted-foreground" />
                          <span>Chat</span>
                        </Link>
                      </SheetClose>
                      <SheetClose asChild>
                        <Link
                          href="/profile"
                          className={`flex items-center gap-2 text-sm font-medium px-2 py-1.5 rounded-md ${
                            location === "/profile" ? "text-primary bg-primary/10" : "text-foreground hover:bg-muted/70"
                          }`}
                        >
                          <User className="h-4 w-4 text-muted-foreground" />
                          <span>Profile</span>
                        </Link>
                      </SheetClose>
                      <button
                        type="button"
                        onClick={async () => {
                          setMobileOpen(false);
                          await handleLogout();
                        }}
                        className="mt-2 flex items-center gap-2 text-sm font-medium px-2 py-1.5 rounded-md text-destructive hover:bg-destructive/10 text-left"
                      >
                        <LogOut className="h-4 w-4" />
                        <span>Log out</span>
                      </button>
                    </>
                  )}
                  {!user && !authLoading && (
                    <SheetClose asChild>
                      <Link
                        href="/auth"
                        className="mt-2 flex items-center gap-2 text-sm font-medium px-2 py-1.5 rounded-md text-foreground hover:bg-muted/70"
                      >
                        <User className="h-4 w-4 text-muted-foreground" />
                        <span>Log in / Sign up</span>
                      </Link>
                    </SheetClose>
                  )}
                </nav>
              </SheetContent>
            </Sheet>
          </div>
        </div>
      </div>
    </header>
  );
}

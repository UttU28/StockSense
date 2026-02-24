import { Link, useLocation } from "wouter";
import { BarChart3, LogOut, User } from "lucide-react";
import { Button } from "@/components/ui/button";
import { useAuth } from "@/contexts/AuthContext";

export function AppNavbar() {
  const { user, loading: authLoading, signOut } = useAuth();
  const [location, setLocation] = useLocation();

  const handleLogout = async () => {
    await signOut();
    setLocation("/");
  };

  return (
    <header className="sticky top-0 z-50 flex-none border-b border-border bg-card/80 backdrop-blur-sm">
      <div className="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex items-center justify-between h-14">
          <nav className="flex items-center gap-6">
            <Link href="/" className="flex items-center gap-2 text-foreground hover:text-primary transition-colors shrink-0">
              <BarChart3 className="w-6 h-6" />
              <span className="font-display font-bold text-lg">Stock Gita</span>
            </Link>
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
          <div className="flex items-center gap-2">
            {!authLoading && (
              user ? (
                <>
                  <span className="text-sm text-muted-foreground truncate max-w-[120px] sm:max-w-[180px]" title={user.email ?? undefined}>
                    {user.displayName || user.email || "User"}
                  </span>
                  <Link href="/profile">
                    <Button variant="ghost" size="sm" className="gap-1.5">
                      <User className="w-4 h-4" />
                      <span className="hidden sm:inline">Profile</span>
                    </Button>
                  </Link>
                  <Button variant="outline" size="sm" className="gap-1.5 border-border" onClick={handleLogout}>
                    <LogOut className="w-4 h-4" />
                    <span className="hidden sm:inline">Log out</span>
                  </Button>
                </>
              ) : (
                <Link href="/auth">
                  <Button size="sm" className="h-9">Log in / Sign up</Button>
                </Link>
              )
            )}
          </div>
        </div>
      </div>
    </header>
  );
}

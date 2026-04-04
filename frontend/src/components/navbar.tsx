"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import {
  LayoutDashboard,
  Bookmark,
  Settings,
  Menu,
  X,
} from "lucide-react";
import { useState } from "react";
import {
  SignInButton,
  SignUpButton,
  UserButton,
  Show,
  useUser,
} from "@clerk/nextjs";

const navItems = [
  { href: "/dashboard", label: "Dashboard", icon: LayoutDashboard },
  { href: "/watchlist", label: "Watchlist", icon: Bookmark },
  { href: "/settings", label: "Settings", icon: Settings },
];

export function Navbar() {
  const pathname = usePathname();
  const [open, setOpen] = useState(false);
  const { user: clerkUser } = useUser();
  const onboardingComplete = clerkUser?.publicMetadata?.onboarding_complete === true;

  return (
    <header className="sticky top-0 z-50 border-b border-border/60 bg-background/80 backdrop-blur-xl">
      <div className="mx-auto flex h-14 max-w-7xl items-center justify-between px-4 sm:px-6">
        <Link href="/" className="flex items-center gap-2.5 group">
          <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-amber text-amber-foreground font-bold text-sm">
            H
          </div>
          <span className="font-[family-name:var(--font-heading)] text-lg font-semibold tracking-tight">
            HouseMatch
          </span>
        </Link>

        {/* Desktop nav */}
        <nav className="hidden sm:flex items-center gap-1">
          {navItems.map((item) => {
            const active = pathname === item.href;
            return (
              <Link
                key={item.href}
                href={item.href}
                className={`flex items-center gap-2 rounded-lg px-3 py-1.5 text-sm font-medium transition-colors ${
                  active
                    ? "bg-amber/10 text-amber-dark dark:text-amber"
                    : "text-muted-foreground hover:text-foreground hover:bg-muted"
                }`}
              >
                <item.icon className="h-4 w-4" />
                {item.label}
              </Link>
            );
          })}

          {/* Auth section */}
          <div className="ml-2 pl-2 border-l border-border/60 flex items-center gap-2">
            <Show when="signed-out">
              <SignInButton mode="modal">
                <button className="flex items-center gap-2 rounded-lg px-3 py-1.5 text-sm font-medium text-muted-foreground hover:text-foreground hover:bg-muted transition-colors cursor-pointer">
                  Sign In
                </button>
              </SignInButton>
              <SignUpButton mode="modal">
                <button className="flex items-center gap-2 rounded-lg px-3 py-1.5 text-sm font-medium bg-amber text-amber-foreground hover:bg-amber-dark transition-colors cursor-pointer">
                  Sign Up
                </button>
              </SignUpButton>
            </Show>
            <Show when="signed-in">
              {clerkUser && !onboardingComplete && (
                <Link
                  href="/onboard"
                  className="flex items-center gap-1.5 rounded-lg px-3 py-1.5 text-xs font-medium border border-amber/30 text-amber-dark dark:text-amber hover:bg-amber/10 transition-colors"
                >
                  Finish Setup
                </Link>
              )}
              <UserButton
                appearance={{
                  elements: {
                    avatarBox: "h-7 w-7",
                    userButtonPopoverCard: "shadow-xl border border-border/60",
                    userButtonPopoverActionButton: "hover:bg-amber/10",
                  },
                }}
              />
            </Show>
          </div>
        </nav>

        {/* Mobile toggle */}
        <button
          className="sm:hidden p-2 rounded-lg hover:bg-muted"
          onClick={() => setOpen(!open)}
          aria-label={open ? "Close menu" : "Open menu"}
        >
          {open ? <X className="h-5 w-5" /> : <Menu className="h-5 w-5" />}
        </button>
      </div>

      {/* Mobile menu */}
      {open && (
        <nav className="sm:hidden border-t border-border/60 bg-background px-4 pb-4 pt-2">
          {navItems.map((item) => {
            const active = pathname === item.href;
            return (
              <Link
                key={item.href}
                href={item.href}
                onClick={() => setOpen(false)}
                className={`flex items-center gap-3 rounded-lg px-3 py-2.5 text-sm font-medium transition-colors ${
                  active
                    ? "bg-amber/10 text-amber-dark dark:text-amber"
                    : "text-muted-foreground hover:text-foreground"
                }`}
              >
                <item.icon className="h-4 w-4" />
                {item.label}
              </Link>
            );
          })}

          {/* Mobile auth */}
          <div className="mt-2 pt-2 border-t border-border/60 flex items-center gap-2 px-3">
            <Show when="signed-out">
              <SignInButton mode="modal">
                <button className="text-sm font-medium text-muted-foreground hover:text-foreground cursor-pointer">
                  Sign In
                </button>
              </SignInButton>
            </Show>
            <Show when="signed-in">
              <UserButton
                appearance={{
                  elements: {
                    avatarBox: "h-7 w-7",
                  },
                }}
              />
            </Show>
          </div>
        </nav>
      )}
    </header>
  );
}

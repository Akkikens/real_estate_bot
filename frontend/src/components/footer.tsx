import Link from "next/link";
import { Lock, ShieldCheck, CreditCard, Scale } from "lucide-react";

const productLinks = [
  { href: "/dashboard", label: "Dashboard" },
  { href: "/#pricing", label: "Pricing" },
  { href: "/security", label: "Security" },
  { href: "/#faq", label: "FAQ" },
];

const legalLinks = [
  { href: "/privacy", label: "Privacy Policy" },
  { href: "/terms", label: "Terms of Service" },
  { href: "/cookies", label: "Cookie Policy" },
  { href: "/dpa", label: "DPA" },
];

const connectLinks = [
  { href: "https://x.com/housematch", label: "Twitter / X", external: true },
  { href: "https://github.com/housematch", label: "GitHub", external: true },
  {
    href: "mailto:support@housematch.io",
    label: "support@housematch.io",
    external: true,
  },
];

const trustBadges = [
  { icon: Lock, label: "SSL Encrypted" },
  { icon: ShieldCheck, label: "Clerk Auth · SOC 2" },
  { icon: CreditCard, label: "Stripe · PCI DSS" },
  { icon: Scale, label: "CCPA Compliant" },
];

export function Footer() {
  return (
    <footer className="border-t border-border/60 bg-card/30">
      <div className="mx-auto max-w-7xl px-4 sm:px-6 py-12 sm:py-16">
        {/* Top grid */}
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-8 lg:gap-12">
          {/* Brand column */}
          <div className="sm:col-span-2 lg:col-span-1">
            <Link href="/" className="flex items-center gap-2.5 group">
              <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-amber text-amber-foreground font-bold text-sm">
                H
              </div>
              <span className="font-[family-name:var(--font-heading)] text-lg font-semibold tracking-tight">
                HouseMatch
              </span>
            </Link>
            <p className="mt-3 text-sm text-muted-foreground leading-relaxed max-w-xs">
              AI-powered property intelligence for Bay Area house-hackers and
              first-time investors.
            </p>
          </div>

          {/* Product links */}
          <div>
            <h4 className="text-sm font-semibold mb-3">Product</h4>
            <ul className="space-y-2">
              {productLinks.map((link) => (
                <li key={link.href}>
                  <Link
                    href={link.href}
                    className="text-sm text-muted-foreground hover:text-foreground transition-colors"
                  >
                    {link.label}
                  </Link>
                </li>
              ))}
            </ul>
          </div>

          {/* Legal links */}
          <div>
            <h4 className="text-sm font-semibold mb-3">Legal</h4>
            <ul className="space-y-2">
              {legalLinks.map((link) => (
                <li key={link.href}>
                  <Link
                    href={link.href}
                    className="text-sm text-muted-foreground hover:text-foreground transition-colors"
                  >
                    {link.label}
                  </Link>
                </li>
              ))}
            </ul>
          </div>

          {/* Connect links */}
          <div>
            <h4 className="text-sm font-semibold mb-3">Connect</h4>
            <ul className="space-y-2">
              {connectLinks.map((link) => (
                <li key={link.href}>
                  <a
                    href={link.href}
                    className="text-sm text-muted-foreground hover:text-foreground transition-colors"
                    {...(link.external
                      ? { target: "_blank", rel: "noopener noreferrer" }
                      : {})}
                  >
                    {link.label}
                  </a>
                </li>
              ))}
            </ul>
          </div>
        </div>

        {/* Divider */}
        <div className="mt-10 pt-6 border-t border-border/60">
          {/* Trust badges */}
          <div className="flex flex-wrap items-center justify-center gap-4 sm:gap-6 mb-6">
            {trustBadges.map((badge) => (
              <div
                key={badge.label}
                className="flex items-center gap-1.5 text-xs text-muted-foreground"
              >
                <badge.icon className="h-3.5 w-3.5" />
                <span>{badge.label}</span>
              </div>
            ))}
          </div>

          {/* Copyright */}
          <p className="text-center text-xs text-muted-foreground">
            &copy; {new Date().getFullYear()} HouseMatch Inc. All rights
            reserved.
          </p>
        </div>
      </div>
    </footer>
  );
}

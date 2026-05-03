import type { Metadata } from "next";
import Link from "next/link";
import { LegalLayout } from "@/components/legal-layout";
import {
  Lock,
  ShieldCheck,
  Database,
  Globe,
  Key,
  Users,
  Eye,
  Server,
} from "lucide-react";

export const metadata: Metadata = {
  title: "Security",
  description:
    "Learn how HouseMatch protects your data with enterprise-grade security practices.",
};

const infrastructure = [
  {
    icon: Lock,
    label: "Encryption in transit (TLS 1.3)",
  },
  {
    icon: Database,
    label: "Encryption at rest (AES-256 via Supabase)",
  },
  {
    icon: Server,
    label: "Database hosted on Supabase (AWS us-east-1)",
  },
  {
    icon: Globe,
    label: "Frontend hosted on Vercel (global edge network)",
  },
  {
    icon: Key,
    label: "Authentication via Clerk (SOC 2 Type II)",
  },
  {
    icon: ShieldCheck,
    label: "Payment processing via Stripe (PCI DSS Level 1)",
  },
];

const subProcessors = [
  {
    service: "Clerk",
    purpose: "Authentication",
    certification: "SOC 2 Type II",
  },
  {
    service: "Supabase",
    purpose: "Database",
    certification: "SOC 2 Type II",
  },
  {
    service: "Stripe",
    purpose: "Payments",
    certification: "PCI DSS Level 1",
  },
  {
    service: "Twilio",
    purpose: "SMS / WhatsApp delivery",
    certification: "SOC 2 Type II",
  },
  {
    service: "Vercel",
    purpose: "Frontend hosting",
    certification: "SOC 2 Type II",
  },
];

export default function SecurityPage() {
  return (
    <LegalLayout title="Security" lastUpdated="April 2026">
      <p>
        We treat your data like we treat our own home search — with serious
        care. This page outlines the security measures we employ to protect your
        information.
      </p>

      <h2>Infrastructure</h2>
      <div className="not-prose grid gap-3 my-6">
        {infrastructure.map((item) => (
          <div
            key={item.label}
            className="flex items-center gap-3 rounded-lg border border-border/60 bg-card p-3"
          >
            <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-md bg-emerald-500/10 text-emerald-600 dark:text-emerald-400">
              <item.icon className="h-4 w-4" />
            </div>
            <span className="text-sm font-medium">{item.label}</span>
          </div>
        ))}
      </div>

      <h2>Authentication &amp; Access</h2>
      <ul>
        <li>
          <strong>Clerk manages all authentication</strong> — we never see or
          store your password directly. Clerk handles password hashing, session
          tokens, and optional multi-factor authentication (MFA).
        </li>
        <li>
          <strong>OAuth via Google</strong> — optional social sign-in available
        </li>
        <li>
          <strong>Session tokens</strong> — automatically rotated and expired by
          Clerk
        </li>
        <li>
          <strong>Isolated data</strong> — each user&apos;s data (preferences,
          watchlist, scoring) is isolated and accessible only to that user
        </li>
      </ul>

      <h2>Data Practices</h2>
      <ul>
        <li>
          We collect only what we need — email, preferences, and watchlist data.
          See our <Link href="/privacy">Privacy Policy</Link> for the complete
          list.
        </li>
        <li>
          <strong>We never sell personal data.</strong> We do not display ads or
          share data with advertisers.
        </li>
        <li>
          Property data is sourced from publicly available real estate listings.
        </li>
        <li>
          Data deletion is available on request. Account holders can request
          deletion via Settings → Delete Account or by emailing{" "}
          <a href="mailto:privacy@housematch.io">privacy@housematch.io</a>.
        </li>
      </ul>

      <h2>Third-Party Sub-Processors</h2>
      <p>
        We use the following third-party services to operate HouseMatch. All are
        SOC 2 or PCI DSS certified:
      </p>
      <table>
        <thead>
          <tr>
            <th>Service</th>
            <th>Purpose</th>
            <th>Certification</th>
          </tr>
        </thead>
        <tbody>
          {subProcessors.map((sp) => (
            <tr key={sp.service}>
              <td className="font-medium">{sp.service}</td>
              <td>{sp.purpose}</td>
              <td>{sp.certification}</td>
            </tr>
          ))}
        </tbody>
      </table>

      <h2>Vulnerability Reporting</h2>
      <div className="not-prose my-6 rounded-lg border border-border/60 bg-card p-5">
        <div className="flex items-start gap-3">
          <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-md bg-amber/10 text-amber-dark dark:text-amber">
            <Eye className="h-4 w-4" />
          </div>
          <div>
            <p className="text-sm font-semibold mb-1">
              Found a security issue?
            </p>
            <p className="text-sm text-muted-foreground leading-relaxed">
              Email{" "}
              <a
                href="mailto:security@housematch.io"
                className="text-amber-dark dark:text-amber underline underline-offset-2"
              >
                security@housematch.io
              </a>
              . We respond within 24 hours and do not pursue legal action
              against good-faith security researchers.
            </p>
          </div>
        </div>
      </div>

      <h2>SOC 2 Compliance Status</h2>
      <div className="not-prose my-6 rounded-lg border border-border/60 bg-card p-5">
        <div className="flex items-start gap-3">
          <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-md bg-blue-500/10 text-blue-600 dark:text-blue-400">
            <Users className="h-4 w-4" />
          </div>
          <div>
            <p className="text-sm text-muted-foreground leading-relaxed">
              We are working toward SOC 2 Type II compliance. Our key
              sub-processors (Clerk, Supabase, Stripe, Vercel) are all SOC 2
              Type II certified. Contact{" "}
              <a
                href="mailto:security@housematch.io"
                className="text-amber-dark dark:text-amber underline underline-offset-2"
              >
                security@housematch.io
              </a>{" "}
              for our current security questionnaire.
            </p>
          </div>
        </div>
      </div>

      <h2>More Information</h2>
      <p>
        For details on how we handle your personal data, see our{" "}
        <Link href="/privacy">Privacy Policy</Link>. For our sub-processor
        agreements, see our{" "}
        <Link href="/dpa">Data Processing Agreement</Link>.
      </p>
    </LegalLayout>
  );
}

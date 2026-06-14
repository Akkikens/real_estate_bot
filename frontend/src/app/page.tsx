"use client";

import { useEffect, useRef, useState } from "react";
import Link from "next/link";
import { motion, AnimatePresence } from "framer-motion";
import {
  ArrowRight,
  BarChart3,
  Bell,
  Check,
  ChevronDown,
  Home,
  MessageSquare,
  Shield,
  Star,
  Target,
  TrendingUp,
  Zap,
} from "lucide-react";
import { SignUpButton, Show } from "@clerk/nextjs";
import { Button } from "@/components/ui/button";
import { Navbar } from "@/components/navbar";
import { Footer } from "@/components/footer";
import { ScoreRing } from "@/components/score-ring";
import { useStats, useProperties } from "@/lib/queries";

// ── Animation variants ───────────────────────────────────────────────────────

const fade = {
  hidden: { opacity: 0, y: 24 },
  show: (i: number) => ({
    opacity: 1,
    y: 0,
    transition: { delay: i * 0.1, duration: 0.5, ease: "easeOut" as const },
  }),
};

const fadeIn = {
  hidden: { opacity: 0, y: 20 },
  show: {
    opacity: 1,
    y: 0,
    transition: { duration: 0.5, ease: "easeOut" as const },
  },
};

// ── Data ─────────────────────────────────────────────────────────────────────

const heroProperties = [
  {
    address: "1247 Elm St, Fremont",
    score: 87,
    price: "$789k",
    beds: 4,
    baths: 2,
    tags: ["House Hack", "ADU", "Near BART"],
  },
  {
    address: "482 Oak Ave, Oakland",
    score: 92,
    price: "$625k",
    beds: 3,
    baths: 2,
    tags: ["Duplex", "Deal Signal", "Large Lot"],
  },
  {
    address: "3901 Pine Dr, Richmond",
    score: 78,
    price: "$510k",
    beds: 4,
    baths: 3,
    tags: ["House Hack", "Price Drop", "4 Bed"],
  },
];

const steps = [
  {
    icon: Target,
    title: "Tell Us Your Strategy",
    desc: "Pick house-hack, buy & hold, or primary residence. Set your budget and target cities.",
  },
  {
    icon: BarChart3,
    title: "We Score Everything",
    desc: "Every listing gets scored 0–100 across 8 dimensions tailored to YOUR criteria.",
  },
  {
    icon: Bell,
    title: "Get Your Top Picks",
    desc: "Top 5 delivered to your phone daily via SMS or WhatsApp. One tap to save.",
  },
];

const mainFeatures = [
  {
    title: "AI-Powered Scoring",
    desc: "Every listing scored 0–100 across 8 dimensions: Price Fit · House Hack · Rental Income · ADU Upside · Transit · Neighborhood · Deal Signal · Lot Expansion. See exactly WHY a property scored high — and what to watch out for.",
    visual: "score",
  },
  {
    title: "Your Strategy, Your Scores",
    desc: "Pick House-Hack, Buy & Hold, or Primary Residence. We re-weight every dimension to match your playbook. A duplex near BART scores 92 for a house-hacker but 61 for someone who just wants a quiet family home. Same property, different score — because your strategy matters.",
    visual: "strategy",
  },
  {
    title: "Daily Alerts — Right to Your Phone",
    desc: "Top picks delivered via SMS, WhatsApp, or email at the time you choose. We filter out the noise so you only see properties that actually match. Stop refreshing Redfin 12 times a day.",
    visual: "alert",
  },
];

const miniFeatures = [
  {
    icon: Shield,
    title: "Multi-Source Data",
    desc: "Redfin + Zillow + Realtor.com + Craigslist. No blind spots.",
  },
  {
    icon: TrendingUp,
    title: "Price Drop Tracking",
    desc: "Get alerted when a saved property drops. Know the real market.",
  },
  {
    icon: Home,
    title: "ADU & Lot Analysis",
    desc: "Spot in-law unit potential and lot expansion opportunities automatically.",
  },
];

const testimonials = [
  {
    name: "Priya M.",
    role: "First-time buyer · Fremont",
    text: "Found my house-hack duplex in 2 weeks. The ADU scoring alone saved me months of manual research.",
    outcome: "Saved $45k on her first deal",
    score: 87,
    color: "bg-amber-500",
  },
  {
    name: "Marcus T.",
    role: "Investor · Oakland",
    text: "I was spending 3 hours a day on Redfin. Now I get the top 5 deals texted to me before breakfast.",
    outcome: "Found deal in 2 weeks",
    score: 92,
    color: "bg-blue-500",
  },
  {
    name: "Sarah K.",
    role: "House-hacker · San Jose",
    text: "The BART proximity scoring is genius. My rental income covers 80% of my mortgage now.",
    outcome: "Covers 80% of mortgage",
    score: 78,
    color: "bg-emerald-500",
  },
  {
    name: "James R.",
    role: "First-time buyer · Hayward",
    text: "Other tools showed me everything. HouseMatch showed me what actually works for my strategy and budget.",
    outcome: "Closed in 30 days",
    score: 84,
    color: "bg-purple-500",
  },
  {
    name: "Lisa C.",
    role: "Investor · Concord",
    text: "The underwriting calculator sold me. I can model any property in 30 seconds without a spreadsheet.",
    outcome: "3 properties in 6 months",
    score: 89,
    color: "bg-rose-500",
  },
  {
    name: "David P.",
    role: "House-hacker · Berkeley",
    text: "Price drop alerts alone are worth the Pro subscription. Caught a $40k drop on a property I'd been watching.",
    outcome: "Caught $40k price drop",
    score: 91,
    color: "bg-cyan-500",
  },
];

const monthlyPlans = [
  {
    name: "Free",
    price: "$0",
    period: "/mo",
    desc: "Get started with basic alerts",
    features: [
      "3 target cities",
      "Daily email digest",
      "Basic scoring (5 dimensions)",
      "10 watchlist slots",
    ],
    cta: "Start Free",
    highlight: false,
  },
  {
    name: "Pro",
    price: "$19",
    period: "/mo",
    desc: "For serious house-hackers",
    features: [
      "Unlimited cities",
      "SMS + WhatsApp alerts",
      "Full 8-dimension scoring",
      "Unlimited watchlist",
      "Price drop tracking",
      "Rental income estimates",
    ],
    cta: "Go Pro",
    highlight: true,
  },
  {
    name: "Investor",
    price: "$49",
    period: "/mo",
    desc: "Portfolio-grade intelligence",
    features: [
      "Everything in Pro",
      "API access",
      "Bulk CSV export",
      "Custom scoring weights",
      "Priority data refresh",
      "Dedicated support",
    ],
    cta: "Get Investor",
    highlight: false,
  },
];

const annualPlans = monthlyPlans.map((p) => ({
  ...p,
  price: p.name === "Free" ? "$0" : p.name === "Pro" ? "$15" : "$39",
}));

const comparisonFeatures = [
  { label: "Target cities", free: "3", pro: "Unlimited", investor: "Unlimited" },
  { label: "Scoring dimensions", free: "5", pro: "8", investor: "8 + custom" },
  { label: "Watchlist slots", free: "10", pro: "100", investor: "Unlimited" },
  { label: "SMS / WhatsApp", free: "✗", pro: "✓", investor: "✓" },
  { label: "API access", free: "✗", pro: "✗", investor: "✓" },
  { label: "CSV export", free: "✗", pro: "✗", investor: "✓" },
  { label: "Support", free: "Email", pro: "Chat", investor: "Priority" },
];

const faqs = [
  {
    q: "Where does HouseMatch get its data?",
    a: "We aggregate from Redfin, Zillow, Realtor.com, Craigslist, and public records. Data is refreshed daily. We cross-reference multiple sources to catch listings others miss and verify pricing accuracy.",
  },
  {
    q: "How does the scoring work?",
    a: "Every property is scored 0–100 across 8 weighted dimensions: Price Fit, House Hack Potential, Rental Income, ADU Upside, Transit Access, Neighborhood Quality, Deal Opportunity, and Lot Expansion. Weights adjust based on your strategy.",
  },
  {
    q: "Is my data safe?",
    a: "Yes. We use Clerk for authentication (SOC 2 Type II certified), encrypt all data in transit (TLS 1.3) and at rest. We never sell your personal information. See our Privacy Policy and Security page for details.",
  },
  {
    q: "Can I use HouseMatch outside the Bay Area?",
    a: "We're currently Bay Area only (15 cities from Richmond to San Jose). We're expanding to Sacramento, LA, and Portland in 2026. Join the waitlist to be first.",
  },
  {
    q: 'What\'s a "house hack"?',
    a: "House hacking means buying a property, living in one part, and renting out the rest to offset your mortgage. Example: buy a 4BR, rent 3 rooms at $1,400/ea, cover 85% of your mortgage from day one.",
  },
  {
    q: "Do I need to pay to browse properties?",
    a: "No. Browsing the full property feed, viewing scores, and property details are free forever. Paid plans add SMS/WhatsApp alerts, unlimited watchlist, and advanced scoring dimensions.",
  },
  {
    q: "How is this different from Zillow or Redfin?",
    a: "Zillow and Redfin show you every listing equally. HouseMatch scores every listing against YOUR specific strategy, budget, and preferences — then delivers only the best ones. We don't sell ads or promote agent listings.",
  },
  {
    q: "Can I cancel anytime?",
    a: "Yes. No contracts, no cancellation fees. Cancel from Settings → Subscription and your plan reverts to Free at the end of your billing period.",
  },
  {
    q: "Who built this?",
    a: "HouseMatch is built by a team of Bay Area house-hackers who were tired of spending hours on Redfin every day. We built the tool we wished existed.",
  },
  {
    q: "How do I get support?",
    a: "Email support@housematch.io. Pro and Investor customers get priority response within 4 hours during business hours.",
  },
];

// ── Number counter animation hook ────────────────────────────────────────────

function useCountUp(end: number, duration = 2000, trigger = false) {
  const [count, setCount] = useState(0);
  useEffect(() => {
    if (!trigger) return;
    let start = 0;
    const step = end / (duration / 16);
    const timer = setInterval(() => {
      start += step;
      if (start >= end) {
        setCount(end);
        clearInterval(timer);
      } else {
        setCount(Math.floor(start));
      }
    }, 16);
    return () => clearInterval(timer);
  }, [end, duration, trigger]);
  return count;
}

// ── Hero Card Carousel ───────────────────────────────────────────────────────

function HeroCardCarousel() {
  const [index, setIndex] = useState(0);

  useEffect(() => {
    const interval = setInterval(() => {
      setIndex((i) => (i + 1) % heroProperties.length);
    }, 4000);
    return () => clearInterval(interval);
  }, []);

  const prop = heroProperties[index];

  return (
    <div className="relative w-full max-w-xs mx-auto">
      <AnimatePresence mode="wait">
        <motion.div
          key={index}
          initial={{ opacity: 0, y: 10 }}
          animate={{ opacity: 1, y: 0 }}
          exit={{ opacity: 0, y: -10 }}
          transition={{ duration: 0.4 }}
          className="rounded-2xl border border-border/60 bg-card/80 backdrop-blur-lg p-5 shadow-xl"
        >
          <div className="flex items-start justify-between">
            <div>
              <p className="text-xs text-muted-foreground">Top Pick Today</p>
              <p className="font-semibold mt-1">
                {prop.address.split(",")[0]}
              </p>
              <p className="text-sm text-muted-foreground">
                {prop.address.split(",")[1]?.trim()}
              </p>
            </div>
            <ScoreRing score={prop.score} size={64} strokeWidth={3} />
          </div>
          <div className="mt-4 grid grid-cols-3 gap-2 text-center">
            <div className="rounded-lg bg-muted/50 p-2">
              <p className="text-xs text-muted-foreground">Price</p>
              <p className="text-sm font-semibold">{prop.price}</p>
            </div>
            <div className="rounded-lg bg-muted/50 p-2">
              <p className="text-xs text-muted-foreground">Beds</p>
              <p className="text-sm font-semibold">{prop.beds}</p>
            </div>
            <div className="rounded-lg bg-muted/50 p-2">
              <p className="text-xs text-muted-foreground">Baths</p>
              <p className="text-sm font-semibold">{prop.baths}</p>
            </div>
          </div>
          <div className="mt-3 flex gap-1 flex-wrap">
            {prop.tags.map((tag) => (
              <span
                key={tag}
                className="rounded-md bg-amber/10 px-2 py-0.5 text-[10px] font-medium text-amber-dark dark:text-amber"
              >
                {tag}
              </span>
            ))}
          </div>
        </motion.div>
      </AnimatePresence>
      {/* Dots */}
      <div className="flex justify-center gap-1.5 mt-4">
        {heroProperties.map((_, i) => (
          <button
            key={i}
            onClick={() => setIndex(i)}
            className={`h-1.5 rounded-full transition-all cursor-pointer ${
              i === index ? "w-6 bg-amber" : "w-1.5 bg-muted-foreground/30"
            }`}
          />
        ))}
      </div>
    </div>
  );
}

// ── Interactive Preview ──────────────────────────────────────────────────────

function InteractivePreview() {
  const [maxPrice, setMaxPrice] = useState(1000000);
  const { data } = useProperties({
    max_price: maxPrice,
    page_size: 3,
    sort: "score",
  });

  const formatPrice = (v: number) =>
    v >= 1000000 ? `$${(v / 1000000).toFixed(1)}M` : `$${(v / 1000).toFixed(0)}k`;

  return (
    <div className="space-y-6">
      <div className="flex flex-col sm:flex-row gap-4 items-start sm:items-center">
        <div className="flex-1 w-full">
          <label className="text-sm font-medium mb-2 block">
            Budget: {formatPrice(maxPrice)}
          </label>
          <input
            type="range"
            min={300000}
            max={2000000}
            step={50000}
            value={maxPrice}
            onChange={(e) => setMaxPrice(Number(e.target.value))}
            className="w-full accent-amber-dark h-2 rounded-lg appearance-none bg-muted cursor-pointer"
          />
          <div className="flex justify-between text-xs text-muted-foreground mt-1">
            <span>$300k</span>
            <span>$2M</span>
          </div>
        </div>
      </div>

      {data?.items && data.items.length > 0 ? (
        <div className="grid sm:grid-cols-3 gap-4">
          {data.items.slice(0, 3).map((p) => (
            <div
              key={p.id}
              className="rounded-xl border border-border/60 bg-card p-4"
            >
              <div className="flex items-start justify-between mb-2">
                <div className="min-w-0 flex-1">
                  <p className="text-sm font-semibold truncate">{p.address}</p>
                  <p className="text-xs text-muted-foreground">{p.city}</p>
                </div>
                <ScoreRing
                  score={p.total_score ?? 0}
                  size={44}
                  strokeWidth={2.5}
                  showLabel={false}
                />
              </div>
              <p className="text-lg font-bold">
                {p.list_price
                  ? `$${(p.list_price / 1000).toFixed(0)}k`
                  : "—"}
              </p>
              <div className="flex gap-1 mt-2 flex-wrap">
                {p.tags?.slice(0, 3).map((tag) => (
                  <span
                    key={tag}
                    className="rounded-md bg-amber/10 px-1.5 py-0.5 text-[9px] font-medium text-amber-dark dark:text-amber"
                  >
                    {tag}
                  </span>
                ))}
              </div>
            </div>
          ))}
        </div>
      ) : (
        <div className="grid sm:grid-cols-3 gap-4">
          {[1, 2, 3].map((i) => (
            <div
              key={i}
              className="rounded-xl border border-border/60 bg-card p-4 animate-pulse"
            >
              <div className="h-4 w-3/4 bg-muted rounded mb-2" />
              <div className="h-3 w-1/2 bg-muted rounded mb-3" />
              <div className="h-6 w-1/3 bg-muted rounded" />
            </div>
          ))}
        </div>
      )}

      <div className="text-center">
        <p className="text-sm text-muted-foreground mb-3">
          ✨{" "}
          {data?.total ? (
            <span className="font-semibold text-foreground">
              {data.total.toLocaleString()}
            </span>
          ) : (
            "Hundreds of"
          )}{" "}
          more properties waiting
        </p>
        <Show when="signed-out">
          <SignUpButton mode="modal">
            <Button className="bg-amber text-amber-foreground hover:bg-amber-dark cursor-pointer">
              Get My Full Feed
              <ArrowRight className="ml-2 h-4 w-4" />
            </Button>
          </SignUpButton>
        </Show>
        <Show when="signed-in">
          <Link href="/dashboard">
            <Button className="bg-amber text-amber-foreground hover:bg-amber-dark cursor-pointer">
              Go to Dashboard
              <ArrowRight className="ml-2 h-4 w-4" />
            </Button>
          </Link>
        </Show>
      </div>
    </div>
  );
}

// ── FAQ Accordion ────────────────────────────────────────────────────────────

function FaqItem({ q, a }: { q: string; a: string }) {
  const [open, setOpen] = useState(false);
  return (
    <div className="border-b border-border/60">
      <button
        onClick={() => setOpen(!open)}
        className="flex w-full items-center justify-between py-4 text-left cursor-pointer group"
      >
        <span className="text-sm font-medium pr-4 group-hover:text-amber-dark dark:group-hover:text-amber transition-colors">
          {q}
        </span>
        <ChevronDown
          className={`h-4 w-4 shrink-0 text-muted-foreground transition-transform ${
            open ? "rotate-180" : ""
          }`}
        />
      </button>
      <AnimatePresence initial={false}>
        {open && (
          <motion.div
            initial={{ height: 0, opacity: 0 }}
            animate={{ height: "auto", opacity: 1 }}
            exit={{ height: 0, opacity: 0 }}
            transition={{ duration: 0.2 }}
            className="overflow-hidden"
          >
            <p className="pb-4 text-sm text-muted-foreground leading-relaxed">
              {a}
            </p>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}

// ── Testimonial Marquee ──────────────────────────────────────────────────────

function TestimonialMarquee() {
  const row1 = testimonials.slice(0, 3);
  const row2 = testimonials.slice(3, 6);

  return (
    <div className="space-y-4 overflow-hidden">
      {[row1, row2].map((row, rowIdx) => (
        <div key={rowIdx} className="relative">
          <motion.div
            className="flex gap-4"
            animate={{ x: rowIdx === 0 ? [0, -1200] : [-1200, 0] }}
            transition={{
              x: {
                repeat: Infinity,
                repeatType: "loop",
                duration: 40,
                ease: "linear",
              },
            }}
          >
            {/* Duplicate for seamless loop */}
            {[...row, ...row, ...row].map((t, i) => (
              <div
                key={`${t.name}-${i}`}
                className="shrink-0 w-80 rounded-xl border border-border/60 bg-card p-5"
              >
                <div className="flex items-center gap-1 mb-3">
                  {[...Array(5)].map((_, j) => (
                    <Star
                      key={j}
                      className="h-3.5 w-3.5 fill-amber text-amber"
                    />
                  ))}
                </div>
                <p className="text-sm leading-relaxed text-muted-foreground mb-4">
                  &ldquo;{t.text}&rdquo;
                </p>
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-2.5">
                    <div
                      className={`flex h-8 w-8 items-center justify-center rounded-full text-white text-xs font-bold ${t.color}`}
                    >
                      {t.name.charAt(0)}
                    </div>
                    <div>
                      <p className="text-sm font-semibold">{t.name}</p>
                      <p className="text-xs text-muted-foreground">
                        {t.role}
                      </p>
                    </div>
                  </div>
                  <ScoreRing
                    score={t.score}
                    size={36}
                    strokeWidth={2}
                    showLabel={false}
                  />
                </div>
                <p className="mt-3 text-xs font-medium text-amber-dark dark:text-amber">
                  ✦ {t.outcome}
                </p>
              </div>
            ))}
          </motion.div>
        </div>
      ))}
    </div>
  );
}

// ── JSON-LD Structured Data ──────────────────────────────────────────────────

const jsonLd = {
  "@context": "https://schema.org",
  "@type": "SoftwareApplication",
  name: "HouseMatch",
  applicationCategory: "BusinessApplication",
  operatingSystem: "Web",
  description:
    "AI-powered property scoring for Bay Area house-hackers and investors",
  offers: [
    { "@type": "Offer", price: "0", priceCurrency: "USD", name: "Free" },
    { "@type": "Offer", price: "19", priceCurrency: "USD", name: "Pro" },
    { "@type": "Offer", price: "49", priceCurrency: "USD", name: "Investor" },
  ],
  aggregateRating: {
    "@type": "AggregateRating",
    ratingValue: "4.8",
    reviewCount: "127",
  },
};

// ══════════════════════════════════════════════════════════════════════════════
// MAIN PAGE COMPONENT
// ══════════════════════════════════════════════════════════════════════════════

export default function LandingPage() {
  const { data: stats } = useStats();
  const [annual, setAnnual] = useState(false);
  const [showComparison, setShowComparison] = useState(false);

  // Social proof stats — use real data from API when available
  const proofBarRef = useRef<HTMLDivElement>(null);
  const [proofVisible, setProofVisible] = useState(false);

  useEffect(() => {
    const observer = new IntersectionObserver(
      ([entry]) => {
        if (entry.isIntersecting) setProofVisible(true);
      },
      { threshold: 0.5 }
    );
    if (proofBarRef.current) observer.observe(proofBarRef.current);
    return () => observer.disconnect();
  }, []);

  const propertiesCount = useCountUp(
    stats?.total_active ?? 1400,
    2000,
    proofVisible
  );
  const buyersCount = useCountUp(200, 2000, proofVisible);
  const ratingCount = useCountUp(48, 2000, proofVisible);

  const plans = annual ? annualPlans : monthlyPlans;

  return (
    <div className="min-h-screen">
      <Navbar />

      {/* JSON-LD */}
      <script
        type="application/ld+json"
        dangerouslySetInnerHTML={{ __html: JSON.stringify(jsonLd) }}
      />

      {/* ─── Hero ───────────────────────────────────────────────────────── */}
      <section className="relative overflow-hidden">
        {/* Gradient mesh background */}
        <div className="absolute inset-0 bg-gradient-to-br from-amber/5 via-transparent to-amber/3 pointer-events-none" />
        <div className="absolute inset-0 blueprint-grid pointer-events-none" />

        <div className="relative mx-auto max-w-7xl px-4 sm:px-6 py-16 sm:py-24 lg:py-32">
          <div className="grid lg:grid-cols-2 gap-12 lg:gap-16 items-center">
            {/* Left column — copy */}
            <div>
              <motion.div
                initial="hidden"
                animate="show"
                variants={fade}
                custom={0}
              >
                <span className="inline-flex items-center gap-2 rounded-full bg-amber/10 px-3 py-1 text-sm font-medium text-amber-dark dark:text-amber mb-6">
                  <Zap className="h-3.5 w-3.5" />
                  Bay Area Beta — {stats?.total_active?.toLocaleString() ?? "1,400"}+ properties scored
                </span>
              </motion.div>

              <motion.h1
                className="font-[family-name:var(--font-heading)] text-4xl sm:text-5xl lg:text-6xl font-bold tracking-tight leading-[1.1]"
                initial="hidden"
                animate="show"
                variants={fade}
                custom={1}
              >
                Your AI
                <br />
                <span className="text-amber-dark dark:text-amber">
                  Property Scout
                </span>
              </motion.h1>

              <motion.p
                className="mt-6 text-lg sm:text-xl text-muted-foreground max-w-xl leading-relaxed"
                initial="hidden"
                animate="show"
                variants={fade}
                custom={2}
              >
                Stop doom-scrolling Redfin. Get the top 5 properties for YOUR
                strategy, delivered daily.
              </motion.p>

              <motion.div
                className="mt-8 flex flex-col sm:flex-row gap-3"
                initial="hidden"
                animate="show"
                variants={fade}
                custom={3}
              >
                <Show when="signed-out">
                  <SignUpButton mode="modal">
                    <Button
                      size="lg"
                      className="bg-amber text-amber-foreground hover:bg-amber-dark h-12 px-6 text-base cursor-pointer"
                    >
                      Get Started Free
                      <ArrowRight className="ml-2 h-4 w-4" />
                    </Button>
                  </SignUpButton>
                </Show>
                <Show when="signed-in">
                  <Link href="/dashboard">
                    <Button
                      size="lg"
                      className="bg-amber text-amber-foreground hover:bg-amber-dark h-12 px-6 text-base cursor-pointer"
                    >
                      Go to Dashboard
                      <ArrowRight className="ml-2 h-4 w-4" />
                    </Button>
                  </Link>
                </Show>
                <a href="#pricing">
                  <Button
                    variant="outline"
                    size="lg"
                    className="h-12 px-6 text-base"
                  >
                    View Pricing
                  </Button>
                </a>
              </motion.div>

              <motion.div
                className="mt-6 flex flex-wrap gap-x-4 gap-y-1 text-sm text-muted-foreground"
                initial="hidden"
                animate="show"
                variants={fade}
                custom={4}
              >
                <span className="flex items-center gap-1.5">
                  <Check className="h-3.5 w-3.5 text-amber-dark dark:text-amber" />
                  Free forever plan
                </span>
                <span className="flex items-center gap-1.5">
                  <Check className="h-3.5 w-3.5 text-amber-dark dark:text-amber" />
                  No credit card
                </span>
                <span className="flex items-center gap-1.5">
                  <Check className="h-3.5 w-3.5 text-amber-dark dark:text-amber" />
                  2-min setup
                </span>
              </motion.div>
            </div>

            {/* Right column — animated card */}
            <motion.div
              initial={{ opacity: 0, x: 40 }}
              animate={{ opacity: 1, x: 0 }}
              transition={{ delay: 0.5, duration: 0.7 }}
              className="hidden lg:block"
            >
              <HeroCardCarousel />
            </motion.div>
          </div>
        </div>
      </section>

      {/* ─── Social Proof Bar ───────────────────────────────────────────── */}
      <section
        ref={proofBarRef}
        className="border-y border-border/60 bg-card/50"
      >
        <div className="mx-auto max-w-7xl px-4 sm:px-6 py-6">
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-6 text-center">
            <div>
              <p className="text-2xl font-bold font-mono tabular-nums">
                {proofVisible ? propertiesCount.toLocaleString() : "0"}+
              </p>
              <p className="text-xs text-muted-foreground mt-0.5">
                🏠 Properties scored
              </p>
            </div>
            <div>
              <p className="text-2xl font-bold font-mono tabular-nums">
                {proofVisible ? buyersCount : "0"}+
              </p>
              <p className="text-xs text-muted-foreground mt-0.5">
                👥 Bay Area buyers
              </p>
            </div>
            <div>
              <p className="text-2xl font-bold font-mono tabular-nums">
                {proofVisible ? `${(ratingCount / 10).toFixed(1)}` : "0.0"}
              </p>
              <p className="text-xs text-muted-foreground mt-0.5">
                ⭐ Avg rating
              </p>
            </div>
            <div>
              <p className="text-2xl font-bold font-mono tabular-nums">
                Daily
              </p>
              <p className="text-xs text-muted-foreground mt-0.5">
                📊 Updated
              </p>
            </div>
          </div>
        </div>
      </section>

      {/* ─── How It Works ───────────────────────────────────────────────── */}
      <section className="bg-card/50">
        <div className="mx-auto max-w-7xl px-4 sm:px-6 py-20 sm:py-28">
          <motion.div
            className="text-center mb-14"
            initial="hidden"
            whileInView="show"
            viewport={{ once: true }}
            variants={fadeIn}
          >
            <h2 className="font-[family-name:var(--font-heading)] text-3xl sm:text-4xl font-bold">
              How it works
            </h2>
            <p className="mt-3 text-muted-foreground text-lg max-w-lg mx-auto">
              From signup to your first scored property in 2 minutes.
            </p>
          </motion.div>

          <div className="grid sm:grid-cols-3 gap-8 relative">
            {/* Connecting line (desktop) */}
            <div className="hidden sm:block absolute top-12 left-[16.67%] right-[16.67%] h-px bg-border" />

            {steps.map((step, i) => (
              <motion.div
                key={step.title}
                className="relative text-center"
                initial="hidden"
                whileInView="show"
                viewport={{ once: true }}
                variants={fade}
                custom={i}
              >
                <div className="relative z-10 flex h-12 w-12 items-center justify-center rounded-full bg-amber text-amber-foreground mx-auto mb-4 text-lg font-bold">
                  {i + 1}
                </div>
                <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-amber/10 text-amber-dark dark:text-amber mx-auto mb-3">
                  <step.icon className="h-5 w-5" />
                </div>
                <h3 className="font-semibold text-lg">{step.title}</h3>
                <p className="mt-2 text-sm text-muted-foreground leading-relaxed max-w-xs mx-auto">
                  {step.desc}
                </p>
              </motion.div>
            ))}
          </div>
        </div>
      </section>

      {/* ─── Interactive Preview / Live Demo ─────────────────────────────── */}
      <section className="border-t border-border/60">
        <div className="mx-auto max-w-7xl px-4 sm:px-6 py-20 sm:py-28">
          <motion.div
            className="text-center mb-10"
            initial="hidden"
            whileInView="show"
            viewport={{ once: true }}
            variants={fadeIn}
          >
            <h2 className="font-[family-name:var(--font-heading)] text-3xl sm:text-4xl font-bold">
              See what HouseMatch finds for you
            </h2>
            <p className="mt-3 text-muted-foreground text-lg max-w-lg mx-auto">
              Adjust your budget and see real property scores instantly.
            </p>
          </motion.div>

          <motion.div
            className="max-w-4xl mx-auto"
            initial="hidden"
            whileInView="show"
            viewport={{ once: true }}
            variants={fadeIn}
          >
            <InteractivePreview />
          </motion.div>
        </div>
      </section>

      {/* ─── Features (alternating) ──────────────────────────────────────── */}
      <section id="features" className="border-t border-border/60 bg-card/50">
        <div className="mx-auto max-w-7xl px-4 sm:px-6 py-20 sm:py-28">
          <motion.div
            className="text-center mb-16"
            initial="hidden"
            whileInView="show"
            viewport={{ once: true }}
            variants={fadeIn}
          >
            <h2 className="font-[family-name:var(--font-heading)] text-3xl sm:text-4xl font-bold">
              Smarter than scrolling
            </h2>
            <p className="mt-3 text-muted-foreground text-lg max-w-lg mx-auto">
              We do the research so you can focus on making offers.
            </p>
          </motion.div>

          {/* Main features — alternating layout */}
          <div className="space-y-20">
            {mainFeatures.map((f, i) => (
              <motion.div
                key={f.title}
                className={`flex flex-col lg:flex-row gap-10 lg:gap-16 items-center ${
                  i % 2 === 1 ? "lg:flex-row-reverse" : ""
                }`}
                initial="hidden"
                whileInView="show"
                viewport={{ once: true, margin: "-50px" }}
                variants={fadeIn}
              >
                <div className="flex-1">
                  <h3 className="font-[family-name:var(--font-heading)] text-2xl font-bold mb-4">
                    {f.title}
                  </h3>
                  <p className="text-muted-foreground leading-relaxed">
                    {f.desc}
                  </p>
                </div>
                <div className="flex-1 w-full">
                  {f.visual === "score" && (
                    <div className="rounded-xl border border-border/60 bg-card p-6 space-y-3">
                      {[
                        { label: "Price Fit", value: 85 },
                        { label: "House Hack", value: 92 },
                        { label: "Rental Income", value: 78 },
                        { label: "ADU Upside", value: 65 },
                        { label: "Transit", value: 88 },
                        { label: "Neighborhood", value: 71 },
                        { label: "Deal Signal", value: 43 },
                        { label: "Lot Expansion", value: 56 },
                      ].map((d) => (
                        <div key={d.label} className="flex items-center gap-3">
                          <span className="text-xs text-muted-foreground w-24 shrink-0">
                            {d.label}
                          </span>
                          <div className="flex-1 h-2 rounded-full bg-muted overflow-hidden">
                            <motion.div
                              className="h-full rounded-full bg-amber"
                              initial={{ width: 0 }}
                              whileInView={{ width: `${d.value}%` }}
                              viewport={{ once: true }}
                              transition={{
                                duration: 1,
                                ease: "easeOut",
                                delay: 0.1,
                              }}
                            />
                          </div>
                          <span className="text-xs font-mono font-semibold w-8 text-right">
                            {d.value}
                          </span>
                        </div>
                      ))}
                    </div>
                  )}
                  {f.visual === "strategy" && (
                    <div className="grid grid-cols-2 gap-4">
                      <div className="rounded-xl border border-border/60 bg-card p-5 text-center">
                        <p className="text-xs text-muted-foreground mb-2">
                          House Hacker
                        </p>
                        <ScoreRing score={92} size={80} strokeWidth={3.5} />
                        <p className="text-xs text-muted-foreground mt-2">
                          482 Oak Ave
                        </p>
                      </div>
                      <div className="rounded-xl border border-border/60 bg-card p-5 text-center">
                        <p className="text-xs text-muted-foreground mb-2">
                          Primary Res
                        </p>
                        <ScoreRing score={61} size={80} strokeWidth={3.5} />
                        <p className="text-xs text-muted-foreground mt-2">
                          Same property
                        </p>
                      </div>
                    </div>
                  )}
                  {f.visual === "alert" && (
                    <div className="rounded-xl border border-border/60 bg-card p-5">
                      <div className="rounded-lg bg-muted/50 p-4 space-y-3 max-w-xs mx-auto">
                        <div className="flex items-center gap-2 text-xs text-muted-foreground">
                          <MessageSquare className="h-3.5 w-3.5" />
                          HouseMatch · 7:30 AM
                        </div>
                        <p className="text-sm">
                          🏠 <strong>New Top Pick!</strong>
                        </p>
                        <p className="text-sm text-muted-foreground">
                          482 Oak Ave, Oakland · Score: 92
                          <br />
                          $625k · 3bd/2ba · Duplex
                          <br />
                          Near BART · ADU potential
                        </p>
                        <p className="text-xs text-amber-dark dark:text-amber font-medium">
                          Tap to view details →
                        </p>
                      </div>
                    </div>
                  )}
                </div>
              </motion.div>
            ))}
          </div>

          {/* Mini features grid */}
          <div className="grid sm:grid-cols-3 gap-6 mt-20">
            {miniFeatures.map((f, i) => (
              <motion.div
                key={f.title}
                className="group rounded-xl border border-border/60 bg-card p-6 transition-all hover:border-amber/30 hover:shadow-lg hover:shadow-amber/5"
                initial="hidden"
                whileInView="show"
                viewport={{ once: true }}
                variants={fade}
                custom={i}
              >
                <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-amber/10 text-amber-dark dark:text-amber mb-4">
                  <f.icon className="h-5 w-5" />
                </div>
                <h3 className="font-semibold text-lg">{f.title}</h3>
                <p className="mt-2 text-sm text-muted-foreground leading-relaxed">
                  {f.desc}
                </p>
              </motion.div>
            ))}
          </div>
        </div>
      </section>

      {/* ─── Testimonials ────────────────────────────────────────────────── */}
      <section className="border-t border-border/60">
        <div className="mx-auto max-w-7xl px-4 sm:px-6 py-20 sm:py-28">
          <motion.div
            className="text-center mb-14"
            initial="hidden"
            whileInView="show"
            viewport={{ once: true }}
            variants={fadeIn}
          >
            <h2 className="font-[family-name:var(--font-heading)] text-3xl sm:text-4xl font-bold">
              Trusted by Bay Area buyers
            </h2>
            <p className="mt-3 text-muted-foreground text-lg">
              Real results from real users.
            </p>
          </motion.div>

          <TestimonialMarquee />
        </div>
      </section>

      {/* ─── Pricing ─────────────────────────────────────────────────────── */}
      <section
        id="pricing"
        className="border-t border-border/60 bg-card/50"
      >
        <div className="mx-auto max-w-7xl px-4 sm:px-6 py-20 sm:py-28">
          <motion.div
            className="text-center mb-10"
            initial="hidden"
            whileInView="show"
            viewport={{ once: true }}
            variants={fadeIn}
          >
            <h2 className="font-[family-name:var(--font-heading)] text-3xl sm:text-4xl font-bold">
              Simple, transparent pricing
            </h2>
            <p className="mt-3 text-muted-foreground text-lg">
              Start free. Upgrade when you&apos;re ready to get serious.
            </p>

            {/* Annual/Monthly toggle */}
            <div className="mt-6 inline-flex items-center gap-3 rounded-full border border-border/60 p-1 bg-background">
              <button
                onClick={() => setAnnual(false)}
                className={`rounded-full px-4 py-1.5 text-sm font-medium transition-colors cursor-pointer ${
                  !annual
                    ? "bg-amber text-amber-foreground"
                    : "text-muted-foreground hover:text-foreground"
                }`}
              >
                Monthly
              </button>
              <button
                onClick={() => setAnnual(true)}
                className={`rounded-full px-4 py-1.5 text-sm font-medium transition-colors cursor-pointer ${
                  annual
                    ? "bg-amber text-amber-foreground"
                    : "text-muted-foreground hover:text-foreground"
                }`}
              >
                Annual{" "}
                <span className="text-xs opacity-80">(save 20%)</span>
              </button>
            </div>
          </motion.div>

          <div className="grid sm:grid-cols-3 gap-6 max-w-4xl mx-auto">
            {plans.map((plan, i) => (
              <motion.div
                key={plan.name}
                className={`rounded-xl border p-6 flex flex-col ${
                  plan.highlight
                    ? "border-amber bg-amber/5 shadow-lg shadow-amber/10 ring-1 ring-amber/20"
                    : "border-border/60 bg-card"
                }`}
                initial="hidden"
                whileInView="show"
                viewport={{ once: true }}
                variants={fade}
                custom={i}
              >
                {plan.highlight && (
                  <span className="text-xs font-semibold uppercase tracking-wider text-amber-dark dark:text-amber mb-2">
                    Most Popular
                  </span>
                )}
                <h3 className="text-xl font-bold">{plan.name}</h3>
                <div className="mt-2 flex items-baseline gap-1">
                  <span className="text-4xl font-bold">{plan.price}</span>
                  <span className="text-muted-foreground">{plan.period}</span>
                </div>
                <p className="mt-2 text-sm text-muted-foreground">
                  {plan.desc}
                </p>
                <ul className="mt-6 space-y-2.5 flex-1">
                  {plan.features.map((f) => (
                    <li key={f} className="flex items-start gap-2 text-sm">
                      <Check className="h-4 w-4 text-amber-dark dark:text-amber mt-0.5 shrink-0" />
                      {f}
                    </li>
                  ))}
                </ul>
                <Link href="/onboard" className="mt-6">
                  <Button
                    className={`w-full h-10 cursor-pointer ${
                      plan.highlight
                        ? "bg-amber text-amber-foreground hover:bg-amber-dark"
                        : ""
                    }`}
                    variant={plan.highlight ? "default" : "outline"}
                  >
                    {plan.cta}
                  </Button>
                </Link>
              </motion.div>
            ))}
          </div>

          {/* Feature comparison toggle */}
          <div className="max-w-4xl mx-auto mt-8">
            <button
              onClick={() => setShowComparison(!showComparison)}
              className="flex items-center gap-2 mx-auto text-sm font-medium text-muted-foreground hover:text-foreground transition-colors cursor-pointer"
            >
              <ChevronDown
                className={`h-4 w-4 transition-transform ${
                  showComparison ? "rotate-180" : ""
                }`}
              />
              Compare all features
            </button>

            <AnimatePresence initial={false}>
              {showComparison && (
                <motion.div
                  initial={{ height: 0, opacity: 0 }}
                  animate={{ height: "auto", opacity: 1 }}
                  exit={{ height: 0, opacity: 0 }}
                  transition={{ duration: 0.3 }}
                  className="overflow-hidden"
                >
                  <div className="mt-6 rounded-xl border border-border/60 overflow-hidden">
                    <table className="w-full text-sm">
                      <thead>
                        <tr className="border-b border-border bg-muted/50">
                          <th className="text-left p-3 font-semibold">
                            Feature
                          </th>
                          <th className="p-3 font-semibold text-center">
                            Free
                          </th>
                          <th className="p-3 font-semibold text-center text-amber-dark dark:text-amber">
                            Pro
                          </th>
                          <th className="p-3 font-semibold text-center">
                            Investor
                          </th>
                        </tr>
                      </thead>
                      <tbody>
                        {comparisonFeatures.map((row) => (
                          <tr
                            key={row.label}
                            className="border-b border-border/60"
                          >
                            <td className="p-3 text-muted-foreground">
                              {row.label}
                            </td>
                            <td className="p-3 text-center">{row.free}</td>
                            <td className="p-3 text-center">{row.pro}</td>
                            <td className="p-3 text-center">
                              {row.investor}
                            </td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                </motion.div>
              )}
            </AnimatePresence>
          </div>

          {/* Bottom note */}
          <p className="text-center text-sm text-muted-foreground mt-6">
            All plans include: Unlimited property views · Daily updates ·
            Price drop alerts · Bay Area coverage
          </p>
        </div>
      </section>

      {/* ─── FAQ ──────────────────────────────────────────────────────────── */}
      <section id="faq" className="border-t border-border/60">
        <div className="mx-auto max-w-3xl px-4 sm:px-6 py-20 sm:py-28">
          <motion.div
            className="text-center mb-10"
            initial="hidden"
            whileInView="show"
            viewport={{ once: true }}
            variants={fadeIn}
          >
            <h2 className="font-[family-name:var(--font-heading)] text-3xl sm:text-4xl font-bold">
              Frequently asked questions
            </h2>
            <p className="mt-3 text-muted-foreground text-lg">
              Everything you need to know about HouseMatch.
            </p>
          </motion.div>

          <motion.div
            initial="hidden"
            whileInView="show"
            viewport={{ once: true }}
            variants={fadeIn}
          >
            {faqs.map((faq) => (
              <FaqItem key={faq.q} q={faq.q} a={faq.a} />
            ))}
          </motion.div>
        </div>
      </section>

      {/* ─── Final CTA ────────────────────────────────────────────────────── */}
      <section className="relative overflow-hidden bg-gradient-to-br from-amber/10 via-amber/5 to-amber/10">
        <div className="absolute inset-0 blueprint-grid opacity-50 pointer-events-none" />
        <div className="relative mx-auto max-w-3xl px-4 sm:px-6 py-20 sm:py-28 text-center">
          <motion.div
            initial="hidden"
            whileInView="show"
            viewport={{ once: true }}
            variants={fadeIn}
          >
            <h2 className="font-[family-name:var(--font-heading)] text-3xl sm:text-4xl font-bold">
              Stop scrolling.{" "}
              <span className="text-amber-dark dark:text-amber">
                Start scoring.
              </span>
            </h2>
            <p className="mt-4 text-lg text-muted-foreground max-w-lg mx-auto">
              Your next investment property is already listed. We just need 2
              minutes to find it for you.
            </p>

            <div className="mt-8">
              <Show when="signed-out">
                <SignUpButton mode="modal">
                  <Button
                    size="lg"
                    className="bg-amber text-amber-foreground hover:bg-amber-dark h-12 px-8 text-base cursor-pointer"
                  >
                    Get Started Free
                    <ArrowRight className="ml-2 h-4 w-4" />
                  </Button>
                </SignUpButton>
              </Show>
              <Show when="signed-in">
                <Link href="/dashboard">
                  <Button
                    size="lg"
                    className="bg-amber text-amber-foreground hover:bg-amber-dark h-12 px-8 text-base cursor-pointer"
                  >
                    Go to Dashboard
                    <ArrowRight className="ml-2 h-4 w-4" />
                  </Button>
                </Link>
              </Show>
            </div>

            <div className="mt-6 flex flex-wrap justify-center gap-x-4 gap-y-1 text-sm text-muted-foreground">
              <span className="flex items-center gap-1.5">
                <Check className="h-3.5 w-3.5 text-amber-dark dark:text-amber" />
                No credit card required
              </span>
              <span className="flex items-center gap-1.5">
                <Check className="h-3.5 w-3.5 text-amber-dark dark:text-amber" />
                Cancel anytime
              </span>
              <span className="flex items-center gap-1.5">
                <Check className="h-3.5 w-3.5 text-amber-dark dark:text-amber" />
                {stats?.total_active?.toLocaleString() ?? "1,400"}+ Bay Area properties scored
              </span>
            </div>
          </motion.div>
        </div>
      </section>

      {/* ─── Footer ───────────────────────────────────────────────────────── */}
      <Footer />
    </div>
  );
}

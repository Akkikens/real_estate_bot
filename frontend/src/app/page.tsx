"use client";

import Link from "next/link";
import { motion } from "framer-motion";
import {
  ArrowRight,
  Zap,
  Bell,
  BarChart3,
  Shield,
  Star,
  Check,
  MapPin,
  TrendingUp,
  Home,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { Navbar } from "@/components/navbar";
import { ScoreRing } from "@/components/score-ring";

const fade = {
  hidden: { opacity: 0, y: 24 },
  show: (i: number) => ({
    opacity: 1,
    y: 0,
    transition: { delay: i * 0.1, duration: 0.5, ease: "easeOut" as const },
  }),
};

const features = [
  {
    icon: BarChart3,
    title: "AI-Powered Scoring",
    desc: "Every listing scored 0–100 across 8 dimensions tailored to your strategy.",
  },
  {
    icon: Bell,
    title: "Daily Alerts",
    desc: "Top picks delivered to your phone via SMS or WhatsApp at the time you choose.",
  },
  {
    icon: MapPin,
    title: "Bay Area Focus",
    desc: "Deep data on BART proximity, ADU potential, rental comps, and neighborhood safety.",
  },
  {
    icon: TrendingUp,
    title: "House-Hack Ready",
    desc: "Built for house-hackers: rental income estimates, in-law potential, and cash-flow analysis.",
  },
  {
    icon: Shield,
    title: "Multi-Source Data",
    desc: "We pull from Redfin, Zillow, Realtor.com, and more — no single-source blind spots.",
  },
  {
    icon: Zap,
    title: "Instant Watchlist",
    desc: "Save favorites, track price drops, and get alerted when a deal gets even better.",
  },
];

const plans = [
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

const testimonials = [
  {
    name: "Priya M.",
    role: "First-time buyer, Fremont",
    text: "Found my house-hack duplex in 2 weeks. The ADU scoring alone saved me months of manual research.",
    score: 87,
  },
  {
    name: "Marcus T.",
    role: "Investor, Oakland",
    text: "I was spending 3 hours a day on Redfin. Now I get the top 5 deals texted to me before breakfast.",
    score: 92,
  },
  {
    name: "Sarah K.",
    role: "House-hacker, San Jose",
    text: "The BART proximity scoring is genius. My rental income covers 80% of my mortgage now.",
    score: 78,
  },
];

export default function LandingPage() {
  return (
    <div className="min-h-screen">
      <Navbar />

      {/* Hero */}
      <section className="relative overflow-hidden blueprint-grid">
        <div className="mx-auto max-w-7xl px-4 sm:px-6 py-20 sm:py-32">
          <div className="max-w-3xl">
            <motion.div
              initial="hidden"
              animate="show"
              variants={fade}
              custom={0}
            >
              <span className="inline-flex items-center gap-2 rounded-full bg-amber/10 px-3 py-1 text-sm font-medium text-amber-dark dark:text-amber mb-6">
                <Zap className="h-3.5 w-3.5" />
                AI-powered property intelligence
              </span>
            </motion.div>

            <motion.h1
              className="font-[family-name:var(--font-heading)] text-4xl sm:text-6xl lg:text-7xl font-bold tracking-tight leading-[1.1]"
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
              Stop scrolling Redfin for hours. Get personalized property scores
              delivered daily — tuned to your budget, strategy, and must-haves.
            </motion.p>

            <motion.div
              className="mt-8 flex flex-col sm:flex-row gap-3"
              initial="hidden"
              animate="show"
              variants={fade}
              custom={3}
            >
              <Link href="/onboard">
                <Button
                  size="lg"
                  className="bg-amber text-amber-foreground hover:bg-amber-dark h-12 px-6 text-base"
                >
                  Get Started Free
                  <ArrowRight className="ml-2 h-4 w-4" />
                </Button>
              </Link>
              <Link href="#pricing">
                <Button variant="outline" size="lg" className="h-12 px-6 text-base">
                  View Pricing
                </Button>
              </Link>
            </motion.div>
          </div>

          {/* Floating score card */}
          <motion.div
            className="absolute right-8 top-32 hidden xl:block"
            initial={{ opacity: 0, x: 40 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ delay: 0.6, duration: 0.7 }}
          >
            <div className="rounded-2xl border border-border/60 bg-card/80 backdrop-blur-lg p-5 shadow-xl w-72">
              <div className="flex items-start justify-between">
                <div>
                  <p className="text-xs text-muted-foreground">Top Pick Today</p>
                  <p className="font-semibold mt-1">1247 Elm St</p>
                  <p className="text-sm text-muted-foreground">Fremont, CA</p>
                </div>
                <ScoreRing score={87} size={64} strokeWidth={3} />
              </div>
              <div className="mt-4 grid grid-cols-3 gap-2 text-center">
                <div className="rounded-lg bg-muted/50 p-2">
                  <p className="text-xs text-muted-foreground">Price</p>
                  <p className="text-sm font-semibold">$789k</p>
                </div>
                <div className="rounded-lg bg-muted/50 p-2">
                  <p className="text-xs text-muted-foreground">Beds</p>
                  <p className="text-sm font-semibold">4</p>
                </div>
                <div className="rounded-lg bg-muted/50 p-2">
                  <p className="text-xs text-muted-foreground">BART</p>
                  <p className="text-sm font-semibold">0.8 mi</p>
                </div>
              </div>
              <div className="mt-3 flex gap-1">
                {["House Hack", "ADU", "Near BART"].map((tag) => (
                  <span
                    key={tag}
                    className="rounded-md bg-amber/10 px-2 py-0.5 text-[10px] font-medium text-amber-dark dark:text-amber"
                  >
                    {tag}
                  </span>
                ))}
              </div>
            </div>
          </motion.div>
        </div>
      </section>

      {/* Features */}
      <section className="border-t border-border/60 bg-card/50">
        <div className="mx-auto max-w-7xl px-4 sm:px-6 py-20 sm:py-28">
          <div className="text-center mb-14">
            <h2 className="font-[family-name:var(--font-heading)] text-3xl sm:text-4xl font-bold">
              Smarter than scrolling
            </h2>
            <p className="mt-3 text-muted-foreground text-lg max-w-lg mx-auto">
              We do the research so you can focus on making offers.
            </p>
          </div>
          <div className="grid sm:grid-cols-2 lg:grid-cols-3 gap-6">
            {features.map((f, i) => (
              <motion.div
                key={f.title}
                className="group rounded-xl border border-border/60 bg-card p-6 transition-all hover:border-amber/30 hover:shadow-lg hover:shadow-amber/5"
                initial="hidden"
                whileInView="show"
                viewport={{ once: true, margin: "-50px" }}
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

      {/* Social Proof */}
      <section className="border-t border-border/60">
        <div className="mx-auto max-w-7xl px-4 sm:px-6 py-20 sm:py-28">
          <div className="text-center mb-14">
            <h2 className="font-[family-name:var(--font-heading)] text-3xl sm:text-4xl font-bold">
              Trusted by Bay Area buyers
            </h2>
          </div>
          <div className="grid sm:grid-cols-3 gap-6">
            {testimonials.map((t, i) => (
              <motion.div
                key={t.name}
                className="rounded-xl border border-border/60 bg-card p-6"
                initial="hidden"
                whileInView="show"
                viewport={{ once: true }}
                variants={fade}
                custom={i}
              >
                <div className="flex items-center gap-1 mb-4">
                  {[...Array(5)].map((_, j) => (
                    <Star
                      key={j}
                      className="h-4 w-4 fill-amber text-amber"
                    />
                  ))}
                </div>
                <p className="text-sm leading-relaxed text-muted-foreground">
                  &ldquo;{t.text}&rdquo;
                </p>
                <div className="mt-4 flex items-center justify-between">
                  <div>
                    <p className="font-semibold text-sm">{t.name}</p>
                    <p className="text-xs text-muted-foreground">{t.role}</p>
                  </div>
                  <ScoreRing score={t.score} size={44} strokeWidth={2.5} showLabel={false} />
                </div>
              </motion.div>
            ))}
          </div>
        </div>
      </section>

      {/* Pricing */}
      <section id="pricing" className="border-t border-border/60 bg-card/50">
        <div className="mx-auto max-w-7xl px-4 sm:px-6 py-20 sm:py-28">
          <div className="text-center mb-14">
            <h2 className="font-[family-name:var(--font-heading)] text-3xl sm:text-4xl font-bold">
              Simple pricing
            </h2>
            <p className="mt-3 text-muted-foreground text-lg">
              Start free. Upgrade when you&apos;re ready to get serious.
            </p>
          </div>
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
                    className={`w-full h-10 ${
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
        </div>
      </section>

      {/* Footer */}
      <footer className="border-t border-border/60 py-10">
        <div className="mx-auto max-w-7xl px-4 sm:px-6 flex flex-col sm:flex-row items-center justify-between gap-4">
          <div className="flex items-center gap-2.5">
            <div className="flex h-7 w-7 items-center justify-center rounded-lg bg-amber text-amber-foreground font-bold text-xs">
              H
            </div>
            <span className="font-[family-name:var(--font-heading)] font-semibold">
              HouseMatch
            </span>
          </div>
          <p className="text-sm text-muted-foreground">
            &copy; 2026 HouseMatch. Built for Bay Area house-hackers.
          </p>
        </div>
      </footer>
    </div>
  );
}

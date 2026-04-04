"use client";

import { useState, useCallback, useEffect, useMemo } from "react";
import { useRouter } from "next/navigation";
import { motion, AnimatePresence } from "framer-motion";
import confetti from "canvas-confetti";
import {
  ArrowRight,
  ArrowLeft,
  DollarSign,
  Target,
  ListChecks,
  Bell,
  Rocket,
  Check,
  Home,
  Repeat,
  Wrench,
  Building,
  Train,
  Trees,
  ShieldCheck,
  GraduationCap,
  Car,
  Bath,
  Bed,
  Zap,
  Loader2,
  MapPin,
  Droplets,
  AlertTriangle,
  Clock,
  Volume2,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { Slider } from "@/components/ui/slider";
import { Switch } from "@/components/ui/switch";
import { Label } from "@/components/ui/label";
import { Input } from "@/components/ui/input";
import { Navbar } from "@/components/navbar";
import { ScoreRing } from "@/components/score-ring";
import { useAuth, useUser, SignInButton } from "@clerk/nextjs";
import { useMarket, useProperties } from "@/lib/queries";
import { api } from "@/lib/api";

// ── Constants ────────────────────────────────────────────────────────────────

const STORAGE_KEY = "hm_onboard_progress";

const steps = [
  { label: "Budget", icon: DollarSign },
  { label: "Strategy", icon: Target },
  { label: "Must-Haves", icon: ListChecks },
  { label: "Alerts", icon: Bell },
  { label: "Launch", icon: Rocket },
];

const strategies = [
  {
    id: "house_hack",
    label: "House-Hack",
    icon: Home,
    desc: "Live in one unit, rent the others. Offset your mortgage.",
    example: "Buy a 4BR in Oakland for $650k → rent 3 rooms at $1,400/ea → cover 85% of your mortgage from day one.",
    popular: true,
  },
  {
    id: "buy_hold",
    label: "Buy & Hold",
    icon: Repeat,
    desc: "Long-term rental income and appreciation play.",
    example: "Buy a duplex in Richmond for $550k → rent both units → $400/mo positive cash flow after PITI.",
  },
  {
    id: "primary",
    label: "Primary Residence",
    icon: Building,
    desc: "Finding the perfect home to live in.",
    example: "Find a 3BR in Fremont near BART for $850k → score 80+ on transit, schools, and neighborhood safety.",
  },
  {
    id: "fix_flip",
    label: "Fix & Flip",
    icon: Wrench,
    desc: "Buy undervalued, renovate, sell for profit.",
    example: "Buy a fixer in El Cerrito for $500k → $80k renovation → sell for $700k → $120k profit before tax.",
  },
];

const mustHaves = [
  { id: "3bed", label: "3+ Bedrooms", icon: Bed },
  { id: "adu", label: "ADU / In-law", icon: Building },
  { id: "bart", label: "Near Transit", icon: Train },
  { id: "pool", label: "Pool", icon: Bath },
  { id: "garage", label: "Garage", icon: Car },
  { id: "large-lot", label: "Large Lot", icon: Trees },
  { id: "duplex", label: "Duplex / Multi-unit", icon: Home },
  { id: "schools", label: "Good Schools", icon: GraduationCap },
  { id: "low-crime", label: "Low Crime", icon: ShieldCheck },
];

const dealBreakerOptions = [
  { id: "hoa_500", label: "HOA > $500/mo", icon: DollarSign },
  { id: "flood_zone", label: "Flood zone", icon: Droplets },
  { id: "age_50", label: "Age > 50 years", icon: Clock },
  { id: "busy_street", label: "Busy street / highway", icon: Volume2 },
  { id: "full_reno", label: "Full renovation needed", icon: AlertTriangle },
];

// ── Types ────────────────────────────────────────────────────────────────────

interface OnboardData {
  max_price: number;
  down_payment_pct: number;
  target_cities: string[];
  strategy: string | null;
  must_haves: string[];
  deal_breakers: string[];
  alert_channels: { sms: boolean; whatsapp: boolean; email: boolean };
  alert_time: string;
  alert_score_threshold: number;
}

interface OnboardProgress {
  step: number;
  data: OnboardData;
  updated_at: string;
}

const DEFAULT_DATA: OnboardData = {
  max_price: 850000,
  down_payment_pct: 20,
  target_cities: [],
  strategy: null,
  must_haves: [],
  deal_breakers: [],
  alert_channels: { sms: true, whatsapp: false, email: true },
  alert_time: "08:00",
  alert_score_threshold: 65,
};

// ── Helpers ──────────────────────────────────────────────────────────────────

function formatPrice(val: number) {
  if (val >= 1000000) return `$${(val / 1000000).toFixed(1)}M`;
  return `$${(val / 1000).toFixed(0)}k`;
}

function loadProgress(): OnboardProgress | null {
  if (typeof window === "undefined") return null;
  try {
    const raw = localStorage.getItem(STORAGE_KEY);
    if (!raw) return null;
    const parsed = JSON.parse(raw) as OnboardProgress;
    // Expire after 30 days
    const age = Date.now() - new Date(parsed.updated_at).getTime();
    if (age > 30 * 24 * 60 * 60 * 1000) {
      localStorage.removeItem(STORAGE_KEY);
      return null;
    }
    return parsed;
  } catch {
    return null;
  }
}

function saveProgress(step: number, data: OnboardData) {
  if (typeof window === "undefined") return;
  const progress: OnboardProgress = {
    step,
    data,
    updated_at: new Date().toISOString(),
  };
  localStorage.setItem(STORAGE_KEY, JSON.stringify(progress));
}

function clearProgress() {
  if (typeof window === "undefined") return;
  localStorage.removeItem(STORAGE_KEY);
}

function getScoreThresholdColor(value: number) {
  if (value >= 80) return "text-green-600 dark:text-green-400";
  if (value >= 65) return "text-amber-dark dark:text-amber";
  if (value >= 50) return "text-yellow-600 dark:text-yellow-400";
  return "text-red-500";
}

// ── Monthly Payment Estimate ─────────────────────────────────────────────────

function estimateMonthly(price: number, downPct: number) {
  const rate = 0.0725 / 12; // 7.25% annual
  const loan = price * (1 - downPct / 100);
  const n = 360; // 30 years
  const pi = loan * (rate * Math.pow(1 + rate, n)) / (Math.pow(1 + rate, n) - 1);
  return Math.round(pi);
}

// ── Component ────────────────────────────────────────────────────────────────

export default function OnboardPage() {
  const router = useRouter();
  const { isSignedIn } = useAuth();
  const { user: clerkUser } = useUser();

  // Initialize from localStorage
  const [initialized, setInitialized] = useState(false);
  const [step, setStep] = useState(0);
  const [data, setData] = useState<OnboardData>(DEFAULT_DATA);
  const [saving, setSaving] = useState(false);
  const [launching, setLaunching] = useState(false);

  // Load market cities
  const marketId = (clerkUser?.publicMetadata?.market_id as string) || "bay_area";
  const { data: market } = useMarket(marketId);
  const cities = market?.cities || [];

  // If onboarding is already complete, redirect to dashboard
  useEffect(() => {
    if (clerkUser?.publicMetadata?.onboarding_complete === true) {
      router.replace("/dashboard");
    }
  }, [clerkUser, router]);

  // Restore from localStorage on mount
  useEffect(() => {
    const saved = loadProgress();
    if (saved) {
      setStep(saved.step);
      setData({ ...DEFAULT_DATA, ...saved.data });
    }
    setInitialized(true);
  }, []);

  // Save to localStorage on any data/step change
  useEffect(() => {
    if (initialized) {
      saveProgress(step, data);
    }
  }, [step, data, initialized]);

  // Fetch preview properties for Step 5
  const previewFilters = useMemo(() => ({
    page: 1,
    page_size: 3,
    sort: "score" as const,
    max_price: data.max_price,
    ...(data.target_cities.length === 1 ? { city: data.target_cities[0] } : {}),
  }), [data.max_price, data.target_cities]);

  const { data: previewProps } = useProperties(previewFilters);

  // ── Data updaters ──────────────────────────────────────────────────────────

  const updateData = useCallback((updates: Partial<OnboardData>) => {
    setData((prev) => ({ ...prev, ...updates }));
  }, []);

  const toggleCity = useCallback((city: string) => {
    setData((prev) => ({
      ...prev,
      target_cities: prev.target_cities.includes(city)
        ? prev.target_cities.filter((c) => c !== city)
        : [...prev.target_cities, city],
    }));
  }, []);

  const toggleMustHave = useCallback((id: string) => {
    setData((prev) => ({
      ...prev,
      must_haves: prev.must_haves.includes(id)
        ? prev.must_haves.filter((x) => x !== id)
        : [...prev.must_haves, id],
    }));
  }, []);

  const toggleDealBreaker = useCallback((id: string) => {
    setData((prev) => ({
      ...prev,
      deal_breakers: prev.deal_breakers.includes(id)
        ? prev.deal_breakers.filter((x) => x !== id)
        : [...prev.deal_breakers, id],
    }));
  }, []);

  // ── Validation ─────────────────────────────────────────────────────────────

  const canNext =
    step === 0
      ? data.target_cities.length > 0
      : step === 1
      ? data.strategy !== null
      : true;

  // ── Save to backend ────────────────────────────────────────────────────────

  const saveCurrentStep = useCallback(async () => {
    if (!isSignedIn) return;

    try {
      setSaving(true);
      const updates: Record<string, unknown> = {};

      if (step === 0) {
        updates.max_price = data.max_price;
        updates.down_payment_pct = data.down_payment_pct;
        updates.target_cities = data.target_cities;
      } else if (step === 1) {
        updates.strategy = data.strategy;
      } else if (step === 2) {
        updates.must_haves = data.must_haves;
        updates.deal_breakers = data.deal_breakers;
      } else if (step === 3) {
        updates.alert_channels = data.alert_channels;
        updates.alert_time = data.alert_time;
        updates.alert_score_threshold = data.alert_score_threshold;
      }

      await api.put("/api/profile/preferences", updates);
    } catch (err) {
      console.error("Failed to save preferences:", err);
    } finally {
      setSaving(false);
    }
  }, [isSignedIn, step, data]);

  // ── Navigation ─────────────────────────────────────────────────────────────

  const handleNext = async () => {
    await saveCurrentStep();
    if (step < steps.length - 1) {
      setStep(step + 1);
    }
  };

  const handleBack = () => {
    if (step > 0) setStep(step - 1);
  };

  const handleLaunch = async () => {
    setLaunching(true);

    // Final save of all preferences
    if (isSignedIn) {
      try {
        await api.put("/api/profile/preferences", {
          max_price: data.max_price,
          down_payment_pct: data.down_payment_pct,
          target_cities: data.target_cities,
          strategy: data.strategy,
          must_haves: data.must_haves,
          deal_breakers: data.deal_breakers,
          alert_channels: data.alert_channels,
          alert_time: data.alert_time,
          alert_score_threshold: data.alert_score_threshold,
        });

        // Mark onboarding complete via API (which sets Clerk metadata)
        try {
          await api.post("/api/profile/onboarding-complete");
        } catch {
          // Non-critical — don't block launch
        }
      } catch (err) {
        console.error("Failed final save:", err);
      }
    }

    // Fire confetti!
    confetti({
      particleCount: 150,
      spread: 80,
      origin: { y: 0.6 },
      colors: ["#d4a843", "#f5d78e", "#b8941f", "#fef3c7"],
    });

    clearProgress();

    // Navigate after a short celebration
    setTimeout(() => {
      router.push("/dashboard");
    }, 1500);
  };

  const handleSkip = () => {
    clearProgress();
    router.push("/dashboard");
  };

  // Strategy label for summary
  const strategyLabel = strategies.find((s) => s.id === data.strategy)?.label || "Not set";
  const selectedStrategy = strategies.find((s) => s.id === data.strategy);
  const monthlyEstimate = estimateMonthly(data.max_price, data.down_payment_pct);

  if (!initialized) return null;

  return (
    <div className="min-h-screen">
      <Navbar />
      <div className="mx-auto max-w-2xl px-4 sm:px-6 py-10 sm:py-16">
        {/* Progress */}
        <div className="flex items-center justify-between mb-10">
          {steps.map((s, i) => (
            <div key={s.label} className="flex items-center gap-2 flex-1">
              <button
                onClick={() => i < step && setStep(i)}
                disabled={i >= step}
                className={`flex h-9 w-9 items-center justify-center rounded-full text-sm font-semibold transition-colors ${
                  i < step
                    ? "bg-amber text-amber-foreground cursor-pointer hover:bg-amber-dark"
                    : i === step
                    ? "bg-amber/20 text-amber-dark dark:text-amber border-2 border-amber"
                    : "bg-muted text-muted-foreground"
                }`}
              >
                {i < step ? <Check className="h-4 w-4" /> : i + 1}
              </button>
              <span
                className={`text-sm font-medium hidden sm:inline ${
                  i <= step ? "text-foreground" : "text-muted-foreground"
                }`}
              >
                {s.label}
              </span>
              {i < steps.length - 1 && (
                <div
                  className={`flex-1 h-px mx-2 ${
                    i < step ? "bg-amber" : "bg-border"
                  }`}
                />
              )}
            </div>
          ))}
        </div>

        {/* Unauthenticated banner */}
        {!isSignedIn && (
          <div className="rounded-lg border border-amber/30 bg-amber/5 px-4 py-2.5 mb-6 text-sm text-muted-foreground">
            <SignInButton mode="modal">
              <button className="text-amber-dark dark:text-amber font-medium hover:underline">
                Sign in
              </button>
            </SignInButton>{" "}
            to save your preferences
          </div>
        )}

        {/* Step content */}
        <AnimatePresence mode="wait">
          <motion.div
            key={step}
            initial={{ opacity: 0, x: 20 }}
            animate={{ opacity: 1, x: 0 }}
            exit={{ opacity: 0, x: -20 }}
            transition={{ duration: 0.25 }}
          >
            {/* ── Step 0: Market & Budget ────────────────────────────────── */}
            {step === 0 && (
              <div className="space-y-8">
                <div>
                  <h2 className="font-[family-name:var(--font-heading)] text-2xl sm:text-3xl font-bold">
                    Where are you looking?
                  </h2>
                  <p className="mt-2 text-muted-foreground">
                    Set your market, budget, and target cities.
                  </p>
                </div>

                <div className="space-y-4">
                  <div className="flex items-center justify-between">
                    <Label className="text-sm font-medium">Max Price</Label>
                    <span className="text-2xl font-bold text-amber-dark dark:text-amber">
                      {formatPrice(data.max_price)}
                    </span>
                  </div>
                  <Slider
                    value={[data.max_price]}
                    onValueChange={(v) =>
                      updateData({ max_price: Array.isArray(v) ? v[0] : v })
                    }
                    min={100000}
                    max={3000000}
                    step={25000}
                    className="[&_[role=slider]]:bg-amber [&_[role=slider]]:border-amber"
                  />
                  <div className="flex justify-between text-xs text-muted-foreground">
                    <span>$100k</span>
                    <span>$3M</span>
                  </div>
                  <p className="text-xs text-muted-foreground">
                    ~${monthlyEstimate.toLocaleString()}/mo at 7.25% ({data.down_payment_pct}% down)
                    {data.down_payment_pct < 20 && (
                      <span className="text-amber-dark dark:text-amber ml-1">
                        · PMI adds ~$200/mo
                      </span>
                    )}
                  </p>
                </div>

                <div className="space-y-2">
                  <Label className="text-sm font-medium">Down Payment %</Label>
                  <div className="flex gap-2">
                    {[3.5, 5, 10, 15, 20, 25].map((pct) => (
                      <button
                        key={pct}
                        onClick={() => updateData({ down_payment_pct: pct })}
                        className={`flex-1 rounded-lg border py-2 text-sm font-medium transition-colors ${
                          data.down_payment_pct === pct
                            ? "border-amber bg-amber/10 text-amber-dark dark:text-amber"
                            : "border-border hover:bg-muted"
                        }`}
                      >
                        {pct}%
                      </button>
                    ))}
                  </div>
                </div>

                <div className="space-y-3">
                  <div className="flex items-center justify-between">
                    <Label className="text-sm font-medium">
                      Target Cities
                      {cities.length > 0 && (
                        <span className="text-muted-foreground font-normal ml-2">
                          ({data.target_cities.length} selected)
                        </span>
                      )}
                    </Label>
                    {cities.length > 0 && (
                      <div className="flex gap-2">
                        <button
                          onClick={() => updateData({ target_cities: [...cities] })}
                          className="text-xs text-amber-dark dark:text-amber hover:underline"
                        >
                          Select All
                        </button>
                        <button
                          onClick={() => updateData({ target_cities: [] })}
                          className="text-xs text-muted-foreground hover:underline"
                        >
                          Clear
                        </button>
                      </div>
                    )}
                  </div>
                  <div className="flex flex-wrap gap-2">
                    {cities.map((city) => (
                      <button
                        key={city}
                        onClick={() => toggleCity(city)}
                        className={`rounded-full border px-3 py-1.5 text-sm transition-colors ${
                          data.target_cities.includes(city)
                            ? "border-amber bg-amber/10 text-amber-dark dark:text-amber"
                            : "border-border text-muted-foreground hover:bg-muted hover:text-foreground"
                        }`}
                      >
                        {city}
                      </button>
                    ))}
                    {cities.length === 0 && (
                      <p className="text-sm text-muted-foreground">
                        Loading cities...
                      </p>
                    )}
                  </div>
                </div>
              </div>
            )}

            {/* ── Step 1: Strategy ───────────────────────────────────────── */}
            {step === 1 && (
              <div className="space-y-8">
                <div>
                  <h2 className="font-[family-name:var(--font-heading)] text-2xl sm:text-3xl font-bold">
                    Pick your strategy
                  </h2>
                  <p className="mt-2 text-muted-foreground">
                    This shapes how we score every property for you.
                  </p>
                </div>

                <div className="grid gap-3">
                  {strategies.map((s) => (
                    <button
                      key={s.id}
                      onClick={() => updateData({ strategy: s.id })}
                      className={`flex items-start gap-4 rounded-xl border p-5 text-left transition-all ${
                        data.strategy === s.id
                          ? "border-amber bg-amber/5 ring-1 ring-amber/30"
                          : "border-border hover:border-amber/20 hover:bg-muted/50"
                      }`}
                    >
                      <div
                        className={`flex h-10 w-10 items-center justify-center rounded-lg shrink-0 ${
                          data.strategy === s.id
                            ? "bg-amber text-amber-foreground"
                            : "bg-muted text-muted-foreground"
                        }`}
                      >
                        <s.icon className="h-5 w-5" />
                      </div>
                      <div className="flex-1">
                        <div className="flex items-center gap-2">
                          <p className="font-semibold">{s.label}</p>
                          {"popular" in s && s.popular && (
                            <span className="text-[10px] bg-amber/20 text-amber-dark dark:text-amber px-2 py-0.5 rounded-full font-medium">
                              Most Popular
                            </span>
                          )}
                        </div>
                        <p className="text-sm text-muted-foreground mt-0.5">
                          {s.desc}
                        </p>
                      </div>
                      {data.strategy === s.id && (
                        <div className="ml-auto mt-1">
                          <Check className="h-5 w-5 text-amber" />
                        </div>
                      )}
                    </button>
                  ))}
                </div>

                {/* Strategy example callout */}
                {selectedStrategy && (
                  <motion.div
                    initial={{ opacity: 0, y: 8 }}
                    animate={{ opacity: 1, y: 0 }}
                    className="rounded-lg border border-amber/20 bg-amber/5 p-4"
                  >
                    <p className="text-sm text-muted-foreground">
                      <span className="font-medium text-foreground">Example: </span>
                      {selectedStrategy.example}
                    </p>
                  </motion.div>
                )}
              </div>
            )}

            {/* ── Step 2: Must-Haves + Deal Breakers ────────────────────── */}
            {step === 2 && (
              <div className="space-y-8">
                <div>
                  <h2 className="font-[family-name:var(--font-heading)] text-2xl sm:text-3xl font-bold">
                    What matters most?
                  </h2>
                  <p className="mt-2 text-muted-foreground">
                    Select features you care about. We&apos;ll boost scores for matches.
                  </p>
                </div>

                {/* Must-haves */}
                <div className="space-y-3">
                  <Label className="text-sm font-medium">
                    Must-Haves
                    {data.must_haves.length > 0 && (
                      <span className="text-muted-foreground font-normal ml-2">
                        ({data.must_haves.length} selected)
                      </span>
                    )}
                  </Label>
                  <div className="grid grid-cols-2 sm:grid-cols-3 gap-3">
                    {mustHaves.map((item) => (
                      <button
                        key={item.id}
                        onClick={() => toggleMustHave(item.id)}
                        className={`flex flex-col items-center gap-2 rounded-xl border p-4 transition-all ${
                          data.must_haves.includes(item.id)
                            ? "border-amber bg-amber/5 ring-1 ring-amber/30"
                            : "border-border hover:border-amber/20 hover:bg-muted/50"
                        }`}
                      >
                        <item.icon
                          className={`h-6 w-6 ${
                            data.must_haves.includes(item.id)
                              ? "text-amber-dark dark:text-amber"
                              : "text-muted-foreground"
                          }`}
                        />
                        <span className="text-sm font-medium text-center">
                          {item.label}
                        </span>
                      </button>
                    ))}
                  </div>
                </div>

                {/* Deal-breakers */}
                <div className="space-y-3">
                  <Label className="text-sm font-medium">
                    Deal-Breakers
                    {data.deal_breakers.length > 0 && (
                      <span className="text-muted-foreground font-normal ml-2">
                        ({data.deal_breakers.length} selected)
                      </span>
                    )}
                  </Label>
                  <p className="text-xs text-muted-foreground -mt-1">
                    Properties with these traits will be filtered out or scored lower.
                  </p>
                  <div className="grid grid-cols-2 sm:grid-cols-3 gap-3">
                    {dealBreakerOptions.map((item) => (
                      <button
                        key={item.id}
                        onClick={() => toggleDealBreaker(item.id)}
                        className={`flex flex-col items-center gap-2 rounded-xl border p-4 transition-all ${
                          data.deal_breakers.includes(item.id)
                            ? "border-red-400 bg-red-50 dark:bg-red-950/30 ring-1 ring-red-300"
                            : "border-border hover:border-red-200 hover:bg-muted/50"
                        }`}
                      >
                        <item.icon
                          className={`h-5 w-5 ${
                            data.deal_breakers.includes(item.id)
                              ? "text-red-500"
                              : "text-muted-foreground"
                          }`}
                        />
                        <span className="text-sm font-medium text-center">
                          {item.label}
                        </span>
                      </button>
                    ))}
                  </div>
                </div>
              </div>
            )}

            {/* ── Step 3: Alerts ─────────────────────────────────────────── */}
            {step === 3 && (
              <div className="space-y-8">
                <div>
                  <h2 className="font-[family-name:var(--font-heading)] text-2xl sm:text-3xl font-bold">
                    How should we reach you?
                  </h2>
                  <p className="mt-2 text-muted-foreground">
                    Choose your alert channels and preferred delivery time.
                  </p>
                </div>

                <div className="space-y-4">
                  {[
                    { key: "sms" as const, emoji: "💬", label: "SMS", desc: "Text message alerts" },
                    { key: "whatsapp" as const, emoji: "📱", label: "WhatsApp", desc: "Rich property cards with score breakdowns" },
                    { key: "email" as const, emoji: "📧", label: "Email", desc: "Daily digest with full details" },
                  ].map((ch) => (
                    <div key={ch.key} className="flex items-center justify-between rounded-xl border border-border p-4">
                      <div className="flex items-center gap-3">
                        <span className="text-lg">{ch.emoji}</span>
                        <div>
                          <p className="font-medium text-sm">{ch.label}</p>
                          <p className="text-xs text-muted-foreground">
                            {ch.desc}
                          </p>
                        </div>
                      </div>
                      <Switch
                        checked={data.alert_channels[ch.key]}
                        onCheckedChange={(v) =>
                          updateData({
                            alert_channels: { ...data.alert_channels, [ch.key]: v },
                          })
                        }
                      />
                    </div>
                  ))}
                </div>

                <div className="space-y-2">
                  <Label className="text-sm font-medium">Delivery Time</Label>
                  <Input
                    type="time"
                    value={data.alert_time}
                    onChange={(e) => updateData({ alert_time: e.target.value })}
                    className="max-w-[200px]"
                  />
                  <p className="text-xs text-muted-foreground">
                    Your daily top picks arrive at this time. Pacific Time.
                  </p>
                </div>

                {/* Score Threshold */}
                <div className="space-y-3">
                  <Label className="text-sm font-medium">
                    Minimum Score for Alerts:{" "}
                    <span className={`font-bold ${getScoreThresholdColor(data.alert_score_threshold)}`}>
                      {data.alert_score_threshold}
                    </span>
                  </Label>
                  <Slider
                    value={[data.alert_score_threshold]}
                    onValueChange={(v) =>
                      updateData({ alert_score_threshold: Array.isArray(v) ? v[0] : v })
                    }
                    min={0}
                    max={100}
                    step={5}
                    className="[&_[role=slider]]:bg-amber [&_[role=slider]]:border-amber"
                  />
                  <div className="flex justify-between text-xs text-muted-foreground">
                    <span>0 (all)</span>
                    <span>50</span>
                    <span>100</span>
                  </div>
                  <p className="text-xs text-muted-foreground">
                    Only properties scoring above this threshold will trigger alerts.
                  </p>
                </div>
              </div>
            )}

            {/* ── Step 4: Preview & Launch ───────────────────────────────── */}
            {step === 4 && (
              <div className="space-y-8">
                <div>
                  <h2 className="font-[family-name:var(--font-heading)] text-2xl sm:text-3xl font-bold">
                    Your scout is ready
                  </h2>
                  <p className="mt-2 text-muted-foreground">
                    Here&apos;s a preview of what we found for you.
                  </p>
                </div>

                {/* Summary card */}
                <div className="rounded-xl border border-border/60 bg-card p-6 space-y-3">
                  <h3 className="font-semibold text-sm text-muted-foreground uppercase tracking-wider">
                    Your Profile
                  </h3>
                  <div className="space-y-2 text-sm">
                    <div className="flex justify-between">
                      <span className="text-muted-foreground">Market</span>
                      <span className="font-medium">{market?.display_name || "Bay Area"}</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-muted-foreground">Budget</span>
                      <span className="font-medium">
                        Up to {formatPrice(data.max_price)} ({data.down_payment_pct}% down)
                      </span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-muted-foreground">Strategy</span>
                      <span className="font-medium">{strategyLabel}</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-muted-foreground">Cities</span>
                      <span className="font-medium text-right max-w-[200px] truncate">
                        {data.target_cities.length > 0
                          ? data.target_cities.join(", ")
                          : "All cities"}
                      </span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-muted-foreground">Must-haves</span>
                      <span className="font-medium">
                        {data.must_haves.length > 0
                          ? `${data.must_haves.length} selected`
                          : "None"}
                      </span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-muted-foreground">Alerts</span>
                      <span className="font-medium">
                        {[
                          data.alert_channels.sms && "SMS",
                          data.alert_channels.whatsapp && "WhatsApp",
                          data.alert_channels.email && "Email",
                        ]
                          .filter(Boolean)
                          .join(" + ") || "None"}{" "}
                        at {data.alert_time}
                      </span>
                    </div>
                  </div>
                  <div className="flex gap-2 pt-2">
                    <button
                      onClick={() => setStep(0)}
                      className="text-xs text-amber-dark dark:text-amber hover:underline"
                    >
                      Edit Budget
                    </button>
                    <span className="text-xs text-muted-foreground">·</span>
                    <button
                      onClick={() => setStep(1)}
                      className="text-xs text-amber-dark dark:text-amber hover:underline"
                    >
                      Edit Strategy
                    </button>
                    <span className="text-xs text-muted-foreground">·</span>
                    <button
                      onClick={() => setStep(3)}
                      className="text-xs text-amber-dark dark:text-amber hover:underline"
                    >
                      Edit Alerts
                    </button>
                  </div>
                </div>

                {/* Property preview */}
                {previewProps && previewProps.items.length > 0 && (
                  <div className="space-y-3">
                    <p className="text-sm text-muted-foreground">
                      We found{" "}
                      <span className="font-semibold text-foreground">
                        {previewProps.total} properties
                      </span>{" "}
                      scored for you. These are your top 3:
                    </p>
                    <div className="grid gap-3">
                      {previewProps.items.map((prop, i) => (
                        <motion.div
                          key={prop.id}
                          initial={{ opacity: 0, y: 12 }}
                          animate={{ opacity: 1, y: 0 }}
                          transition={{ delay: i * 0.15 }}
                          className="rounded-xl border border-border/60 bg-card p-4 flex items-center gap-4"
                        >
                          <ScoreRing score={prop.score ?? 0} size={52} strokeWidth={3} showLabel={false} />
                          <div className="flex-1 min-w-0">
                            <p className="font-semibold text-sm truncate">
                              {prop.address}
                            </p>
                            <p className="text-xs text-muted-foreground flex items-center gap-1">
                              <MapPin className="h-3 w-3" />
                              {prop.city}
                            </p>
                          </div>
                          <div className="text-right shrink-0">
                            <p className="font-bold">
                              {prop.price ? formatPrice(prop.price) : "N/A"}
                            </p>
                            <p className="text-xs text-muted-foreground">
                              {prop.beds}bd / {prop.baths}ba
                            </p>
                          </div>
                        </motion.div>
                      ))}
                    </div>
                  </div>
                )}
              </div>
            )}
          </motion.div>
        </AnimatePresence>

        {/* Navigation */}
        <div className="flex items-center justify-between mt-10 pt-6 border-t border-border/60">
          <Button
            variant="ghost"
            onClick={handleBack}
            disabled={step === 0 || saving || launching}
          >
            <ArrowLeft className="mr-2 h-4 w-4" />
            Back
          </Button>

          <div className="flex items-center gap-3">
            {/* Skip link on step 4 */}
            {step === 4 && (
              <button
                onClick={handleSkip}
                className="text-sm text-muted-foreground hover:text-foreground transition-colors"
                disabled={launching}
              >
                Skip for now →
              </button>
            )}

            {step < 4 ? (
              <Button
                onClick={handleNext}
                disabled={!canNext || saving}
                className="bg-amber text-amber-foreground hover:bg-amber-dark"
              >
                {saving ? (
                  <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                ) : null}
                Continue
                <ArrowRight className="ml-2 h-4 w-4" />
              </Button>
            ) : (
              <Button
                onClick={handleLaunch}
                disabled={saving || launching}
                className="bg-amber text-amber-foreground hover:bg-amber-dark px-8"
              >
                {launching ? (
                  <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                ) : null}
                Launch My Scout
                <Zap className="ml-2 h-4 w-4" />
              </Button>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}

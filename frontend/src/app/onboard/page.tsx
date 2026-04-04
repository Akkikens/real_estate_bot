"use client";

import { useState, useCallback } from "react";
import { useRouter } from "next/navigation";
import { motion, AnimatePresence } from "framer-motion";
import {
  ArrowRight,
  ArrowLeft,
  DollarSign,
  Target,
  ListChecks,
  Bell,
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
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { Slider } from "@/components/ui/slider";
import { Switch } from "@/components/ui/switch";
import { Label } from "@/components/ui/label";
import { Input } from "@/components/ui/input";
import { Navbar } from "@/components/navbar";
import Link from "next/link";
import { useAuthStore } from "@/lib/stores";
import { useMarket } from "@/lib/queries";

const steps = [
  { label: "Budget", icon: DollarSign },
  { label: "Strategy", icon: Target },
  { label: "Must-Haves", icon: ListChecks },
  { label: "Alerts", icon: Bell },
];

const strategies = [
  {
    id: "house_hack",
    label: "House-Hack",
    icon: Home,
    desc: "Live in one unit, rent the others. Offset your mortgage.",
    popular: true,
  },
  {
    id: "buy_hold",
    label: "Buy & Hold",
    icon: Repeat,
    desc: "Long-term rental income and appreciation play.",
  },
  {
    id: "primary",
    label: "Primary Residence",
    icon: Building,
    desc: "Finding the perfect home to live in.",
  },
  {
    id: "fix_flip",
    label: "Fix & Flip",
    icon: Wrench,
    desc: "Buy undervalued, renovate, sell for profit.",
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

function formatPrice(val: number) {
  if (val >= 1000000) return `$${(val / 1000000).toFixed(1)}M`;
  return `$${(val / 1000).toFixed(0)}k`;
}

export default function OnboardPage() {
  const router = useRouter();
  const { user, preferences, updatePreferences, isAuthenticated } = useAuthStore();

  const [step, setStep] = useState(0);
  const [budget, setBudget] = useState([preferences?.max_price || 850000]);
  const [downPayment, setDownPayment] = useState(
    String(preferences?.down_payment_pct || 20)
  );
  const [selectedCities, setSelectedCities] = useState<string[]>(
    preferences?.target_cities || []
  );
  const [strategy, setStrategy] = useState<string | null>(
    preferences?.strategy || null
  );
  const [selected, setSelected] = useState<string[]>(
    preferences?.must_haves || []
  );
  const [channels, setChannels] = useState(
    preferences?.alert_channels || { sms: true, whatsapp: false, email: true }
  );
  const [alertTime, setAlertTime] = useState(preferences?.alert_time || "08:00");
  const [saving, setSaving] = useState(false);

  // Load market cities
  const marketId = user?.market_id || "bay_area";
  const { data: market } = useMarket(marketId);
  const cities = market?.cities || [];

  const toggleCity = (city: string) =>
    setSelectedCities((prev) =>
      prev.includes(city) ? prev.filter((c) => c !== city) : [...prev, city]
    );

  const toggleMustHave = (id: string) =>
    setSelected((prev) =>
      prev.includes(id) ? prev.filter((x) => x !== id) : [...prev, id]
    );

  const canNext =
    step === 0
      ? selectedCities.length > 0
      : step === 1
      ? strategy !== null
      : step === 2
      ? true
      : true;

  // Save preferences at each step transition
  const saveCurrentStep = useCallback(async () => {
    if (!isAuthenticated) return;

    try {
      setSaving(true);
      const updates: Record<string, unknown> = {};

      if (step === 0) {
        updates.max_price = budget[0];
        updates.down_payment_pct = parseFloat(downPayment);
        updates.target_cities = selectedCities;
      } else if (step === 1) {
        updates.strategy = strategy;
      } else if (step === 2) {
        updates.must_haves = selected;
      } else if (step === 3) {
        updates.alert_channels = channels;
        updates.alert_time = alertTime;
      }

      await updatePreferences(updates);
    } catch (err) {
      console.error("Failed to save preferences:", err);
    } finally {
      setSaving(false);
    }
  }, [
    isAuthenticated, step, budget, downPayment, selectedCities,
    strategy, selected, channels, alertTime, updatePreferences,
  ]);

  const handleNext = async () => {
    await saveCurrentStep();
    if (step < 3) {
      setStep(step + 1);
    }
  };

  const handleLaunch = async () => {
    await saveCurrentStep();
    router.push("/dashboard");
  };

  return (
    <div className="min-h-screen">
      <Navbar />
      <div className="mx-auto max-w-2xl px-4 sm:px-6 py-10 sm:py-16">
        {/* Progress */}
        <div className="flex items-center justify-between mb-10">
          {steps.map((s, i) => (
            <div key={s.label} className="flex items-center gap-2 flex-1">
              <div
                className={`flex h-9 w-9 items-center justify-center rounded-full text-sm font-semibold transition-colors ${
                  i < step
                    ? "bg-amber text-amber-foreground"
                    : i === step
                    ? "bg-amber/20 text-amber-dark dark:text-amber border-2 border-amber"
                    : "bg-muted text-muted-foreground"
                }`}
              >
                {i < step ? <Check className="h-4 w-4" /> : i + 1}
              </div>
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
        {!isAuthenticated && (
          <div className="rounded-lg border border-amber/30 bg-amber/5 px-4 py-2.5 mb-6 text-sm text-muted-foreground">
            <Link href="/login" className="text-amber-dark dark:text-amber font-medium hover:underline">
              Sign in
            </Link>{" "}
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
            {step === 0 && (
              <div className="space-y-8">
                <div>
                  <h2 className="font-[family-name:var(--font-heading)] text-2xl sm:text-3xl font-bold">
                    What&apos;s your budget?
                  </h2>
                  <p className="mt-2 text-muted-foreground">
                    Set your max price and down payment. We&apos;ll only show
                    properties that fit.
                  </p>
                </div>

                <div className="space-y-4">
                  <div className="flex items-center justify-between">
                    <Label className="text-sm font-medium">Max Price</Label>
                    <span className="text-2xl font-bold text-amber-dark dark:text-amber">
                      {formatPrice(budget[0])}
                    </span>
                  </div>
                  <Slider
                    value={budget}
                    onValueChange={(v) =>
                      setBudget(Array.isArray(v) ? v : [v])
                    }
                    min={200000}
                    max={2000000}
                    step={25000}
                    className="[&_[role=slider]]:bg-amber [&_[role=slider]]:border-amber"
                  />
                  <div className="flex justify-between text-xs text-muted-foreground">
                    <span>$200k</span>
                    <span>$2M</span>
                  </div>
                </div>

                <div className="space-y-2">
                  <Label className="text-sm font-medium">Down Payment %</Label>
                  <div className="flex gap-2">
                    {["3.5", "5", "10", "15", "20", "25"].map((pct) => (
                      <button
                        key={pct}
                        onClick={() => setDownPayment(pct)}
                        className={`flex-1 rounded-lg border py-2 text-sm font-medium transition-colors ${
                          downPayment === pct
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
                  <Label className="text-sm font-medium">
                    Target Cities
                    {cities.length > 0 && (
                      <span className="text-muted-foreground font-normal ml-2">
                        ({selectedCities.length} selected)
                      </span>
                    )}
                  </Label>
                  <div className="flex flex-wrap gap-2">
                    {cities.map((city) => (
                      <button
                        key={city}
                        onClick={() => toggleCity(city)}
                        className={`rounded-full border px-3 py-1.5 text-sm transition-colors ${
                          selectedCities.includes(city)
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
                      onClick={() => setStrategy(s.id)}
                      className={`flex items-start gap-4 rounded-xl border p-5 text-left transition-all ${
                        strategy === s.id
                          ? "border-amber bg-amber/5 ring-1 ring-amber/30"
                          : "border-border hover:border-amber/20 hover:bg-muted/50"
                      }`}
                    >
                      <div
                        className={`flex h-10 w-10 items-center justify-center rounded-lg shrink-0 ${
                          strategy === s.id
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
                      {strategy === s.id && (
                        <div className="ml-auto mt-1">
                          <Check className="h-5 w-5 text-amber" />
                        </div>
                      )}
                    </button>
                  ))}
                </div>
              </div>
            )}

            {step === 2 && (
              <div className="space-y-8">
                <div>
                  <h2 className="font-[family-name:var(--font-heading)] text-2xl sm:text-3xl font-bold">
                    Must-haves
                  </h2>
                  <p className="mt-2 text-muted-foreground">
                    Select what matters most. We&apos;ll boost scores for
                    properties that match.
                  </p>
                </div>

                <div className="grid grid-cols-2 sm:grid-cols-3 gap-3">
                  {mustHaves.map((item) => (
                    <button
                      key={item.id}
                      onClick={() => toggleMustHave(item.id)}
                      className={`flex flex-col items-center gap-2 rounded-xl border p-4 transition-all ${
                        selected.includes(item.id)
                          ? "border-amber bg-amber/5 ring-1 ring-amber/30"
                          : "border-border hover:border-amber/20 hover:bg-muted/50"
                      }`}
                    >
                      <item.icon
                        className={`h-6 w-6 ${
                          selected.includes(item.id)
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
            )}

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
                  <div className="flex items-center justify-between rounded-xl border border-border p-4">
                    <div className="flex items-center gap-3">
                      <span className="text-lg">💬</span>
                      <div>
                        <p className="font-medium text-sm">SMS</p>
                        <p className="text-xs text-muted-foreground">
                          Text message alerts
                        </p>
                      </div>
                    </div>
                    <Switch
                      checked={channels.sms}
                      onCheckedChange={(v) =>
                        setChannels((c) => ({ ...c, sms: v }))
                      }
                    />
                  </div>
                  <div className="flex items-center justify-between rounded-xl border border-border p-4">
                    <div className="flex items-center gap-3">
                      <span className="text-lg">📱</span>
                      <div>
                        <p className="font-medium text-sm">WhatsApp</p>
                        <p className="text-xs text-muted-foreground">
                          Rich message with property cards
                        </p>
                      </div>
                    </div>
                    <Switch
                      checked={channels.whatsapp}
                      onCheckedChange={(v) =>
                        setChannels((c) => ({ ...c, whatsapp: v }))
                      }
                    />
                  </div>
                  <div className="flex items-center justify-between rounded-xl border border-border p-4">
                    <div className="flex items-center gap-3">
                      <span className="text-lg">📧</span>
                      <div>
                        <p className="font-medium text-sm">Email</p>
                        <p className="text-xs text-muted-foreground">
                          Daily digest with full details
                        </p>
                      </div>
                    </div>
                    <Switch
                      checked={channels.email}
                      onCheckedChange={(v) =>
                        setChannels((c) => ({ ...c, email: v }))
                      }
                    />
                  </div>
                </div>

                <div className="space-y-2">
                  <Label className="text-sm font-medium">Delivery Time</Label>
                  <Input
                    type="time"
                    value={alertTime}
                    onChange={(e) => setAlertTime(e.target.value)}
                    className="max-w-[200px]"
                  />
                  <p className="text-xs text-muted-foreground">
                    Your daily top picks arrive at this time.
                  </p>
                </div>
              </div>
            )}
          </motion.div>
        </AnimatePresence>

        {/* Navigation */}
        <div className="flex items-center justify-between mt-10 pt-6 border-t border-border/60">
          <Button
            variant="ghost"
            onClick={() => setStep(step - 1)}
            disabled={step === 0 || saving}
          >
            <ArrowLeft className="mr-2 h-4 w-4" />
            Back
          </Button>

          {step < 3 ? (
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
              disabled={saving}
              className="bg-amber text-amber-foreground hover:bg-amber-dark"
            >
              {saving ? (
                <Loader2 className="mr-2 h-4 w-4 animate-spin" />
              ) : null}
              Launch My Scout
              <Zap className="ml-2 h-4 w-4" />
            </Button>
          )}
        </div>
      </div>
    </div>
  );
}

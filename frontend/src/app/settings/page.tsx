"use client";

import { useState, useEffect, useCallback } from "react";
import {
  User,
  Bell,
  CreditCard,
  MapPin,
  Save,
  Check,
  Loader2,
  LogIn,
} from "lucide-react";
import { Navbar } from "@/components/navbar";
import { EmptyState } from "@/components/empty-state";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Switch } from "@/components/ui/switch";
import { Separator } from "@/components/ui/separator";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Badge } from "@/components/ui/badge";
import { useAuthStore } from "@/lib/stores";
import {
  useMarket,
  useUpdateProfile,
  useUpdatePreferences,
} from "@/lib/queries";

const TIER_LABELS: Record<string, { label: string; color: string }> = {
  free: { label: "Free", color: "bg-muted text-muted-foreground" },
  pro: { label: "Pro", color: "bg-amber text-amber-foreground" },
  investor: { label: "Investor", color: "bg-violet-600 text-white" },
};

export default function SettingsPage() {
  const {
    user,
    preferences,
    isAuthenticated,
    isLoading: authLoading,
    loadUser,
    setUser,
  } = useAuthStore();

  // ── Form state, seeded from auth store ──────────────────────────────────
  const [name, setName] = useState("");
  const [phone, setPhone] = useState("");
  const [targetCities, setTargetCities] = useState<string[]>([]);
  const [notifications, setNotifications] = useState({
    sms: true,
    whatsapp: false,
    email: true,
  });
  const [alertTime, setAlertTime] = useState("08:00");
  const [rentalTime, setRentalTime] = useState("18:00");
  const [scoreThreshold, setScoreThreshold] = useState(65);

  const [profileSaved, setProfileSaved] = useState(false);
  const [prefsSaved, setPrefsSaved] = useState(false);

  // Seed form from user/preferences once loaded
  useEffect(() => {
    if (user) {
      setName(user.name || "");
      setPhone(user.phone || "");
    }
  }, [user]);

  useEffect(() => {
    if (preferences) {
      setTargetCities(preferences.target_cities || []);
      setNotifications({
        sms: preferences.alert_channels?.sms ?? true,
        whatsapp: preferences.alert_channels?.whatsapp ?? false,
        email: preferences.alert_channels?.email ?? true,
      });
      setAlertTime(preferences.alert_time || "08:00");
      setRentalTime(preferences.rental_alert_time || "18:00");
      setScoreThreshold(preferences.alert_score_threshold ?? 65);
    }
  }, [preferences]);

  // Load market cities for the city picker
  const marketId = user?.market_id || "bay_area";
  const { data: market } = useMarket(marketId);
  const cities = market?.cities || [];

  // Mutations
  const updateProfile = useUpdateProfile();
  const updatePreferences = useUpdatePreferences();

  const toggleCity = (city: string) =>
    setTargetCities((prev) =>
      prev.includes(city) ? prev.filter((c) => c !== city) : [...prev, city]
    );

  // ── Save handlers ──────────────────────────────────────────────────────
  const handleSaveProfile = useCallback(async () => {
    try {
      const result = await updateProfile.mutateAsync({ name, phone });
      if (result.user) setUser(result.user);
      // Also save target cities (part of preferences)
      await updatePreferences.mutateAsync({ target_cities: targetCities });
      setProfileSaved(true);
      setTimeout(() => setProfileSaved(false), 2000);
    } catch (err) {
      console.error("Failed to save profile:", err);
    }
  }, [name, phone, targetCities, updateProfile, updatePreferences, setUser]);

  const handleSaveNotifications = useCallback(async () => {
    try {
      await updatePreferences.mutateAsync({
        alert_channels: notifications,
        alert_time: alertTime,
        rental_alert_time: rentalTime,
        alert_score_threshold: scoreThreshold,
      });
      setPrefsSaved(true);
      setTimeout(() => setPrefsSaved(false), 2000);
      // Refresh auth store preferences
      loadUser();
    } catch (err) {
      console.error("Failed to save notifications:", err);
    }
  }, [notifications, alertTime, rentalTime, scoreThreshold, updatePreferences, loadUser]);

  // ── Auth guard ─────────────────────────────────────────────────────────
  if (!authLoading && !isAuthenticated) {
    return (
      <div className="min-h-screen">
        <Navbar />
        <div className="mx-auto max-w-3xl px-4 sm:px-6 py-20">
          <EmptyState
            icon={LogIn}
            title="Sign in to access settings"
            description="Manage your profile, target cities, and notification preferences."
            actionLabel="Sign In"
            actionHref="/login"
          />
        </div>
      </div>
    );
  }

  const tier = TIER_LABELS[user?.subscription_tier || "free"];

  return (
    <div className="min-h-screen">
      <Navbar />
      <div className="mx-auto max-w-3xl px-4 sm:px-6 py-6 sm:py-10">
        <h1 className="font-[family-name:var(--font-heading)] text-2xl sm:text-3xl font-bold mb-8">
          Settings
        </h1>

        <Tabs defaultValue="profile" className="space-y-6">
          <TabsList className="grid w-full grid-cols-3">
            <TabsTrigger value="profile" className="gap-2">
              <User className="h-4 w-4" />
              <span className="hidden sm:inline">Profile</span>
            </TabsTrigger>
            <TabsTrigger value="notifications" className="gap-2">
              <Bell className="h-4 w-4" />
              <span className="hidden sm:inline">Notifications</span>
            </TabsTrigger>
            <TabsTrigger value="subscription" className="gap-2">
              <CreditCard className="h-4 w-4" />
              <span className="hidden sm:inline">Subscription</span>
            </TabsTrigger>
          </TabsList>

          {/* ── Profile Tab ─────────────────────────────────────────── */}
          <TabsContent value="profile" className="space-y-6">
            <div className="rounded-xl border border-border/60 bg-card p-6 space-y-5">
              <h2 className="font-semibold text-lg">Personal Info</h2>
              <div className="grid sm:grid-cols-2 gap-4">
                <div className="space-y-2">
                  <Label>Full Name</Label>
                  <Input
                    value={name}
                    onChange={(e) => setName(e.target.value)}
                    placeholder="Jane Smith"
                  />
                </div>
                <div className="space-y-2">
                  <Label>Email</Label>
                  <Input
                    type="email"
                    value={user?.email || ""}
                    disabled
                    className="opacity-60"
                  />
                  <p className="text-xs text-muted-foreground">
                    Email cannot be changed
                  </p>
                </div>
                <div className="space-y-2">
                  <Label>Phone</Label>
                  <Input
                    value={phone}
                    onChange={(e) => setPhone(e.target.value)}
                    placeholder="+1 (555) 123-4567"
                  />
                </div>
                <div className="space-y-2">
                  <Label>Market</Label>
                  <Input
                    value={market?.display_name || marketId}
                    disabled
                    className="opacity-60"
                  />
                  <p className="text-xs text-muted-foreground">
                    Contact support to change market
                  </p>
                </div>
              </div>
            </div>

            <div className="rounded-xl border border-border/60 bg-card p-6 space-y-4">
              <h2 className="font-semibold text-lg flex items-center gap-2">
                <MapPin className="h-5 w-5 text-amber" />
                Target Cities
                {targetCities.length > 0 && (
                  <span className="text-sm font-normal text-muted-foreground ml-1">
                    ({targetCities.length} selected)
                  </span>
                )}
              </h2>
              <div className="flex flex-wrap gap-2">
                {cities.map((city) => (
                  <button
                    key={city}
                    onClick={() => toggleCity(city)}
                    className={`rounded-full border px-3 py-1.5 text-sm transition-colors ${
                      targetCities.includes(city)
                        ? "border-amber bg-amber/10 text-amber-dark dark:text-amber"
                        : "border-border text-muted-foreground hover:bg-muted"
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

            <Button
              onClick={handleSaveProfile}
              disabled={updateProfile.isPending || updatePreferences.isPending}
              className="bg-amber text-amber-foreground hover:bg-amber-dark gap-2"
            >
              {updateProfile.isPending ? (
                <Loader2 className="h-4 w-4 animate-spin" />
              ) : profileSaved ? (
                <Check className="h-4 w-4" />
              ) : (
                <Save className="h-4 w-4" />
              )}
              {profileSaved ? "Saved!" : "Save Changes"}
            </Button>
          </TabsContent>

          {/* ── Notifications Tab ───────────────────────────────────── */}
          <TabsContent value="notifications" className="space-y-6">
            <div className="rounded-xl border border-border/60 bg-card p-6 space-y-5">
              <h2 className="font-semibold text-lg">Alert Channels</h2>

              <div className="space-y-4">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="font-medium text-sm">SMS Alerts</p>
                    <p className="text-xs text-muted-foreground">
                      Text messages to {phone || "your phone"}
                    </p>
                  </div>
                  <Switch
                    checked={notifications.sms}
                    onCheckedChange={(v) =>
                      setNotifications((n) => ({ ...n, sms: v }))
                    }
                  />
                </div>
                <Separator />
                <div className="flex items-center justify-between">
                  <div>
                    <p className="font-medium text-sm">WhatsApp</p>
                    <p className="text-xs text-muted-foreground">
                      Rich property cards via WhatsApp
                    </p>
                  </div>
                  <Switch
                    checked={notifications.whatsapp}
                    onCheckedChange={(v) =>
                      setNotifications((n) => ({ ...n, whatsapp: v }))
                    }
                  />
                </div>
                <Separator />
                <div className="flex items-center justify-between">
                  <div>
                    <p className="font-medium text-sm">Email Digest</p>
                    <p className="text-xs text-muted-foreground">
                      Daily summary to {user?.email || "your email"}
                    </p>
                  </div>
                  <Switch
                    checked={notifications.email}
                    onCheckedChange={(v) =>
                      setNotifications((n) => ({ ...n, email: v }))
                    }
                  />
                </div>
              </div>
            </div>

            <div className="rounded-xl border border-border/60 bg-card p-6 space-y-4">
              <h2 className="font-semibold text-lg">Delivery Schedule</h2>
              <div className="grid sm:grid-cols-2 gap-4">
                <div className="space-y-2">
                  <Label>For-Sale Alert Time</Label>
                  <Input
                    type="time"
                    value={alertTime}
                    onChange={(e) => setAlertTime(e.target.value)}
                  />
                  <p className="text-xs text-muted-foreground">
                    {market?.timezone || "Pacific Time"}
                  </p>
                </div>
                <div className="space-y-2">
                  <Label>Rental Digest Time</Label>
                  <Input
                    type="time"
                    value={rentalTime}
                    onChange={(e) => setRentalTime(e.target.value)}
                  />
                  <p className="text-xs text-muted-foreground">
                    {market?.timezone || "Pacific Time"}
                  </p>
                </div>
              </div>
            </div>

            <div className="rounded-xl border border-border/60 bg-card p-6 space-y-4">
              <h2 className="font-semibold text-lg">Score Threshold</h2>
              <div className="space-y-2">
                <Label>
                  Minimum score for alerts:{" "}
                  <span className="font-bold text-amber-dark dark:text-amber">
                    {scoreThreshold}
                  </span>
                </Label>
                <Input
                  type="range"
                  min={0}
                  max={100}
                  step={5}
                  value={scoreThreshold}
                  onChange={(e) => setScoreThreshold(parseInt(e.target.value))}
                  className="w-full accent-amber"
                />
                <div className="flex justify-between text-xs text-muted-foreground">
                  <span>0 (all)</span>
                  <span>50</span>
                  <span>100</span>
                </div>
                <p className="text-xs text-muted-foreground">
                  Only properties scoring above this threshold will trigger
                  alerts.
                </p>
              </div>
            </div>

            <Button
              onClick={handleSaveNotifications}
              disabled={updatePreferences.isPending}
              className="bg-amber text-amber-foreground hover:bg-amber-dark gap-2"
            >
              {updatePreferences.isPending ? (
                <Loader2 className="h-4 w-4 animate-spin" />
              ) : prefsSaved ? (
                <Check className="h-4 w-4" />
              ) : (
                <Save className="h-4 w-4" />
              )}
              {prefsSaved ? "Saved!" : "Save Preferences"}
            </Button>
          </TabsContent>

          {/* ── Subscription Tab ────────────────────────────────────── */}
          <TabsContent value="subscription" className="space-y-6">
            <div
              className={`rounded-xl border p-6 ${
                user?.subscription_tier === "pro"
                  ? "border-amber/30 bg-amber/5"
                  : user?.subscription_tier === "investor"
                  ? "border-violet-500/30 bg-violet-500/5"
                  : "border-border/60 bg-card"
              }`}
            >
              <div className="flex items-center justify-between">
                <div>
                  <Badge className={tier.color + " mb-2"}>
                    {tier.label} Plan
                  </Badge>
                  <h2 className="font-semibold text-lg">
                    {user?.subscription_tier === "free"
                      ? "$0/month"
                      : user?.subscription_tier === "pro"
                      ? "$19/month"
                      : "$49/month"}
                  </h2>
                  <p className="text-sm text-muted-foreground mt-1">
                    {user?.subscription_tier === "free"
                      ? "Basic alerts and scoring"
                      : user?.subscription_tier === "pro"
                      ? "Unlimited cities, SMS + WhatsApp, full scoring"
                      : "Portfolio-grade intelligence with API access"}
                  </p>
                  {user?.created_at && (
                    <p className="text-xs text-muted-foreground mt-2">
                      Member since{" "}
                      {new Date(user.created_at).toLocaleDateString()}
                    </p>
                  )}
                </div>
                <CreditCard className="h-8 w-8 text-amber" />
              </div>
            </div>

            <div className="rounded-xl border border-border/60 bg-card p-6 space-y-4">
              <h2 className="font-semibold text-lg">Plan Features</h2>
              <ul className="space-y-2 text-sm">
                {(user?.subscription_tier === "investor"
                  ? [
                      "Everything in Pro",
                      "API access",
                      "Bulk CSV export",
                      "Custom scoring weights",
                      "Priority data refresh",
                      "Dedicated support",
                    ]
                  : user?.subscription_tier === "pro"
                  ? [
                      "Unlimited target cities",
                      "SMS + WhatsApp alerts",
                      "Full 8-dimension scoring",
                      "Unlimited watchlist",
                      "Price drop tracking",
                      "Rental income estimates",
                    ]
                  : [
                      "3 target cities",
                      "Daily email digest",
                      "Basic scoring (5 dimensions)",
                      "10 watchlist slots",
                    ]
                ).map((f) => (
                  <li key={f} className="flex items-center gap-2">
                    <Check className="h-4 w-4 text-amber shrink-0" />
                    {f}
                  </li>
                ))}
              </ul>
            </div>

            {user?.subscription_tier === "free" && (
              <div className="rounded-xl border border-amber/20 bg-amber/5 p-6">
                <h3 className="font-semibold text-lg mb-2">
                  Upgrade to Pro
                </h3>
                <p className="text-sm text-muted-foreground mb-4">
                  Get unlimited cities, SMS + WhatsApp alerts, and full
                  8-dimension scoring for $19/month.
                </p>
                <Button className="bg-amber text-amber-foreground hover:bg-amber-dark">
                  Upgrade to Pro — $19/mo
                </Button>
              </div>
            )}

            {user?.subscription_tier !== "free" && (
              <div className="flex gap-3">
                <Button variant="outline">Manage Billing</Button>
                <Button
                  variant="outline"
                  className="text-muted-foreground"
                >
                  Cancel Subscription
                </Button>
              </div>
            )}
          </TabsContent>
        </Tabs>
      </div>
    </div>
  );
}

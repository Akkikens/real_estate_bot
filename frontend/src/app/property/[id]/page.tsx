"use client";

import { useParams } from "next/navigation";
import { motion } from "framer-motion";
import {
  ArrowLeft,
  MapPin,
  Bed,
  Bath,
  Maximize,
  Train,
  Bookmark,
  ExternalLink,
  Phone,
  Calendar,
  Home,
  DollarSign,
  TrendingDown,
  TrendingUp,
  Mail,
} from "lucide-react";
import Link from "next/link";
import { Navbar } from "@/components/navbar";
import { ScoreRing } from "@/components/score-ring";
import { ScoreBars } from "@/components/score-bars";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Separator } from "@/components/ui/separator";
import { EmptyState } from "@/components/empty-state";
import {
  useProperty,
  useUnderwriting,
  useAddToWatchlist,
  useRemoveFromWatchlist,
  useWatchlist,
} from "@/lib/queries";
import { useAuth } from "@clerk/nextjs";
import { useMemo, useState } from "react";

function formatPrice(p: number) {
  if (p >= 1000000) return `$${(p / 1000000).toFixed(2)}M`;
  return `$${(p / 1000).toFixed(0)}k`;
}

function formatCurrency(val: number) {
  return `$${Math.abs(val).toLocaleString("en-US", { maximumFractionDigits: 0 })}`;
}

export default function PropertyDetailPage() {
  const params = useParams();
  const id = params.id as string;

  const { data: prop, isLoading, isError } = useProperty(id);
  const { data: uw } = useUnderwriting(id);
  const { isSignedIn } = useAuth();

  const { data: watchlist } = useWatchlist();
  const addToWatchlist = useAddToWatchlist();
  const removeFromWatchlist = useRemoveFromWatchlist();

  const isWatched = useMemo(
    () => watchlist?.some((w) => w.property_id === id) ?? false,
    [watchlist, id]
  );

  const [showUnderwriting, setShowUnderwriting] = useState(false);

  const toggleSave = () => {
    if (!isSignedIn) {
      return;
    }
    if (isWatched) {
      removeFromWatchlist.mutate(id);
    } else {
      addToWatchlist.mutate(id);
    }
  };

  // Score breakdown → dimensions array for ScoreBars
  const dimensions = useMemo(() => {
    if (!prop?.score_breakdown) return [];
    return Object.entries(prop.score_breakdown).map(([label, data]) => ({
      label,
      score: data.score,
      note: data.note,
    }));
  }, [prop?.score_breakdown]);

  // ── Loading ────────────────────────────────────────────────────────────────
  if (isLoading) {
    return (
      <div className="min-h-screen">
        <Navbar />
        <div className="mx-auto max-w-5xl px-4 sm:px-6 py-6 sm:py-10">
          <div className="animate-pulse space-y-6">
            <div className="h-5 w-32 rounded bg-muted" />
            <div className="h-10 w-2/3 rounded bg-muted" />
            <div className="grid grid-cols-4 gap-3">
              {Array.from({ length: 4 }).map((_, i) => (
                <div key={i} className="h-24 rounded-xl bg-muted" />
              ))}
            </div>
            <div className="h-64 rounded-xl bg-muted" />
          </div>
        </div>
      </div>
    );
  }

  if (isError || !prop) {
    return (
      <div className="min-h-screen">
        <Navbar />
        <div className="mx-auto max-w-5xl px-4 sm:px-6 py-20">
          <EmptyState
            title="Property not found"
            description="This property may have been removed or the link is incorrect."
            actionLabel="Back to Dashboard"
            actionHref="/dashboard"
          />
        </div>
      </div>
    );
  }

  const pricePerSqft =
    prop.list_price && prop.sqft ? Math.round(prop.list_price / prop.sqft) : null;

  return (
    <div className="min-h-screen">
      <Navbar />
      <div className="mx-auto max-w-5xl px-4 sm:px-6 py-6 sm:py-10">
        {/* Back */}
        <Link
          href="/dashboard"
          className="inline-flex items-center gap-1.5 text-sm text-muted-foreground hover:text-foreground mb-6"
        >
          <ArrowLeft className="h-4 w-4" />
          Back to feed
        </Link>

        {/* Header */}
        <div className="flex flex-col sm:flex-row sm:items-start justify-between gap-4 mb-8">
          <div>
            <h1 className="font-[family-name:var(--font-heading)] text-2xl sm:text-3xl font-bold">
              {prop.address}
            </h1>
            <p className="text-muted-foreground flex items-center gap-1.5 mt-1">
              <MapPin className="h-4 w-4" />
              {prop.city || ''}{prop.city && prop.state ? ', ' : ''}{prop.state || ''} {prop.zip_code || ''}
            </p>
            <div className="flex flex-wrap gap-1.5 mt-3">
              {prop.tags.map((tag) => (
                <Badge
                  key={tag}
                  variant="secondary"
                  className="bg-amber/10 text-amber-dark dark:text-amber border-0"
                >
                  {tag}
                </Badge>
              ))}
            </div>
          </div>
          <ScoreRing score={prop.total_score ?? 0} size={90} strokeWidth={5} />
        </div>

        <div className="grid lg:grid-cols-3 gap-8">
          {/* Main content */}
          <div className="lg:col-span-2 space-y-8">
            {/* Key stats */}
            <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
              {[
                {
                  label: "Price",
                  value: prop.list_price ? formatPrice(prop.list_price) : "N/A",
                  icon: DollarSign,
                },
                {
                  label: "Beds / Baths",
                  value: `${prop.beds ?? "—"}bd / ${prop.baths ?? "—"}ba`,
                  icon: Bed,
                },
                {
                  label: "Sqft",
                  value: prop.sqft ? prop.sqft.toLocaleString() : "N/A",
                  icon: Maximize,
                },
                {
                  label: "Transit",
                  value: prop.bart_distance_miles
                    ? `${prop.bart_distance_miles.toFixed(1)} mi`
                    : "N/A",
                  icon: Train,
                },
              ].map((stat) => (
                <div
                  key={stat.label}
                  className="rounded-xl border border-border/60 bg-card p-4"
                >
                  <stat.icon className="h-4 w-4 text-muted-foreground mb-2" />
                  <p className="text-xs text-muted-foreground">{stat.label}</p>
                  <p className="font-semibold mt-0.5">{stat.value}</p>
                </div>
              ))}
            </div>

            {/* Extra details */}
            <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 text-sm">
              <div className="rounded-lg bg-muted/50 p-3">
                <p className="text-muted-foreground text-xs">Lot Size</p>
                <p className="font-medium">{prop.lot_size || "N/A"}</p>
              </div>
              <div className="rounded-lg bg-muted/50 p-3">
                <p className="text-muted-foreground text-xs">Year Built</p>
                <p className="font-medium">{prop.year_built || "N/A"}</p>
              </div>
              <div className="rounded-lg bg-muted/50 p-3">
                <p className="text-muted-foreground text-xs">$/Sqft</p>
                <p className="font-medium">
                  {pricePerSqft ? `$${pricePerSqft}` : "N/A"}
                </p>
              </div>
              <div className="rounded-lg bg-muted/50 p-3">
                <p className="text-muted-foreground text-xs">Days on Market</p>
                <p className="font-medium">
                  {prop.days_on_market ?? "N/A"}
                </p>
              </div>
            </div>

            {/* Score explanation */}
            {prop.score_explanation && (
              <div className="rounded-xl border border-border/60 bg-card p-5">
                <h2 className="font-semibold text-lg mb-2">Why This Score</h2>
                <p className="text-sm text-muted-foreground leading-relaxed">
                  {prop.score_explanation}
                </p>
              </div>
            )}

            {/* Listing Remarks */}
            {prop.listing_remarks && (
              <div>
                <h2 className="font-semibold text-lg mb-3">Listing Remarks</h2>
                <p className="text-sm text-muted-foreground leading-relaxed whitespace-pre-wrap">
                  {prop.listing_remarks}
                </p>
              </div>
            )}

            {/* ── Underwriting Section ─────────────────────────────────────── */}
            {uw && (
              <motion.div
                className="rounded-xl border border-border/60 bg-card p-5"
                initial={{ opacity: 0, y: 16 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: 0.3 }}
              >
                <div className="flex items-center justify-between mb-4">
                  <h2 className="font-semibold text-lg">
                    💰 Financial Underwriting
                  </h2>
                  <Button
                    variant="ghost"
                    size="sm"
                    onClick={() => setShowUnderwriting(!showUnderwriting)}
                  >
                    {showUnderwriting ? "Collapse" : "Expand"}
                  </Button>
                </div>

                {/* Always show summary */}
                <div className="grid grid-cols-2 sm:grid-cols-3 gap-3 text-sm">
                  <div>
                    <p className="text-xs text-muted-foreground">Monthly PITI</p>
                    <p className="font-bold text-lg">
                      {formatCurrency(uw.monthly_total_piti)}
                    </p>
                  </div>
                  <div>
                    <p className="text-xs text-muted-foreground">House-Hack Net</p>
                    <p
                      className={`font-bold text-lg ${
                        uw.house_hack_net >= 0
                          ? "text-green-600 dark:text-green-400"
                          : "text-red-500"
                      }`}
                    >
                      {uw.house_hack_net >= 0 ? "+" : ""}
                      {formatCurrency(uw.house_hack_net)}/mo
                    </p>
                  </div>
                  <div>
                    <p className="text-xs text-muted-foreground">Cash to Close</p>
                    <p className="font-bold text-lg">
                      {formatCurrency(uw.cash_to_close)}
                    </p>
                  </div>
                </div>

                {/* Verdict */}
                <div className="mt-4">
                  <Badge
                    className={
                      uw.good_first_property
                        ? "bg-green-500/10 text-green-700 dark:text-green-400 border-0"
                        : "bg-yellow-500/10 text-yellow-700 dark:text-yellow-400 border-0"
                    }
                  >
                    {uw.good_first_property
                      ? "✅ Good First Property"
                      : "⚠️ Review Carefully"}
                  </Badge>
                  <p className="text-xs text-muted-foreground mt-1">
                    {uw.verdict}
                  </p>
                </div>

                {/* Expanded details */}
                {showUnderwriting && (
                  <motion.div
                    initial={{ opacity: 0, height: 0 }}
                    animate={{ opacity: 1, height: "auto" }}
                    className="mt-4 pt-4 border-t border-border/60 space-y-4"
                  >
                    {/* Monthly breakdown */}
                    <div>
                      <h3 className="text-sm font-semibold mb-2">
                        Monthly Breakdown
                      </h3>
                      <div className="space-y-1 text-sm">
                        {[
                          ["Principal & Interest", uw.monthly_pi],
                          ["Property Tax", uw.monthly_tax],
                          ["Insurance", uw.monthly_insurance],
                          ["PMI", uw.monthly_pmi],
                          ["HOA", uw.monthly_hoa],
                        ]
                          .filter(([, val]) => (val as number) > 0)
                          .map(([label, val]) => (
                            <div
                              key={label as string}
                              className="flex justify-between"
                            >
                              <span className="text-muted-foreground">
                                {label as string}
                              </span>
                              <span className="font-medium">
                                {formatCurrency(val as number)}
                              </span>
                            </div>
                          ))}
                        <Separator className="my-2" />
                        <div className="flex justify-between font-semibold">
                          <span>Total PITI</span>
                          <span>{formatCurrency(uw.monthly_total_piti)}</span>
                        </div>
                      </div>
                    </div>

                    {/* Scenarios */}
                    <div>
                      <h3 className="text-sm font-semibold mb-2">Scenarios</h3>
                      <div className="space-y-2">
                        {[
                          {
                            label: "Owner-Occupant (no rental)",
                            value: uw.owner_occupant_burn,
                          },
                          {
                            label: "Room Rental — Low",
                            value: uw.room_rental_net_low,
                          },
                          {
                            label: "Room Rental — Mid",
                            value: uw.room_rental_net_mid,
                          },
                          {
                            label: "Room Rental — High",
                            value: uw.room_rental_net_high,
                          },
                          {
                            label: "House-Hack (all rooms rented)",
                            value: uw.house_hack_net,
                          },
                          {
                            label: "Full Rental",
                            value: uw.full_rental_net,
                          },
                        ].map((s) => (
                          <div key={s.label} className="flex justify-between text-sm">
                            <span className="text-muted-foreground">
                              {s.label}
                            </span>
                            <span
                              className={`font-medium ${
                                s.value >= 0
                                  ? "text-green-600 dark:text-green-400"
                                  : "text-red-500"
                              }`}
                            >
                              {s.value >= 0 ? "+" : ""}
                              {formatCurrency(s.value)}/mo
                            </span>
                          </div>
                        ))}
                      </div>
                    </div>

                    {/* 5-Year Appreciation */}
                    <div>
                      <h3 className="text-sm font-semibold mb-2">
                        5-Year Equity Gain
                      </h3>
                      <div className="space-y-1 text-sm">
                        {[
                          ["Conservative (2%)", uw.appreciation_conservative],
                          ["Moderate (4%)", uw.appreciation_moderate],
                          ["Optimistic (6%)", uw.appreciation_optimistic],
                        ].map(([label, val]) => (
                          <div
                            key={label as string}
                            className="flex justify-between"
                          >
                            <span className="text-muted-foreground">
                              {label as string}
                            </span>
                            <span className="font-medium text-green-600 dark:text-green-400">
                              +{formatCurrency(val as number)}
                            </span>
                          </div>
                        ))}
                      </div>
                    </div>

                    {/* Checks */}
                    {uw.checks.length > 0 && (
                      <div>
                        <h3 className="text-sm font-semibold mb-2">
                          Key Considerations
                        </h3>
                        <ul className="space-y-1">
                          {uw.checks.map((check, i) => (
                            <li
                              key={i}
                              className="text-sm text-muted-foreground flex gap-2"
                            >
                              <span>•</span>
                              <span>{check}</span>
                            </li>
                          ))}
                        </ul>
                      </div>
                    )}
                  </motion.div>
                )}
              </motion.div>
            )}

            {/* Map placeholder */}
            <div className="rounded-xl border border-border/60 bg-muted/30 h-64 flex items-center justify-center">
              <div className="text-center text-muted-foreground">
                <MapPin className="h-8 w-8 mx-auto mb-2 opacity-40" />
                <p className="text-sm">Map view</p>
                {prop.latitude && prop.longitude && (
                  <p className="text-xs mt-1">
                    {prop.latitude.toFixed(4)}, {prop.longitude.toFixed(4)}
                  </p>
                )}
              </div>
            </div>
          </div>

          {/* Sidebar */}
          <div className="space-y-6">
            {/* Score breakdown */}
            {dimensions.length > 0 && (
              <motion.div
                className="rounded-xl border border-border/60 bg-card p-5"
                initial={{ opacity: 0, y: 16 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: 0.2 }}
              >
                <h3 className="font-semibold mb-4">Score Breakdown</h3>
                <ScoreBars dimensions={dimensions} />
              </motion.div>
            )}

            {/* Transit info */}
            {prop.bart_distance_miles != null && (
              <div className="rounded-xl border border-border/60 bg-card p-5">
                <div className="flex items-center gap-2 mb-2">
                  <Train className="h-4 w-4 text-amber" />
                  <h3 className="font-semibold text-sm">Nearest Transit</h3>
                </div>
                <p className="text-sm">
                  {prop.bart_distance_miles.toFixed(1)} miles away
                </p>
                {prop.walk_score != null && (
                  <p className="text-xs text-muted-foreground mt-1">
                    Walk Score: {prop.walk_score}
                    {prop.transit_score != null && (
                      <> · Transit Score: {prop.transit_score}</>
                    )}
                  </p>
                )}
              </div>
            )}

            {/* Agent info */}
            {prop.agent_name && (
              <div className="rounded-xl border border-border/60 bg-card p-5">
                <h3 className="font-semibold text-sm mb-2">Listing Agent</h3>
                <p className="text-sm">{prop.agent_name}</p>
                {prop.brokerage && (
                  <p className="text-xs text-muted-foreground">
                    {prop.brokerage}
                  </p>
                )}
                {prop.agent_phone && (
                  <p className="text-xs text-muted-foreground mt-1">
                    <Phone className="h-3 w-3 inline mr-1" />
                    {prop.agent_phone}
                  </p>
                )}
                {prop.agent_email && (
                  <p className="text-xs text-muted-foreground mt-0.5">
                    <Mail className="h-3 w-3 inline mr-1" />
                    {prop.agent_email}
                  </p>
                )}
              </div>
            )}

            {/* Actions */}
            <div className="space-y-2">
              <Button
                className={`w-full gap-2 ${
                  isWatched
                    ? "bg-amber/20 text-amber-dark dark:text-amber border border-amber/30"
                    : "bg-amber text-amber-foreground hover:bg-amber-dark"
                }`}
                onClick={toggleSave}
                disabled={
                  addToWatchlist.isPending || removeFromWatchlist.isPending
                }
              >
                <Bookmark
                  className={`h-4 w-4 ${isWatched ? "fill-amber" : ""}`}
                />
                {isWatched ? "Saved to Watchlist" : "Save to Watchlist"}
              </Button>
              {prop.listing_url && (
                <a
                  href={prop.listing_url}
                  target="_blank"
                  rel="noopener noreferrer"
                >
                  <Button variant="outline" className="w-full gap-2">
                    <ExternalLink className="h-4 w-4" />
                    View on {prop.source || "Listing Site"}
                  </Button>
                </a>
              )}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

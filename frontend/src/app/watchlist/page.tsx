"use client";

import { useMemo } from "react";
import { motion, AnimatePresence } from "framer-motion";
import {
  Bookmark,
  TrendingDown,
  TrendingUp,
  Minus,
  Trash2,
  ExternalLink,
  MapPin,
  Bed,
  Bath,
  Train,
} from "lucide-react";
import { Navbar } from "@/components/navbar";
import { ScoreRing } from "@/components/score-ring";
import { SkeletonCard } from "@/components/skeleton-card";
import { EmptyState } from "@/components/empty-state";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import Link from "next/link";
import {
  useWatchlist,
  useRemoveFromWatchlist,
} from "@/lib/queries";
import { useAuth, SignInButton } from "@clerk/nextjs";
import { useTier } from "@/hooks/use-tier";
import { UpgradePrompt } from "@/components/upgrade-prompt";

function formatPrice(p: number) {
  if (p >= 1000000) return `$${(p / 1000000).toFixed(2)}M`;
  return `$${(p / 1000).toFixed(0)}k`;
}

function PriceChange({
  change,
  changePct,
}: {
  change: number | null;
  changePct: number | null;
}) {
  if (change == null || change === 0) {
    return (
      <span className="flex items-center gap-1 text-xs text-muted-foreground">
        <Minus className="h-3 w-3" /> No change
      </span>
    );
  }
  if (change < 0) {
    return (
      <span className="flex items-center gap-1 text-xs text-green-600 dark:text-green-400">
        <TrendingDown className="h-3 w-3" />
        {formatPrice(Math.abs(change))} ({changePct?.toFixed(1)}%)
      </span>
    );
  }
  return (
    <span className="flex items-center gap-1 text-xs text-red-500">
      <TrendingUp className="h-3 w-3" />+{formatPrice(change)} (+
      {changePct?.toFixed(1)}%)
    </span>
  );
}

export default function WatchlistPage() {
  const { isLoaded, isSignedIn } = useAuth();
  const { data: items, isLoading, isError, error } = useWatchlist();
  const removeFromWatchlist = useRemoveFromWatchlist();
  const { isFree, watchlistLimit } = useTier();
  const isAtLimit = isFree && (items?.length ?? 0) >= watchlistLimit;

  // ── Auth check ─────────────────────────────────────────────────────────────
  if (isLoaded && !isSignedIn) {
    return (
      <div className="min-h-screen">
        <Navbar />
        <div className="mx-auto max-w-4xl px-4 sm:px-6 py-20">
          <EmptyState
            title="Sign in to see your watchlist"
            description="Save properties from the dashboard to track price changes and manage your deal pipeline."
          >
            <SignInButton mode="modal">
              <Button className="bg-amber text-amber-foreground hover:bg-amber-dark">
                Sign In
              </Button>
            </SignInButton>
          </EmptyState>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen">
      <Navbar />
      <div className="mx-auto max-w-4xl px-4 sm:px-6 py-6 sm:py-10">
        <div className="flex items-center justify-between mb-8">
          <div>
            <h1 className="font-[family-name:var(--font-heading)] text-2xl sm:text-3xl font-bold">
              Watchlist
            </h1>
            <p className="text-sm text-muted-foreground mt-1">
              {items
                ? `${items.length} saved properties — tracking price changes daily`
                : "Loading..."}
            </p>
          </div>
          <Bookmark className="h-6 w-6 text-amber fill-amber/20" />
        </div>

        {/* Loading */}
        {isLoading && (
          <div className="space-y-3">
            {Array.from({ length: 3 }).map((_, i) => (
              <div
                key={i}
                className="rounded-xl border border-border/60 bg-card p-5 animate-pulse"
              >
                <div className="flex items-start gap-4">
                  <div className="h-14 w-14 rounded-full bg-muted shrink-0" />
                  <div className="flex-1 space-y-2">
                    <div className="h-5 w-2/3 rounded bg-muted" />
                    <div className="h-4 w-1/4 rounded bg-muted" />
                    <div className="h-4 w-1/2 rounded bg-muted" />
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}

        {/* Error */}
        {isError && (
          <EmptyState
            title="Failed to load watchlist"
            description={
              error instanceof Error ? error.message : "Please try again."
            }
          />
        )}

        {/* Empty */}
        {items && items.length === 0 && (
          <EmptyState
            icon={Bookmark}
            title="No saved properties yet"
            description="Browse the feed and save properties you're interested in to track them here."
            actionLabel="Browse properties"
            actionHref="/dashboard"
          />
        )}

        {/* List */}
        {items && items.length > 0 && (
          <div className="space-y-3">
            <AnimatePresence mode="popLayout">
              {items.map((item, i) => (
                <motion.div
                  key={item.property_id}
                  layout
                  initial={{ opacity: 0, y: 12 }}
                  animate={{ opacity: 1, y: 0 }}
                  exit={{ opacity: 0, x: -50 }}
                  transition={{ delay: i * 0.05 }}
                  className="rounded-xl border border-border/60 bg-card p-5 hover:border-amber/20 transition-colors"
                >
                  <div className="flex items-start gap-4">
                    <ScoreRing
                      score={item.score ?? 0}
                      size={56}
                      strokeWidth={3}
                      showLabel={false}
                      className="shrink-0 mt-1"
                    />
                    <div className="flex-1 min-w-0">
                      <div className="flex items-start justify-between gap-2">
                        <div>
                          <Link
                            href={`/property/${item.property_id}`}
                            className="font-semibold hover:underline"
                          >
                            {item.address || "Unknown address"}
                          </Link>
                          <p className="text-sm text-muted-foreground flex items-center gap-1">
                            <MapPin className="h-3 w-3" />
                            {item.city || "Unknown"}
                          </p>
                        </div>
                        <div className="text-right shrink-0">
                          <p className="font-bold text-lg">
                            {item.price
                              ? formatPrice(item.price)
                              : "N/A"}
                          </p>
                          <PriceChange
                            change={item.price_change}
                            changePct={item.price_change_pct}
                          />
                        </div>
                      </div>

                      <div className="flex items-center gap-4 mt-2 text-xs text-muted-foreground">
                        {item.beds != null && (
                          <span className="flex items-center gap-1">
                            <Bed className="h-3 w-3" />
                            {item.beds} bd
                          </span>
                        )}
                        {item.baths != null && (
                          <span className="flex items-center gap-1">
                            <Bath className="h-3 w-3" />
                            {item.baths} ba
                          </span>
                        )}
                        {item.bart_distance != null && (
                          <span className="flex items-center gap-1">
                            <Train className="h-3 w-3" />
                            {item.bart_distance.toFixed(1)} mi
                          </span>
                        )}
                        {item.saved_at && (
                          <span>
                            Saved{" "}
                            {new Date(item.saved_at).toLocaleDateString()}
                          </span>
                        )}
                      </div>

                      {/* Notes */}
                      {item.notes && (
                        <p className="text-xs text-muted-foreground mt-2 italic">
                          📝 {item.notes}
                        </p>
                      )}

                      <div className="flex items-center justify-between mt-3">
                        <div className="flex gap-1">
                          {item.tags?.map((tag) => (
                            <Badge
                              key={tag}
                              variant="secondary"
                              className="bg-amber/10 text-amber-dark dark:text-amber border-0 text-[10px]"
                            >
                              {tag}
                            </Badge>
                          ))}
                          {/* Pipeline stage badge */}
                          {item.pipeline_stage &&
                            item.pipeline_stage !== "watching" && (
                              <Badge
                                variant="secondary"
                                className="text-[10px]"
                              >
                                {item.pipeline_stage.replace("_", " ")}
                              </Badge>
                            )}
                        </div>
                        <div className="flex gap-1">
                          <Link href={`/property/${item.property_id}`}>
                            <Button variant="ghost" size="icon-sm">
                              <ExternalLink className="h-3.5 w-3.5" />
                            </Button>
                          </Link>
                          <Button
                            variant="ghost"
                            size="icon-sm"
                            className="text-muted-foreground hover:text-red-500"
                            onClick={() =>
                              removeFromWatchlist.mutate(item.property_id)
                            }
                            disabled={removeFromWatchlist.isPending}
                          >
                            <Trash2 className="h-3.5 w-3.5" />
                          </Button>
                        </div>
                      </div>
                    </div>
                  </div>
                </motion.div>
              ))}
            </AnimatePresence>

            {/* Watchlist limit upgrade prompt */}
            {isAtLimit && (
              <UpgradePrompt
                title="Watchlist is full"
                description={`Free accounts can save up to ${watchlistLimit} properties. Upgrade to Pro for 100 watchlist slots.`}
                className="mt-4"
              />
            )}
          </div>
        )}
      </div>
    </div>
  );
}

"use client";

import { Suspense, useCallback, useMemo } from "react";
import { useSearchParams, useRouter, usePathname } from "next/navigation";
import { motion } from "framer-motion";
import {
  RefreshCw,
  ChevronLeft,
  ChevronRight,
  BarChart3,
  TrendingDown,
  Home,
  Star,
} from "lucide-react";
import { Navbar } from "@/components/navbar";
import { DashboardFilters } from "@/components/dashboard-filters";
import { PropertyCard } from "@/components/property-card";
import { SkeletonCard } from "@/components/skeleton-card";
import { EmptyState } from "@/components/empty-state";
import { Button } from "@/components/ui/button";
import {
  useProperties,
  useStats,
  useAddToWatchlist,
  useRemoveFromWatchlist,
  useWatchlist,
} from "@/lib/queries";
import { useAuth } from "@clerk/nextjs";
import { useUser } from "@clerk/nextjs";
import type { PropertyFilters } from "@/lib/types";

// ── Helpers ──────────────────────────────────────────────────────────────────

function useFilterParams() {
  const searchParams = useSearchParams();

  return useMemo(() => {
    const page = parseInt(searchParams.get("page") || "1", 10);
    const sort = (searchParams.get("sort") || "score") as PropertyFilters["sort"];
    const min_score = searchParams.get("min_score") || undefined;
    const max_price = searchParams.get("max_price") || undefined;
    const min_beds = searchParams.get("min_beds") || undefined;
    const city = searchParams.get("city") || undefined;
    const listing_type = searchParams.get("listing_type") || undefined;
    const adu_only = searchParams.get("adu_only") === "true";
    const q = searchParams.get("q") || undefined;
    const filter = searchParams.get("filter") || "all";

    return {
      page,
      page_size: 21,
      sort: sort || "score",
      min_score,
      max_price,
      min_beds,
      city,
      listing_type,
      adu_only: adu_only || undefined,
      q,
      filter,
    };
  }, [searchParams]);
}

export default function DashboardPage() {
  return (
    <Suspense
      fallback={
        <div className="min-h-screen">
          <Navbar />
          <div className="mx-auto max-w-7xl px-4 sm:px-6 py-6 sm:py-10">
            <div className="h-10 w-48 rounded bg-muted animate-pulse mb-6" />
            <div className="grid sm:grid-cols-2 lg:grid-cols-3 gap-4">
              {Array.from({ length: 6 }).map((_, i) => (
                <SkeletonCard key={i} />
              ))}
            </div>
          </div>
        </div>
      }
    >
      <DashboardContent />
    </Suspense>
  );
}

function DashboardContent() {
  const router = useRouter();
  const pathname = usePathname();
  const filterParams = useFilterParams();
  const { filter: quickFilter, ...rawFilters } = filterParams;

  // ── Resolve quick filters + URL params into API params ────────────────────
  const resolvedFilters: PropertyFilters = useMemo(() => {
    const f: PropertyFilters = {
      page: rawFilters.page,
      page_size: rawFilters.page_size,
      sort: rawFilters.sort as PropertyFilters["sort"],
      q: rawFilters.q,
      city: rawFilters.city,
      listing_type: rawFilters.listing_type as "sale" | "rental" | undefined,
      adu_only: rawFilters.adu_only,
    };

    // Apply typed number filters
    if (rawFilters.min_score) f.min_score = parseFloat(rawFilters.min_score);
    if (rawFilters.max_price) f.max_price = parseFloat(rawFilters.max_price);
    if (rawFilters.min_beds) f.min_beds = parseInt(rawFilters.min_beds, 10);

    // Quick filter overrides
    switch (quickFilter) {
      case "excellent":
        f.min_score = Math.max(f.min_score ?? 0, 80);
        break;
      case "good":
        f.min_score = Math.max(f.min_score ?? 0, 65);
        break;
      case "adu":
        f.adu_only = true;
        break;
    }
    return f;
  }, [rawFilters, quickFilter]);

  // ── Data queries ───────────────────────────────────────────────────────────
  const { data, isLoading, isError, error, refetch, isFetching } =
    useProperties(resolvedFilters);
  const { data: stats } = useStats();
  const { isSignedIn } = useAuth();
  const { user: clerkUser } = useUser();
  const onboardingComplete = clerkUser?.unsafeMetadata?.onboarding_complete === true;

  // Watchlist state (only fetched if authenticated)
  const { data: watchlist } = useWatchlist();
  const addToWatchlist = useAddToWatchlist();
  const removeFromWatchlist = useRemoveFromWatchlist();

  const watchedIds = useMemo(() => {
    if (!watchlist) return new Set<string>();
    return new Set(watchlist.map((w) => w.property_id));
  }, [watchlist]);

  // ── URL param updater ──────────────────────────────────────────────────────
  const setFilter = useCallback(
    (updates: Record<string, string | undefined>) => {
      const params = new URLSearchParams(window.location.search);
      for (const [key, value] of Object.entries(updates)) {
        if (value === undefined || value === "" || value === "all") {
          params.delete(key);
        } else {
          params.set(key, value);
        }
      }
      // Reset to page 1 when filters change (unless page is the change)
      if (!("page" in updates)) {
        params.delete("page");
      }
      const qs = params.toString();
      router.push(`${pathname}${qs ? `?${qs}` : ""}`, { scroll: false });
    },
    [router, pathname]
  );

  // ── Watchlist toggling ─────────────────────────────────────────────────────
  const toggleSave = useCallback(
    (propertyId: string) => {
      if (!isSignedIn) return;
      if (watchedIds.has(propertyId)) {
        removeFromWatchlist.mutate(propertyId);
      } else {
        addToWatchlist.mutate(propertyId);
      }
    },
    [isSignedIn, watchedIds, addToWatchlist, removeFromWatchlist]
  );

  // ── Pagination ─────────────────────────────────────────────────────────────
  const page = data?.page ?? 1;
  const totalPages = data?.total_pages ?? 1;

  return (
    <div className="min-h-screen">
      <Navbar />

      {/* Onboarding incomplete banner */}
      {isSignedIn && !onboardingComplete && (
        <motion.div
          initial={{ y: -40, opacity: 0 }}
          animate={{ y: 0, opacity: 1 }}
          className="bg-amber/10 border-b border-amber/20 px-4 py-2.5 text-sm text-center"
        >
          Your scout isn&apos;t fully configured yet.{" "}
          <a href="/onboard" className="font-semibold text-amber-dark dark:text-amber underline">
            Finish setup →
          </a>
        </motion.div>
      )}

      <div className="mx-auto max-w-7xl px-4 sm:px-6 py-6 sm:py-10">
        {/* Header */}
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 mb-6">
          <div>
            <h1 className="font-[family-name:var(--font-heading)] text-2xl sm:text-3xl font-bold">
              Your Feed
            </h1>
            <p className="text-sm text-muted-foreground mt-1">
              {data
                ? `${data.total} properties scored`
                : "Loading properties..."}
              {stats?.avg_score != null && (
                <span className="ml-2">
                  · Avg score: {stats.avg_score.toFixed(0)}
                </span>
              )}
            </p>
          </div>
          <div className="flex items-center gap-2 self-start">
            <Button
              variant="outline"
              size="sm"
              className="gap-2"
              onClick={() => refetch()}
              disabled={isFetching}
            >
              <RefreshCw
                className={`h-3.5 w-3.5 ${isFetching ? "animate-spin" : ""}`}
              />
              Refresh
            </Button>
          </div>
        </div>

        {/* Stats bar */}
        {stats && (
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 mb-6">
            {[
              {
                label: "Active",
                value: stats.total_active,
                icon: Home,
              },
              {
                label: "Excellent (80+)",
                value: stats.excellent_count,
                icon: Star,
              },
              {
                label: "Price Drops (7d)",
                value: stats.price_drops_7d,
                icon: TrendingDown,
              },
              {
                label: "ADU Candidates",
                value: stats.adu_candidates,
                icon: BarChart3,
              },
            ].map((s) => (
              <div
                key={s.label}
                className="rounded-xl border border-border/60 bg-card p-3"
              >
                <div className="flex items-center gap-2 text-xs text-muted-foreground mb-1">
                  <s.icon className="h-3.5 w-3.5" />
                  {s.label}
                </div>
                <p className="font-bold text-lg">{s.value}</p>
              </div>
            ))}
          </div>
        )}

        {/* Filters */}
        <div className="mb-6">
          <DashboardFilters
            filters={{
              q: filterParams.q,
              sort: filterParams.sort || "score",
              filter: quickFilter,
              listing_type: filterParams.listing_type,
              min_score: filterParams.min_score,
              max_price: filterParams.max_price,
              min_beds: filterParams.min_beds,
              city: filterParams.city,
            }}
            onFilterChange={setFilter}
            totalResults={data?.total}
          />
        </div>

        {/* ── Loading state ───────────────────────────────────────────────── */}
        {isLoading && (
          <div className="grid sm:grid-cols-2 lg:grid-cols-3 gap-4">
            {Array.from({ length: 6 }).map((_, i) => (
              <SkeletonCard key={i} />
            ))}
          </div>
        )}

        {/* ── Error state ─────────────────────────────────────────────────── */}
        {isError && (
          <EmptyState
            title="Failed to load properties"
            description={
              error instanceof Error
                ? error.message
                : "Something went wrong. Please try again."
            }
            actionLabel="Retry"
            onAction={() => refetch()}
          />
        )}

        {/* ── Empty state ─────────────────────────────────────────────────── */}
        {data && data.items.length === 0 && (
          <EmptyState
            title="No properties match your filters"
            description="Try expanding your search, lowering the score threshold, or checking a different city."
            actionLabel="Reset filters"
            onAction={() => router.push(pathname)}
          />
        )}

        {/* ── Property grid ───────────────────────────────────────────────── */}
        {data && data.items.length > 0 && (
          <>
            <div className="grid sm:grid-cols-2 lg:grid-cols-3 gap-4">
              {data.items.map((property, i) => (
                <motion.div
                  key={property.id}
                  initial={{ opacity: 0, y: 16 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ delay: i * 0.03, duration: 0.3 }}
                >
                  <PropertyCard
                    property={property}
                    saved={watchedIds.has(property.id)}
                    onSave={() => toggleSave(property.id)}
                    savePending={
                      addToWatchlist.isPending || removeFromWatchlist.isPending
                    }
                  />
                </motion.div>
              ))}
            </div>

            {/* ── Pagination ──────────────────────────────────────────────── */}
            {totalPages > 1 && (
              <div className="flex items-center justify-center gap-4 mt-8">
                <Button
                  variant="outline"
                  size="sm"
                  disabled={page <= 1}
                  onClick={() => setFilter({ page: String(page - 1) })}
                >
                  <ChevronLeft className="h-4 w-4 mr-1" />
                  Previous
                </Button>
                <span className="text-sm text-muted-foreground">
                  Page {page} of {totalPages}
                  <span className="hidden sm:inline">
                    {" "}
                    · {data.total} properties
                  </span>
                </span>
                <Button
                  variant="outline"
                  size="sm"
                  disabled={page >= totalPages}
                  onClick={() => setFilter({ page: String(page + 1) })}
                >
                  Next
                  <ChevronRight className="h-4 w-4 ml-1" />
                </Button>
              </div>
            )}
          </>
        )}
      </div>
    </div>
  );
}

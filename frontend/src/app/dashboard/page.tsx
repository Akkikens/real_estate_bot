"use client";

import { Suspense, useCallback, useMemo, useState } from "react";
import { useSearchParams, useRouter, usePathname } from "next/navigation";
import { motion } from "framer-motion";
import {
  Search,
  RefreshCw,
  ChevronLeft,
  ChevronRight,
  BarChart3,
  TrendingDown,
  Home,
  Star,
} from "lucide-react";
import { Navbar } from "@/components/navbar";
import { PropertyCard } from "@/components/property-card";
import { SkeletonCard } from "@/components/skeleton-card";
import { EmptyState } from "@/components/empty-state";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Badge } from "@/components/ui/badge";
import {
  useProperties,
  useStats,
  useAddToWatchlist,
  useRemoveFromWatchlist,
  useWatchlist,
} from "@/lib/queries";
import { useAuthStore } from "@/lib/stores";
import type { PropertyFilters } from "@/lib/types";

// ── Quick filter definitions ─────────────────────────────────────────────────

const QUICK_FILTERS = [
  { label: "All", key: "all" },
  { label: "Excellent (80+)", key: "excellent" },
  { label: "Good (65+)", key: "good" },
  { label: "House Hack", key: "house_hack" },
  { label: "Near BART", key: "near_bart" },
  { label: "ADU", key: "adu" },
  { label: "Large Lot", key: "large_lot" },
] as const;

const SORT_OPTIONS = [
  { label: "Top Score", value: "score" },
  { label: "Price ↑", value: "price" },
  { label: "Newest", value: "newest" },
  { label: "BART Distance", value: "bart" },
] as const;

// ── Helpers ──────────────────────────────────────────────────────────────────

function useFilterParams(): PropertyFilters & { quickFilter: string } {
  const searchParams = useSearchParams();

  return useMemo(() => {
    const page = parseInt(searchParams.get("page") || "1", 10);
    const sort = (searchParams.get("sort") || "score") as PropertyFilters["sort"];
    const min_score = searchParams.get("min_score")
      ? parseFloat(searchParams.get("min_score")!)
      : undefined;
    const max_price = searchParams.get("max_price")
      ? parseFloat(searchParams.get("max_price")!)
      : undefined;
    const min_beds = searchParams.get("min_beds")
      ? parseInt(searchParams.get("min_beds")!, 10)
      : undefined;
    const city = searchParams.get("city") || undefined;
    const listing_type = (searchParams.get("listing_type") || undefined) as
      | "sale"
      | "rental"
      | undefined;
    const adu_only = searchParams.get("adu_only") === "true";
    const q = searchParams.get("q") || undefined;
    const quickFilter = searchParams.get("filter") || "all";

    return {
      page,
      page_size: 21,
      sort,
      min_score,
      max_price,
      min_beds,
      city,
      listing_type,
      adu_only: adu_only || undefined,
      q,
      quickFilter,
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
  const { quickFilter, ...apiFilters } = filterParams;

  // ── Resolve quick filters into API params ──────────────────────────────────
  const resolvedFilters: PropertyFilters = useMemo(() => {
    const f = { ...apiFilters };
    switch (quickFilter) {
      case "excellent":
        f.min_score = 80;
        break;
      case "good":
        f.min_score = 65;
        break;
      case "adu":
        f.adu_only = true;
        break;
      // house_hack and near_bart use tag-based filtering on the API side
      // (not implemented as API params yet; they'll show via tag matching)
      default:
        break;
    }
    return f;
  }, [apiFilters, quickFilter]);

  // ── Data queries ───────────────────────────────────────────────────────────
  const { data, isLoading, isError, error, refetch, isFetching } =
    useProperties(resolvedFilters);
  const { data: stats } = useStats();
  const { isAuthenticated } = useAuthStore();

  // Watchlist state (only fetched if authenticated)
  const { data: watchlist } = useWatchlist();
  const addToWatchlist = useAddToWatchlist();
  const removeFromWatchlist = useRemoveFromWatchlist();

  const watchedIds = useMemo(() => {
    if (!watchlist) return new Set<string>();
    return new Set(watchlist.map((w) => w.property_id));
  }, [watchlist]);

  // ── Search state (local, debounced push to URL) ────────────────────────────
  const [searchInput, setSearchInput] = useState(filterParams.q || "");

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

  // Debounced search
  const handleSearchSubmit = useCallback(
    (e: React.FormEvent) => {
      e.preventDefault();
      setFilter({ q: searchInput || undefined });
    },
    [searchInput, setFilter]
  );

  const handleSearchKeyDown = useCallback(
    (e: React.KeyboardEvent) => {
      if (e.key === "Enter") {
        setFilter({ q: searchInput || undefined });
      }
    },
    [searchInput, setFilter]
  );

  // ── Watchlist toggling ─────────────────────────────────────────────────────
  const toggleSave = useCallback(
    (propertyId: string) => {
      if (!isAuthenticated) {
        router.push("/login");
        return;
      }
      if (watchedIds.has(propertyId)) {
        removeFromWatchlist.mutate(propertyId);
      } else {
        addToWatchlist.mutate(propertyId);
      }
    },
    [isAuthenticated, watchedIds, addToWatchlist, removeFromWatchlist, router]
  );

  // ── Pagination ─────────────────────────────────────────────────────────────
  const page = data?.page ?? 1;
  const totalPages = data?.total_pages ?? 1;

  return (
    <div className="min-h-screen">
      <Navbar />
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

        {/* Search & Sort */}
        <div className="space-y-3 mb-6">
          <div className="flex gap-2">
            <form onSubmit={handleSearchSubmit} className="relative flex-1">
              <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
              <Input
                placeholder="Search by address or city..."
                value={searchInput}
                onChange={(e) => setSearchInput(e.target.value)}
                onKeyDown={handleSearchKeyDown}
                className="pl-9"
              />
            </form>
            <select
              value={filterParams.sort || "score"}
              onChange={(e) => setFilter({ sort: e.target.value })}
              className="rounded-lg border border-border bg-background px-3 py-2 text-sm"
            >
              {SORT_OPTIONS.map((o) => (
                <option key={o.value} value={o.value}>
                  {o.label}
                </option>
              ))}
            </select>
          </div>

          {/* Quick filters */}
          <div className="flex flex-wrap gap-2">
            {QUICK_FILTERS.map((f) => (
              <button
                key={f.key}
                onClick={() => setFilter({ filter: f.key })}
                className={`rounded-full border px-3 py-1 text-xs font-medium transition-colors ${
                  quickFilter === f.key
                    ? "border-amber bg-amber/10 text-amber-dark dark:text-amber"
                    : "border-border text-muted-foreground hover:bg-muted"
                }`}
              >
                {f.label}
              </button>
            ))}
          </div>
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

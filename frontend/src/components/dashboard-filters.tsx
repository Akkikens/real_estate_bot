"use client";

import { useCallback, useMemo, useRef, useState, useEffect } from "react";
import { motion, AnimatePresence } from "framer-motion";
import {
  Search,
  SlidersHorizontal,
  X,
  ChevronDown,
  Home,
  Key,
  Bed,
  MapPin,
  ArrowUpDown,
  Sparkles,
  Check,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Badge } from "@/components/ui/badge";
import { Slider } from "@/components/ui/slider";
import { useMarket } from "@/lib/queries";

// ── Types ───────────────────────────────────────────────────────────────────

interface FilterState {
  q?: string;
  sort: string;
  filter: string;
  listing_type?: string;
  min_score?: string;
  max_price?: string;
  min_beds?: string;
  city?: string;
}

interface DashboardFiltersProps {
  filters: FilterState;
  onFilterChange: (updates: Record<string, string | undefined>) => void;
  totalResults?: number;
}

// ── Constants ───────────────────────────────────────────────────────────────

const LISTING_TYPES = [
  { value: "all", label: "All Listings", icon: Home },
  { value: "sale", label: "For Sale", icon: Home },
  { value: "rental", label: "For Rent", icon: Key },
] as const;

const SORT_OPTIONS = [
  { value: "score", label: "Top Score", short: "Score" },
  { value: "price", label: "Price: Low → High", short: "Price ↑" },
  { value: "newest", label: "Newest First", short: "Newest" },
  { value: "bart", label: "Nearest BART", short: "BART" },
] as const;

const QUICK_FILTERS = [
  { key: "all", label: "All" },
  { key: "excellent", label: "Excellent 80+" },
  { key: "good", label: "Good 65+" },
  { key: "house_hack", label: "House Hack" },
  { key: "near_bart", label: "Near BART" },
  { key: "adu", label: "ADU Ready" },
  { key: "large_lot", label: "Large Lot" },
] as const;

const BED_OPTIONS = [
  { value: "", label: "Any" },
  { value: "1", label: "1+" },
  { value: "2", label: "2+" },
  { value: "3", label: "3+" },
  { value: "4", label: "4+" },
  { value: "5", label: "5+" },
] as const;

const PRICE_PRESETS = [
  { value: "", label: "Any Price" },
  { value: "500000", label: "Under $500k" },
  { value: "750000", label: "Under $750k" },
  { value: "1000000", label: "Under $1M" },
  { value: "1500000", label: "Under $1.5M" },
  { value: "2000000", label: "Under $2M" },
] as const;

// ── Dropdown component ──────────────────────────────────────────────────────

function FilterDropdown({
  trigger,
  children,
  align = "left",
}: {
  trigger: React.ReactNode;
  children: React.ReactNode;
  align?: "left" | "right";
}) {
  const [open, setOpen] = useState(false);
  const ref = useRef<HTMLDivElement>(null);

  useEffect(() => {
    function handleClick(e: MouseEvent) {
      if (ref.current && !ref.current.contains(e.target as Node)) {
        setOpen(false);
      }
    }
    if (open) document.addEventListener("mousedown", handleClick);
    return () => document.removeEventListener("mousedown", handleClick);
  }, [open]);

  return (
    <div ref={ref} className="relative">
      <div onClick={() => setOpen(!open)}>{trigger}</div>
      <AnimatePresence>
        {open && (
          <motion.div
            initial={{ opacity: 0, y: 4, scale: 0.97 }}
            animate={{ opacity: 1, y: 0, scale: 1 }}
            exit={{ opacity: 0, y: 4, scale: 0.97 }}
            transition={{ duration: 0.15 }}
            className={`absolute z-50 mt-1.5 min-w-[200px] rounded-xl border border-border/80 bg-background/95 backdrop-blur-xl shadow-lg shadow-black/8 dark:shadow-black/25 ${
              align === "right" ? "right-0" : "left-0"
            }`}
            onClick={() => setOpen(false)}
          >
            {children}
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}

// ── Main Component ──────────────────────────────────────────────────────────

export function DashboardFilters({
  filters,
  onFilterChange,
  totalResults,
}: DashboardFiltersProps) {
  const [searchInput, setSearchInput] = useState(filters.q || "");
  const [showAdvanced, setShowAdvanced] = useState(false);
  const { data: market } = useMarket("bay_area");
  const cities = market?.cities || [];

  // Count active filters (excluding defaults)
  const activeFilterCount = useMemo(() => {
    let count = 0;
    if (filters.listing_type && filters.listing_type !== "all") count++;
    if (filters.max_price) count++;
    if (filters.min_beds) count++;
    if (filters.city) count++;
    if (filters.min_score) count++;
    if (filters.q) count++;
    return count;
  }, [filters]);

  const handleSearchSubmit = useCallback(
    (e: React.FormEvent) => {
      e.preventDefault();
      onFilterChange({ q: searchInput || undefined });
    },
    [searchInput, onFilterChange]
  );

  const clearAllFilters = useCallback(() => {
    setSearchInput("");
    onFilterChange({
      q: undefined,
      filter: "all",
      listing_type: undefined,
      max_price: undefined,
      min_beds: undefined,
      city: undefined,
      min_score: undefined,
      sort: "score",
    });
  }, [onFilterChange]);

  const currentSort = SORT_OPTIONS.find((o) => o.value === filters.sort) || SORT_OPTIONS[0];
  const currentListingType = LISTING_TYPES.find((t) => t.value === (filters.listing_type || "all")) || LISTING_TYPES[0];

  return (
    <div className="space-y-3">
      {/* ── Row 1: Search + Listing Type Toggle + Sort ───────────────── */}
      <div className="flex gap-2 items-stretch">
        {/* Search */}
        <form onSubmit={handleSearchSubmit} className="relative flex-1 min-w-0">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground pointer-events-none" />
          <Input
            placeholder="Search address, city, zip..."
            value={searchInput}
            onChange={(e) => setSearchInput(e.target.value)}
            onKeyDown={(e) => {
              if (e.key === "Enter") onFilterChange({ q: searchInput || undefined });
            }}
            className="pl-9 pr-8 h-9 bg-muted/40 border-border/60 focus:bg-background transition-colors"
          />
          {searchInput && (
            <button
              type="button"
              onClick={() => {
                setSearchInput("");
                onFilterChange({ q: undefined });
              }}
              className="absolute right-2.5 top-1/2 -translate-y-1/2 text-muted-foreground hover:text-foreground"
            >
              <X className="h-3.5 w-3.5" />
            </button>
          )}
        </form>

        {/* Listing type segmented control */}
        <div className="hidden sm:flex items-center rounded-lg border border-border/60 bg-muted/40 p-0.5">
          {LISTING_TYPES.map((type) => {
            const active = (filters.listing_type || "all") === type.value;
            return (
              <button
                key={type.value}
                onClick={() =>
                  onFilterChange({
                    listing_type: type.value === "all" ? undefined : type.value,
                  })
                }
                className={`relative flex items-center gap-1.5 rounded-md px-3 py-1.5 text-xs font-medium transition-all ${
                  active
                    ? "text-amber-dark dark:text-amber"
                    : "text-muted-foreground hover:text-foreground"
                }`}
              >
                {active && (
                  <motion.div
                    layoutId="listing-type-bg"
                    className="absolute inset-0 rounded-md bg-background border border-border/60 shadow-sm"
                    transition={{ type: "spring", bounce: 0.15, duration: 0.4 }}
                  />
                )}
                <span className="relative flex items-center gap-1.5">
                  <type.icon className="h-3.5 w-3.5" />
                  {type.label}
                </span>
              </button>
            );
          })}
        </div>

        {/* Mobile listing type dropdown */}
        <FilterDropdown
          align="right"
          trigger={
            <button className="sm:hidden flex items-center gap-1.5 rounded-lg border border-border/60 bg-muted/40 px-3 py-2 text-xs font-medium text-muted-foreground hover:text-foreground transition-colors">
              <currentListingType.icon className="h-3.5 w-3.5" />
              <ChevronDown className="h-3 w-3" />
            </button>
          }
        >
          <div className="p-1">
            {LISTING_TYPES.map((type) => (
              <button
                key={type.value}
                onClick={() =>
                  onFilterChange({
                    listing_type: type.value === "all" ? undefined : type.value,
                  })
                }
                className={`flex items-center gap-2.5 w-full rounded-lg px-3 py-2 text-sm transition-colors ${
                  (filters.listing_type || "all") === type.value
                    ? "bg-amber/10 text-amber-dark dark:text-amber"
                    : "text-muted-foreground hover:text-foreground hover:bg-muted"
                }`}
              >
                <type.icon className="h-4 w-4" />
                {type.label}
                {(filters.listing_type || "all") === type.value && (
                  <Check className="h-3.5 w-3.5 ml-auto" />
                )}
              </button>
            ))}
          </div>
        </FilterDropdown>

        {/* Sort dropdown */}
        <FilterDropdown
          align="right"
          trigger={
            <button className="flex items-center gap-1.5 rounded-lg border border-border/60 bg-muted/40 px-3 py-2 text-xs font-medium text-muted-foreground hover:text-foreground transition-colors whitespace-nowrap">
              <ArrowUpDown className="h-3.5 w-3.5" />
              <span className="hidden sm:inline">{currentSort.short}</span>
              <ChevronDown className="h-3 w-3" />
            </button>
          }
        >
          <div className="p-1">
            {SORT_OPTIONS.map((opt) => (
              <button
                key={opt.value}
                onClick={() => onFilterChange({ sort: opt.value })}
                className={`flex items-center gap-2.5 w-full rounded-lg px-3 py-2 text-sm transition-colors ${
                  filters.sort === opt.value
                    ? "bg-amber/10 text-amber-dark dark:text-amber"
                    : "text-muted-foreground hover:text-foreground hover:bg-muted"
                }`}
              >
                {opt.label}
                {filters.sort === opt.value && (
                  <Check className="h-3.5 w-3.5 ml-auto" />
                )}
              </button>
            ))}
          </div>
        </FilterDropdown>
      </div>

      {/* ── Row 2: Quick Filters + Advanced Toggle ──────────────────── */}
      <div className="flex items-center gap-2">
        {/* Quick filter pills */}
        <div className="flex-1 flex flex-wrap gap-1.5">
          {QUICK_FILTERS.map((f) => {
            const active = (filters.filter || "all") === f.key;
            return (
              <button
                key={f.key}
                onClick={() => onFilterChange({ filter: f.key })}
                className={`relative rounded-full px-3 py-1 text-xs font-medium transition-all ${
                  active
                    ? "text-amber-dark dark:text-amber"
                    : "text-muted-foreground hover:text-foreground"
                }`}
              >
                {active && (
                  <motion.div
                    layoutId="quick-filter-bg"
                    className="absolute inset-0 rounded-full bg-amber/12 border border-amber/25"
                    transition={{ type: "spring", bounce: 0.2, duration: 0.4 }}
                  />
                )}
                <span className="relative">
                  {f.key === "excellent" && <Sparkles className="inline h-3 w-3 mr-1 -mt-0.5" />}
                  {f.label}
                </span>
              </button>
            );
          })}
        </div>

        {/* Advanced filters toggle */}
        <button
          onClick={() => setShowAdvanced(!showAdvanced)}
          className={`flex items-center gap-1.5 rounded-lg px-2.5 py-1.5 text-xs font-medium transition-all shrink-0 ${
            showAdvanced || activeFilterCount > 0
              ? "bg-amber/10 text-amber-dark dark:text-amber border border-amber/25"
              : "text-muted-foreground hover:text-foreground border border-transparent hover:border-border/60"
          }`}
        >
          <SlidersHorizontal className="h-3.5 w-3.5" />
          <span className="hidden sm:inline">Filters</span>
          {activeFilterCount > 0 && (
            <span className="flex items-center justify-center h-4 min-w-4 px-1 rounded-full bg-amber text-amber-foreground text-[10px] font-bold">
              {activeFilterCount}
            </span>
          )}
        </button>
      </div>

      {/* ── Row 3: Advanced Filters Panel ───────────────────────────── */}
      <AnimatePresence>
        {showAdvanced && (
          <motion.div
            initial={{ height: 0, opacity: 0 }}
            animate={{ height: "auto", opacity: 1 }}
            exit={{ height: 0, opacity: 0 }}
            transition={{ duration: 0.2 }}
            className="overflow-hidden"
          >
            <div className="rounded-xl border border-border/60 bg-card/50 backdrop-blur-sm p-4 space-y-4">
              <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
                {/* Price */}
                <div className="space-y-2">
                  <label className="text-xs font-medium text-muted-foreground uppercase tracking-wider">
                    Max Price
                  </label>
                  <div className="flex flex-wrap gap-1.5">
                    {PRICE_PRESETS.map((p) => {
                      const active = (filters.max_price || "") === p.value;
                      return (
                        <button
                          key={p.value}
                          onClick={() =>
                            onFilterChange({ max_price: p.value || undefined })
                          }
                          className={`rounded-md px-2.5 py-1.5 text-xs font-medium transition-colors ${
                            active
                              ? "bg-amber/15 text-amber-dark dark:text-amber border border-amber/30"
                              : "bg-muted/60 text-muted-foreground hover:text-foreground hover:bg-muted border border-transparent"
                          }`}
                        >
                          {p.label}
                        </button>
                      );
                    })}
                  </div>
                </div>

                {/* Beds */}
                <div className="space-y-2">
                  <label className="text-xs font-medium text-muted-foreground uppercase tracking-wider">
                    Bedrooms
                  </label>
                  <div className="flex gap-1.5">
                    {BED_OPTIONS.map((b) => {
                      const active = (filters.min_beds || "") === b.value;
                      return (
                        <button
                          key={b.value}
                          onClick={() =>
                            onFilterChange({ min_beds: b.value || undefined })
                          }
                          className={`flex items-center justify-center rounded-md px-3 py-1.5 text-xs font-medium transition-colors ${
                            active
                              ? "bg-amber/15 text-amber-dark dark:text-amber border border-amber/30"
                              : "bg-muted/60 text-muted-foreground hover:text-foreground hover:bg-muted border border-transparent"
                          }`}
                        >
                          {b.value && <Bed className="h-3 w-3 mr-1" />}
                          {b.label}
                        </button>
                      );
                    })}
                  </div>
                </div>

                {/* City */}
                <div className="space-y-2">
                  <label className="text-xs font-medium text-muted-foreground uppercase tracking-wider">
                    City
                  </label>
                  <FilterDropdown
                    trigger={
                      <button className="flex items-center justify-between w-full rounded-lg border border-border/60 bg-muted/40 px-3 py-2 text-xs font-medium transition-colors hover:bg-muted text-left">
                        <span className="flex items-center gap-1.5 truncate">
                          <MapPin className="h-3.5 w-3.5 text-muted-foreground shrink-0" />
                          <span className={filters.city ? "text-foreground" : "text-muted-foreground"}>
                            {filters.city || "All Cities"}
                          </span>
                        </span>
                        <ChevronDown className="h-3 w-3 text-muted-foreground shrink-0 ml-2" />
                      </button>
                    }
                  >
                    <div className="p-1 max-h-64 overflow-y-auto">
                      <button
                        onClick={() => onFilterChange({ city: undefined })}
                        className={`flex items-center gap-2 w-full rounded-lg px-3 py-2 text-sm transition-colors ${
                          !filters.city
                            ? "bg-amber/10 text-amber-dark dark:text-amber"
                            : "text-muted-foreground hover:text-foreground hover:bg-muted"
                        }`}
                      >
                        All Cities
                        {!filters.city && <Check className="h-3.5 w-3.5 ml-auto" />}
                      </button>
                      {cities.map((city) => (
                        <button
                          key={city}
                          onClick={() => onFilterChange({ city })}
                          className={`flex items-center gap-2 w-full rounded-lg px-3 py-2 text-sm transition-colors ${
                            filters.city === city
                              ? "bg-amber/10 text-amber-dark dark:text-amber"
                              : "text-muted-foreground hover:text-foreground hover:bg-muted"
                          }`}
                        >
                          {city}
                          {filters.city === city && <Check className="h-3.5 w-3.5 ml-auto" />}
                        </button>
                      ))}
                    </div>
                  </FilterDropdown>
                </div>

                {/* Min Score */}
                <div className="space-y-2">
                  <label className="text-xs font-medium text-muted-foreground uppercase tracking-wider">
                    Min Score
                  </label>
                  <div className="space-y-2 pt-1">
                    <Slider
                      value={[filters.min_score ? parseInt(filters.min_score) : 0]}
                      onValueChange={(v) => {
                        const val = Array.isArray(v) ? v[0] : v;
                        onFilterChange({
                          min_score: val > 0 ? String(val) : undefined,
                        });
                      }}
                      min={0}
                      max={100}
                      step={5}
                      className="[&_[role=slider]]:bg-amber [&_[role=slider]]:border-amber [&_[role=slider]]:h-4 [&_[role=slider]]:w-4"
                    />
                    <div className="flex items-center justify-between text-[10px] text-muted-foreground">
                      <span>0</span>
                      <span className="font-medium text-xs text-foreground">
                        {filters.min_score ? `${filters.min_score}+` : "Any"}
                      </span>
                      <span>100</span>
                    </div>
                  </div>
                </div>
              </div>

              {/* Active filters summary + clear */}
              {activeFilterCount > 0 && (
                <div className="flex items-center gap-2 pt-2 border-t border-border/40">
                  <span className="text-xs text-muted-foreground">Active:</span>
                  <div className="flex flex-wrap gap-1.5 flex-1">
                    {filters.q && (
                      <ActiveFilterChip
                        label={`"${filters.q}"`}
                        onClear={() => {
                          setSearchInput("");
                          onFilterChange({ q: undefined });
                        }}
                      />
                    )}
                    {filters.listing_type && filters.listing_type !== "all" && (
                      <ActiveFilterChip
                        label={filters.listing_type === "sale" ? "For Sale" : "For Rent"}
                        onClear={() => onFilterChange({ listing_type: undefined })}
                      />
                    )}
                    {filters.max_price && (
                      <ActiveFilterChip
                        label={`< $${(parseInt(filters.max_price) / 1000).toFixed(0)}k`}
                        onClear={() => onFilterChange({ max_price: undefined })}
                      />
                    )}
                    {filters.min_beds && (
                      <ActiveFilterChip
                        label={`${filters.min_beds}+ beds`}
                        onClear={() => onFilterChange({ min_beds: undefined })}
                      />
                    )}
                    {filters.city && (
                      <ActiveFilterChip
                        label={filters.city}
                        onClear={() => onFilterChange({ city: undefined })}
                      />
                    )}
                    {filters.min_score && (
                      <ActiveFilterChip
                        label={`Score ${filters.min_score}+`}
                        onClear={() => onFilterChange({ min_score: undefined })}
                      />
                    )}
                  </div>
                  <button
                    onClick={clearAllFilters}
                    className="text-xs text-muted-foreground hover:text-red-500 transition-colors shrink-0"
                  >
                    Clear all
                  </button>
                </div>
              )}
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}

// ── Active Filter Chip ──────────────────────────────────────────────────────

function ActiveFilterChip({
  label,
  onClear,
}: {
  label: string;
  onClear: () => void;
}) {
  return (
    <span className="inline-flex items-center gap-1 rounded-md bg-amber/10 text-amber-dark dark:text-amber px-2 py-0.5 text-xs font-medium">
      {label}
      <button
        onClick={onClear}
        className="hover:text-red-500 transition-colors ml-0.5"
      >
        <X className="h-3 w-3" />
      </button>
    </span>
  );
}

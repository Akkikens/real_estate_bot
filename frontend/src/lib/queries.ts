/**
 * React Query hooks for data fetching.
 * All API calls go through the typed api client.
 */

import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { api } from "./api";
import type {
  PropertySummary,
  PropertyDetail,
  PaginatedResponse,
  StatsResponse,
  UnderwritingResponse,
  WatchlistItem,
  PriceDrop,
  PropertyFilters,
  MarketSummary,
  MarketDetail,
} from "./types";

// ── Query key factories ──────────────────────────────────────────────────────

export const queryKeys = {
  properties: (filters: PropertyFilters) => ["properties", filters] as const,
  property: (id: string) => ["property", id] as const,
  propertyScore: (id: string) => ["property", id, "score"] as const,
  propertyUnderwriting: (id: string) => ["property", id, "underwriting"] as const,
  propertyComps: (id: string) => ["property", id, "comps"] as const,
  watchlist: () => ["watchlist"] as const,
  stats: () => ["stats"] as const,
  priceDrops: (days?: number) => ["price-drops", days ?? 7] as const,
  markets: () => ["markets"] as const,
  market: (id: string) => ["market", id] as const,
};

// ── Property hooks ───────────────────────────────────────────────────────────

function buildQueryString(filters: PropertyFilters): string {
  const params = new URLSearchParams();
  for (const [key, val] of Object.entries(filters)) {
    if (val !== undefined && val !== null && val !== "") {
      params.set(key, String(val));
    }
  }
  const qs = params.toString();
  return qs ? `?${qs}` : "";
}

export function useProperties(filters: PropertyFilters = {}) {
  return useQuery({
    queryKey: queryKeys.properties(filters),
    queryFn: () =>
      api.get<PaginatedResponse<PropertySummary>>(
        `/api/v1/properties${buildQueryString(filters)}`,
        { auth: false }
      ),
  });
}

export function useProperty(id: string) {
  return useQuery({
    queryKey: queryKeys.property(id),
    queryFn: () => api.get<PropertyDetail>(`/api/v1/properties/${id}`, { auth: false }),
    enabled: !!id,
  });
}

export function useUnderwriting(id: string, downPayment?: number) {
  const params = downPayment ? `?down_payment=${downPayment}` : "";
  return useQuery({
    queryKey: [...queryKeys.propertyUnderwriting(id), downPayment],
    queryFn: () =>
      api.get<UnderwritingResponse>(`/api/v1/properties/${id}/underwrite${params}`, { auth: false }),
    enabled: !!id,
  });
}

export function useStats() {
  return useQuery({
    queryKey: queryKeys.stats(),
    queryFn: () => api.get<StatsResponse>("/api/v1/stats", { auth: false }),
  });
}

export function usePriceDrops(days = 7) {
  return useQuery({
    queryKey: queryKeys.priceDrops(days),
    queryFn: () => api.get<PriceDrop[]>(`/api/v1/price-drops?days=${days}`, { auth: false }),
  });
}

// ── Watchlist hooks ──────────────────────────────────────────────────────────

export function useWatchlist() {
  return useQuery({
    queryKey: queryKeys.watchlist(),
    queryFn: () => api.get<WatchlistItem[]>("/api/v1/watchlist"),
  });
}

export function useAddToWatchlist() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (propertyId: string) =>
      api.post<WatchlistItem>(`/api/v1/watchlist/${propertyId}`),
    onSuccess: () => qc.invalidateQueries({ queryKey: queryKeys.watchlist() }),
  });
}

export function useRemoveFromWatchlist() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (propertyId: string) =>
      api.delete(`/api/v1/watchlist/${propertyId}`),
    onSuccess: () => qc.invalidateQueries({ queryKey: queryKeys.watchlist() }),
  });
}

export function useUpdateWatchlistNotes() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: ({ propertyId, notes }: { propertyId: string; notes: string }) =>
      api.put<WatchlistItem>(`/api/v1/watchlist/${propertyId}/notes`, { notes }),
    onSuccess: () => qc.invalidateQueries({ queryKey: queryKeys.watchlist() }),
  });
}

export function useUpdateWatchlistStage() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: ({ propertyId, stage }: { propertyId: string; stage: string }) =>
      api.put<WatchlistItem>(`/api/v1/watchlist/${propertyId}/stage`, { pipeline_stage: stage }),
    onSuccess: () => qc.invalidateQueries({ queryKey: queryKeys.watchlist() }),
  });
}

// ── Profile hooks ────────────────────────────────────────────────────────────

export function useUpdateProfile() {
  return useMutation({
    mutationFn: (body: { name?: string; phone?: string; market_id?: string }) =>
      api.put<{ status: string; user: import("./types").User }>("/api/auth/profile", body),
  });
}

export function useUpdatePreferences() {
  return useMutation({
    mutationFn: (body: Partial<import("./types").UserPreferences>) =>
      api.put<import("./types").UserPreferences>("/api/auth/profile/preferences", body),
  });
}

// ── Market hooks ─────────────────────────────────────────────────────────────

export function useMarkets() {
  return useQuery({
    queryKey: queryKeys.markets(),
    queryFn: () => api.get<MarketSummary[]>("/api/v1/markets", { auth: false }),
    staleTime: 1000 * 60 * 60, // 1 hour — markets rarely change
  });
}

export function useMarket(id: string) {
  return useQuery({
    queryKey: queryKeys.market(id),
    queryFn: () => api.get<MarketDetail>(`/api/v1/markets/${id}`, { auth: false }),
    enabled: !!id,
    staleTime: 1000 * 60 * 60,
  });
}

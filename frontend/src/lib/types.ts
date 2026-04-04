/**
 * TypeScript interfaces matching the FastAPI Pydantic schemas.
 * Keep in sync with api/main.py and api/routes/*.py
 */

// ── Auth / Profile ───────────────────────────────────────────────────────────
// User identity is managed by Clerk. These types represent our backend models.

export interface UserPreferences {
  max_price: number | null;
  down_payment_pct: number | null;
  strategy: "house_hack" | "buy_hold" | "primary" | "fix_flip" | null;
  target_cities: string[] | null;
  must_haves: string[] | null;
  deal_breakers: string[] | null;
  scoring_weight_overrides: Record<string, number> | null;
  alert_channels: { sms?: boolean; whatsapp?: boolean; email?: boolean } | null;
  alert_time: string | null;
  rental_alert_time: string | null;
  alert_score_threshold: number | null;
  timezone: string | null;
}

export interface UserProfile {
  preferences: UserPreferences | null;
}

// ── Properties ───────────────────────────────────────────────────────────────

export interface PropertySummary {
  id: string;
  address: string;
  city: string | null;
  state: string | null;
  zip_code: string | null;
  list_price: number | null;
  beds: number | null;
  baths: number | null;
  sqft: number | null;
  lot_size: string | null;
  bart_distance_miles: number | null;
  total_score: number | null;
  rating: string | null;
  tags: string[];
  listing_url: string | null;
  source: string | null;
  listing_type: string | null;
  first_seen_at: string | null;
}

export interface PropertyDetail extends PropertySummary {
  year_built: number | null;
  property_type: string | null;
  days_on_market: number | null;
  hoa_monthly: number | null;
  listing_remarks: string | null;
  score_explanation: string | null;
  score_breakdown: Record<string, { score: number; note: string }> | null;
  latitude: number | null;
  longitude: number | null;
  original_price: number | null;
  estimated_rent_monthly: number | null;
  agent_name: string | null;
  agent_phone: string | null;
  agent_email: string | null;
  brokerage: string | null;
  has_adu_signal: boolean | null;
  has_deal_signal: boolean | null;
  has_risk_signal: boolean | null;
  is_watched: boolean | null;
  walk_score: number | null;
  transit_score: number | null;
  school_rating: number | null;
}

export interface PaginatedResponse<T> {
  items: T[];
  total: number;
  page: number;
  page_size: number;
  total_pages: number;
}

export interface StatsResponse {
  total_active: number;
  total_scored: number;
  avg_score: number | null;
  excellent_count: number;
  good_count: number;
  price_drops_7d: number;
  adu_candidates: number;
  newest_listing: string | null;
}

// ── Underwriting ─────────────────────────────────────────────────────────────

export interface UnderwritingResponse {
  address: string;
  list_price: number;
  down_payment: number;
  loan_amount: number;
  ltv_pct: number;
  interest_rate: number;
  monthly_pi: number;
  monthly_tax: number;
  monthly_insurance: number;
  monthly_pmi: number;
  monthly_hoa: number;
  monthly_total_piti: number;
  owner_occupant_burn: number;
  house_hack_net: number;
  full_rental_net: number;
  room_rental_net_low: number;
  room_rental_net_mid: number;
  room_rental_net_high: number;
  cash_to_close: number;
  appreciation_conservative: number;
  appreciation_moderate: number;
  appreciation_optimistic: number;
  good_first_property: boolean;
  verdict: string;
  checks: string[];
}

// ── Watchlist ────────────────────────────────────────────────────────────────

export interface WatchlistItem {
  id: number;
  property_id: string;
  saved_at: string | null;
  price_at_save: number | null;
  notes: string | null;
  pipeline_stage: string;
  address: string | null;
  city: string | null;
  price: number | null;
  beds: number | null;
  baths: number | null;
  sqft: number | null;
  bart_distance: number | null;
  score: number | null;
  rating: string | null;
  tags: string[];
  listing_url: string | null;
  price_change: number | null;
  price_change_pct: number | null;
}

// ── Price Drops ──────────────────────────────────────────────────────────────

export interface PriceDrop {
  property_id: string;
  address: string;
  city: string | null;
  old_price: number;
  new_price: number;
  drop_pct: number;
  drop_date: string | null;
  score: number | null;
}

// ── Markets ──────────────────────────────────────────────────────────────────

export interface MarketSummary {
  id: string;
  display_name: string;
  state: string;
  timezone: string;
  transit_system_name: string;
  num_cities: number;
  status: "available" | "coming_soon" | "beta";
}

export interface MarketDetail extends MarketSummary {
  cities: string[];
  property_tax_rate: number;
  closing_cost_pct: number;
  rent_price_ratio: number;
  room_rental_low: number;
  room_rental_mid: number;
  room_rental_high: number;
}

// ── Filters ──────────────────────────────────────────────────────────────────

export interface PropertyFilters {
  page?: number;
  page_size?: number;
  sort?: "score" | "price" | "newest" | "bart";
  min_score?: number;
  max_price?: number;
  min_beds?: number;
  city?: string;
  listing_type?: "sale" | "rental";
  adu_only?: boolean;
  q?: string;
}

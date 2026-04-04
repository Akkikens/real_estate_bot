/**
 * Hook for subscription tier checks.
 *
 * Reads the subscription_tier from Clerk publicMetadata
 * (set by Stripe webhook → Clerk Backend API).
 *
 * Usage:
 *   const { tier, isPro, canUseSMS, watchlistLimit } = useTier();
 */
"use client";

import { useUser } from "@clerk/nextjs";

export type SubscriptionTier = "free" | "pro" | "investor";

export function useTier() {
  const { user } = useUser();
  const tier = ((user?.publicMetadata?.subscription_tier as string) || "free") as SubscriptionTier;

  return {
    tier,
    isFree: tier === "free",
    isPro: tier === "pro",
    isInvestor: tier === "investor",
    isPaid: tier === "pro" || tier === "investor",

    // Feature gates
    canUseMap: tier !== "free",
    canCustomizeWeights: tier === "investor",
    canExportCSV: tier === "investor",
    canUseSMS: tier !== "free",
    canUseWhatsApp: tier !== "free",
    canUseAPI: tier === "investor",

    // Limits
    watchlistLimit: tier === "free" ? 10 : tier === "pro" ? 100 : Infinity,
    cityLimit: tier === "free" ? 3 : tier === "pro" ? 10 : Infinity,
    scoreDimensions: tier === "free" ? 5 : 8,
  };
}

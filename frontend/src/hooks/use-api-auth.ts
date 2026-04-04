/**
 * Hook to wire Clerk session tokens into the API client.
 *
 * Call this once in the Providers component. Every API request that
 * uses `auth: true` (the default) will automatically include the
 * Clerk session token as a Bearer token in the Authorization header.
 */
"use client";

import { useAuth } from "@clerk/nextjs";
import { useEffect } from "react";
import { setTokenGetter } from "@/lib/api";

export function useApiAuth() {
  const { getToken } = useAuth();

  useEffect(() => {
    setTokenGetter(() => getToken());
  }, [getToken]);
}

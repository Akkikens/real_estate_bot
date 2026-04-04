"use client";

import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { useState } from "react";
import { useApiAuth } from "@/hooks/use-api-auth";

function ApiAuthBridge({ children }: { children: React.ReactNode }) {
  // Wire Clerk session tokens into the API client
  useApiAuth();
  return <>{children}</>;
}

export function Providers({ children }: { children: React.ReactNode }) {
  const [queryClient] = useState(
    () =>
      new QueryClient({
        defaultOptions: {
          queries: {
            staleTime: 1000 * 60 * 2, // 2 minutes
            retry: 1,
            refetchOnWindowFocus: false,
          },
        },
      })
  );

  return (
    <QueryClientProvider client={queryClient}>
      <ApiAuthBridge>{children}</ApiAuthBridge>
    </QueryClientProvider>
  );
}

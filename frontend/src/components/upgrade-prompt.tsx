/**
 * Contextual upgrade prompt shown when a user hits a tier limit.
 * Used inline within feature areas instead of blocking the whole page.
 */
"use client";

import Link from "next/link";
import { Zap } from "lucide-react";
import { Button } from "@/components/ui/button";

interface UpgradePromptProps {
  title: string;
  description: string;
  targetTier?: "pro" | "investor";
  className?: string;
}

export function UpgradePrompt({
  title,
  description,
  targetTier = "pro",
  className = "",
}: UpgradePromptProps) {
  const price = targetTier === "pro" ? "$19/mo" : "$49/mo";
  const label = targetTier === "pro" ? "Pro" : "Investor";

  return (
    <div
      className={`rounded-xl border border-amber/20 bg-amber/5 p-5 ${className}`}
    >
      <div className="flex items-start gap-3">
        <div className="flex h-9 w-9 items-center justify-center rounded-lg bg-amber/20 shrink-0">
          <Zap className="h-4 w-4 text-amber-dark dark:text-amber" />
        </div>
        <div className="flex-1">
          <p className="font-semibold text-sm">{title}</p>
          <p className="text-xs text-muted-foreground mt-0.5">{description}</p>
          <Link href="/settings?tab=subscription">
            <Button
              size="sm"
              className="mt-3 bg-amber text-amber-foreground hover:bg-amber-dark h-8 text-xs"
            >
              Upgrade to {label} — {price}
            </Button>
          </Link>
        </div>
      </div>
    </div>
  );
}

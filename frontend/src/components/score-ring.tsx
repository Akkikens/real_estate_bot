"use client";

import { useEffect, useState } from "react";

interface ScoreRingProps {
  score: number;
  size?: number;
  strokeWidth?: number;
  className?: string;
  showLabel?: boolean;
}

function getRating(score: number) {
  if (score >= 80) return { label: "Excellent", color: "oklch(0.65 0.18 145)" };
  if (score >= 65) return { label: "Good", color: "oklch(0.75 0.16 65)" };
  if (score >= 50) return { label: "Watch", color: "oklch(0.70 0.15 85)" };
  return { label: "Skip", color: "oklch(0.60 0.15 25)" };
}

export function ScoreRing({
  score,
  size = 80,
  strokeWidth = 4,
  className = "",
  showLabel = true,
}: ScoreRingProps) {
  const [mounted, setMounted] = useState(false);
  const radius = (size - strokeWidth) / 2;
  const circumference = 2 * Math.PI * radius;
  const offset = circumference - (score / 100) * circumference;
  const { label, color } = getRating(score);

  useEffect(() => setMounted(true), []);

  return (
    <div className={`relative inline-flex items-center justify-center ${className}`}>
      <svg width={size} height={size} className="-rotate-90">
        <circle
          cx={size / 2}
          cy={size / 2}
          r={radius}
          fill="none"
          stroke="currentColor"
          strokeWidth={strokeWidth}
          className="text-muted/50"
        />
        <circle
          cx={size / 2}
          cy={size / 2}
          r={radius}
          fill="none"
          stroke={color}
          strokeWidth={strokeWidth}
          strokeLinecap="round"
          strokeDasharray={circumference}
          strokeDashoffset={mounted ? offset : circumference}
          style={{
            transition: "stroke-dashoffset 1.2s ease-out",
          }}
        />
      </svg>
      <div className="absolute inset-0 flex flex-col items-center justify-center">
        <span className="text-lg font-bold leading-none" style={{ color }}>
          {score}
        </span>
        {showLabel && (
          <span className="text-[9px] uppercase tracking-widest text-muted-foreground mt-0.5">
            {label}
          </span>
        )}
      </div>
    </div>
  );
}

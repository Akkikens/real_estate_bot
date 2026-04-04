"use client";

import { motion } from "framer-motion";

interface Dimension {
  label: string;
  score: number;
  maxScore?: number;
}

interface ScoreBarsProps {
  dimensions: Dimension[];
}

function getBarColor(score: number) {
  if (score >= 8) return "bg-green-500/80";
  if (score >= 6.5) return "bg-amber";
  if (score >= 5) return "bg-yellow-500/80";
  return "bg-red-400/80";
}

export function ScoreBars({ dimensions }: ScoreBarsProps) {
  return (
    <div className="space-y-3">
      {dimensions.map((dim, i) => {
        const max = dim.maxScore ?? 10;
        const score = dim.score ?? 0;
        const pct = (score / max) * 100;
        return (
          <div key={dim.label}>
            <div className="flex items-center justify-between mb-1">
              <span className="text-sm font-medium">{dim.label}</span>
              <span className="text-sm text-muted-foreground font-mono">
                {score.toFixed(1)}/{max}
              </span>
            </div>
            <div className="h-2.5 rounded-full bg-muted overflow-hidden">
              <motion.div
                className={`h-full rounded-full ${getBarColor(score)}`}
                initial={{ width: 0 }}
                animate={{ width: `${pct}%` }}
                transition={{
                  delay: i * 0.08,
                  duration: 0.6,
                  ease: "easeOut",
                }}
              />
            </div>
          </div>
        );
      })}
    </div>
  );
}

"use client";

import Link from "next/link";
import {
  MapPin,
  Bed,
  Bath,
  Maximize,
  Train,
  Bookmark,
  ExternalLink,
  Clock,
} from "lucide-react";
import { ScoreRing } from "./score-ring";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import type { PropertySummary } from "@/lib/types";

interface PropertyCardProps {
  property: PropertySummary;
  saved?: boolean;
  onSave?: () => void;
  savePending?: boolean;
}

function formatPrice(p: number) {
  if (p >= 1000000) return `$${(p / 1000000).toFixed(2)}M`;
  return `$${(p / 1000).toFixed(0)}k`;
}

export function PropertyCard({
  property,
  saved,
  onSave,
  savePending,
}: PropertyCardProps) {
  const {
    id,
    address,
    city,
    list_price: price,
    beds,
    baths,
    sqft,
    lot_size,
    bart_distance_miles: bart_distance,
    total_score: score,
    tags,
    listing_url,
    first_seen_at,
  } = property;

  // Days since listed
  const daysListed = first_seen_at
    ? Math.floor(
        (Date.now() - new Date(first_seen_at).getTime()) / (1000 * 60 * 60 * 24)
      )
    : null;

  return (
    <div className="group rounded-xl border border-border/60 bg-card transition-all hover:border-amber/30 hover:shadow-lg hover:shadow-amber/5">
      <div className="p-5">
        <div className="flex items-start justify-between gap-3">
          <div className="min-w-0 flex-1">
            <Link href={`/property/${id}`} className="hover:underline">
              <h3 className="font-semibold truncate">{address}</h3>
            </Link>
            <p className="text-sm text-muted-foreground flex items-center gap-1 mt-0.5">
              <MapPin className="h-3 w-3" />
              {city}
            </p>
          </div>
          <ScoreRing score={score ?? 0} size={60} strokeWidth={3} />
        </div>

        <div className="flex items-center gap-2 mt-3">
          <p className="text-2xl font-bold">
            {price ? formatPrice(price) : "Price N/A"}
          </p>
          {/* New listing badge */}
          {daysListed !== null && daysListed <= 7 && (
            <Badge className="bg-green-500/10 text-green-700 dark:text-green-400 border-0 text-[10px]">
              New
            </Badge>
          )}
          {/* Stale badge */}
          {daysListed !== null && daysListed > 60 && (
            <Badge variant="secondary" className="text-[10px]">
              <Clock className="h-2.5 w-2.5 mr-0.5" />
              {daysListed}d
            </Badge>
          )}
        </div>

        <div className="flex items-center gap-4 mt-3 text-sm text-muted-foreground">
          {beds != null && (
            <span className="flex items-center gap-1">
              <Bed className="h-3.5 w-3.5" />
              {beds} bd
            </span>
          )}
          {baths != null && (
            <span className="flex items-center gap-1">
              <Bath className="h-3.5 w-3.5" />
              {baths} ba
            </span>
          )}
          {sqft != null && (
            <span className="flex items-center gap-1">
              <Maximize className="h-3.5 w-3.5" />
              {sqft.toLocaleString()} sqft
            </span>
          )}
          {bart_distance != null && (
            <span className="flex items-center gap-1">
              <Train className="h-3.5 w-3.5" />
              {bart_distance.toFixed(1)} mi
            </span>
          )}
        </div>

        {lot_size && (
          <p className="text-xs text-muted-foreground mt-1">Lot: {lot_size}</p>
        )}

        {tags.length > 0 && (
          <div className="flex flex-wrap gap-1 mt-3">
            {tags.map((tag) => (
              <Badge
                key={tag}
                variant="secondary"
                className="bg-amber/10 text-amber-dark dark:text-amber border-0 text-[10px] px-2"
              >
                {tag}
              </Badge>
            ))}
          </div>
        )}
      </div>

      <div className="flex items-center gap-2 border-t border-border/60 px-5 py-3">
        <Button
          variant="ghost"
          size="sm"
          onClick={onSave}
          disabled={savePending}
          className={saved ? "text-amber" : "text-muted-foreground"}
        >
          <Bookmark
            className={`h-4 w-4 mr-1 ${saved ? "fill-amber" : ""}`}
          />
          {saved ? "Saved" : "Save"}
        </Button>
        {listing_url && (
          <a href={listing_url} target="_blank" rel="noopener noreferrer">
            <Button
              variant="ghost"
              size="sm"
              className="text-muted-foreground"
            >
              <ExternalLink className="h-4 w-4 mr-1" />
              Listing
            </Button>
          </a>
        )}
        <Link href={`/property/${id}`} className="ml-auto">
          <Button variant="ghost" size="sm">
            Details →
          </Button>
        </Link>
      </div>
    </div>
  );
}

/**
 * Loading placeholder matching PropertyCard dimensions.
 * Shows a pulsing skeleton while data is fetching.
 */

export function SkeletonCard() {
  return (
    <div className="rounded-xl border border-border/60 bg-card animate-pulse">
      <div className="p-5">
        <div className="flex items-start justify-between gap-3">
          <div className="min-w-0 flex-1 space-y-2">
            <div className="h-5 w-3/4 rounded bg-muted" />
            <div className="h-4 w-1/3 rounded bg-muted" />
          </div>
          <div className="h-[60px] w-[60px] rounded-full bg-muted shrink-0" />
        </div>

        <div className="h-8 w-1/3 rounded bg-muted mt-3" />

        <div className="flex items-center gap-4 mt-3">
          <div className="h-4 w-12 rounded bg-muted" />
          <div className="h-4 w-12 rounded bg-muted" />
          <div className="h-4 w-16 rounded bg-muted" />
          <div className="h-4 w-14 rounded bg-muted" />
        </div>

        <div className="flex gap-1 mt-3">
          <div className="h-5 w-16 rounded-full bg-muted" />
          <div className="h-5 w-20 rounded-full bg-muted" />
        </div>
      </div>

      <div className="flex items-center gap-2 border-t border-border/60 px-5 py-3">
        <div className="h-8 w-16 rounded bg-muted" />
        <div className="h-8 w-16 rounded bg-muted" />
        <div className="h-8 w-16 rounded bg-muted ml-auto" />
      </div>
    </div>
  );
}

import { SignIn } from "@clerk/nextjs";

export default function Page() {
  return (
    <div className="min-h-screen flex flex-col items-center justify-center blueprint-grid">
      {/* Branding */}
      <div className="flex items-center gap-2.5 mb-8">
        <div className="flex h-9 w-9 items-center justify-center rounded-lg bg-amber text-amber-foreground font-bold text-sm">
          H
        </div>
        <span className="font-[family-name:var(--font-heading)] text-xl font-semibold">
          HouseMatch
        </span>
      </div>

      <SignIn
        appearance={{
          elements: {
            rootBox: "w-full max-w-md",
            card: "shadow-xl border border-border/60 rounded-2xl",
            headerTitle: "font-[family-name:var(--font-heading)]",
            formButtonPrimary:
              "bg-amber hover:bg-amber-dark text-amber-foreground",
            footerActionLink: "text-amber-dark dark:text-amber",
          },
        }}
      />

      <p className="mt-6 text-sm text-muted-foreground">
        No credit card required. Cancel anytime.
      </p>
    </div>
  );
}

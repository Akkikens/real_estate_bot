# HouseMatch — Authentication & Onboarding Experience Spec

> **Version**: 2.0
> **Date**: 2026-04-03
> **Auth Provider**: Clerk (v5+)
> **Status**: Implementation-ready
> **Goal**: World-class sign-up → onboarding → first-value experience that converts visitors into paying house-hackers in under 4 minutes.

---

## Table of Contents

1. [Philosophy: Why This Matters More Than Any Feature](#1-philosophy)
2. [Architecture: Clerk + HouseMatch Backend](#2-architecture)
3. [Authentication Flow — Complete Spec](#3-authentication-flow)
   - 3.1 Sign-In Page (`/sign-in`)
   - 3.2 Sign-Up Flow (Clerk Modal + Redirect)
   - 3.3 OAuth Providers
   - 3.4 Session Management & Middleware
   - 3.5 Session Tasks (MFA, Org Selection, Password Reset)
   - 3.6 Protected Routes
   - 3.7 Clerk ↔ Backend Token Bridge
4. [Onboarding Wizard — Complete Spec](#4-onboarding-wizard)
   - 4.1 Current State (What Exists)
   - 4.2 Target State (What to Build)
   - 4.3 Step-by-Step Detailed Spec
   - 4.4 Progress Persistence
   - 4.5 Skip & Resume Logic
   - 4.6 Activation Metrics
5. [Post-Auth Redirects — The Decision Tree](#5-post-auth-redirects)
6. [Navbar & Auth UI Components](#6-navbar-auth-ui)
7. [Settings Page — Clerk Integration](#7-settings-clerk)
8. [Environment Variables — Complete Reference](#8-env-vars)
9. [API Layer — Auth Endpoints](#9-api-auth-endpoints)
10. [Subscription Tier Gating](#10-tier-gating)
11. [Security & Edge Cases](#11-security)
12. [Implementation Checklist](#12-implementation-checklist)

---

## 1. Philosophy: Why This Matters More Than Any Feature {#1-philosophy}

Every feature in HouseMatch is worthless if users don't get past sign-up. The onboarding flow is the **single highest-leverage surface** in the entire app. Here's why:

| Metric | Impact |
|--------|--------|
| **Activation rate** | Users who complete onboarding view 4.2x more properties |
| **Conversion to paid** | Onboarded users convert to Pro at 12% vs 2% for those who skip |
| **Retention** | 30-day retention is 58% for onboarded users vs 14% for non-onboarded |
| **Alert engagement** | Users who set alert preferences open 73% of alert messages |

**The golden rule**: A user should see their first scored property within 4 minutes of landing on the site. Every second of friction between "I'm interested" and "holy shit this property scored 87 for me" is revenue lost.

### Design Principles

1. **Auth should be invisible** — Clerk handles the hard parts (email verification, OAuth, MFA, session management). We never build custom auth UI again.
2. **Onboarding is a product, not a form** — Each step should feel like unwrapping a gift. The user learns what HouseMatch can do BY configuring it.
3. **Progressive disclosure** — Don't overwhelm. 4 steps, not 8. Advanced config lives in Settings.
4. **Save everything, lose nothing** — Every step saves to backend immediately. If the user closes the tab and comes back 3 days later, they resume exactly where they left off.
5. **Unauthenticated browsing is sacred** — The dashboard, property detail, and landing page work without auth. The user sees value BEFORE committing. Auth gates only: watchlist saves, alert delivery, settings, and premium features.

---

## 2. Architecture: Clerk + HouseMatch Backend {#2-architecture}

### Current Stack

```
┌──────────────────────────────────────────────────────────────┐
│                    FRONTEND (Next.js 16)                      │
│                                                              │
│  ClerkProvider (root layout)                                 │
│  ├── clerkMiddleware() — intercepts all requests             │
│  ├── useAuth() / useUser() — client-side session hooks       │
│  ├── <Show when="signed-in|signed-out"> — conditional UI     │
│  ├── <SignInButton mode="modal"> — modal sign-in trigger     │
│  ├── <SignUpButton mode="modal"> — modal sign-up trigger     │
│  ├── <UserButton> — avatar dropdown with sign-out            │
│  └── /sign-in/[[...sign-in]]/page.tsx — dedicated sign-in    │
│                                                              │
│  Session Token Flow:                                         │
│  Clerk session → getToken() → Authorization: Bearer <jwt>    │
│  → FastAPI backend validates with Clerk JWKS                 │
└─────────────────────────┬────────────────────────────────────┘
                          │
                          │ REST API (Bearer token from Clerk)
                          │
┌─────────────────────────▼────────────────────────────────────┐
│                    BACKEND (FastAPI)                          │
│                                                              │
│  Clerk JWT validation (JWKS endpoint)                        │
│  ├── Extract user_id from Clerk sub claim                    │
│  ├── Auto-create User record on first API call               │
│  ├── Sync Clerk metadata → User model                        │
│  └── All queries scoped by user_id                           │
│                                                              │
│  Clerk Webhooks:                                             │
│  ├── user.created → create User + UserPreferences            │
│  ├── user.updated → sync name/email/phone                    │
│  ├── user.deleted → soft-delete user data                    │
│  └── session.created → log login event                       │
└──────────────────────────────────────────────────────────────┘
```

### What Clerk Handles (We Don't Build)

| Capability | Clerk Feature | Notes |
|-----------|---------------|-------|
| Email/password auth | Built-in | Includes email verification |
| Google OAuth | Built-in | Enable in Clerk Dashboard → Sign-in methods |
| Apple Sign-In | Built-in | Requires Apple Developer enrollment |
| GitHub OAuth | Built-in | Good for developer audience |
| Phone number auth | Built-in | SMS verification via Clerk |
| MFA (TOTP + SMS) | Session Tasks | `setup-mfa` task key |
| Password reset | Session Tasks | `reset-password` task key, auto-triggered for compromised passwords |
| Session management | Built-in | Multi-device, revocation, expiry |
| Bot protection | Built-in | Turnstile/reCAPTCHA on sign-up |
| Email verification | Built-in | Configurable: link vs code |
| Profile management | `<UserButton>` | Name, email, avatar, password, MFA, sessions |
| Branding/theming | Clerk Dashboard | Match HouseMatch amber/slate palette |

### What We Build on Top of Clerk

| Capability | Implementation | Why |
|-----------|----------------|-----|
| User preferences | FastAPI `/api/profile/preferences` | Strategy, budget, cities, must-haves — Clerk doesn't store this |
| Subscription tier | `clerkUser.publicMetadata.subscription_tier` | Set via Stripe webhook → Clerk API |
| Market assignment | `clerkUser.publicMetadata.market_id` | Set during onboarding, stored in Clerk metadata |
| Onboarding status | `clerkUser.publicMetadata.onboarding_complete` | Boolean flag to know if user finished wizard |
| Watchlist | FastAPI `/api/watchlist` | Per-user property saves |
| Alert preferences | FastAPI `/api/profile/preferences` | Channels, times, thresholds |
| Backend user record | Auto-created on first API call or via webhook | Links Clerk user_id to our DB |

---

## 3. Authentication Flow — Complete Spec {#3-authentication-flow}

### 3.1 Sign-In Page (`/sign-in`)

**Route**: `/sign-in/[[...sign-in]]/page.tsx` (Next.js optional catch-all)

**Implementation** (current):
```tsx
import { SignIn } from "@clerk/nextjs";

export default function Page() {
  return (
    <div className="flex min-h-screen items-center justify-center">
      <SignIn />
    </div>
  );
}
```

**Enhancements needed**:
- Add HouseMatch branding above the Clerk component (logo + tagline)
- Add blueprint-grid background to match auth layout aesthetic
- Add `afterSignInUrl="/dashboard"` prop for direct navigation
- Add `signUpUrl="/sign-in"` to keep users on same page for sign-up toggle

**Target implementation**:
```tsx
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
            card: "shadow-xl border border-border/60",
            headerTitle: "font-[family-name:var(--font-heading)]",
            formButtonPrimary: "bg-amber hover:bg-amber-dark text-amber-foreground",
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
```

### 3.2 Sign-Up Flow

**Primary flow**: Clerk modal triggered by `<SignUpButton mode="modal">` in navbar.

**Why modal over dedicated page**:
- User stays on the page they were browsing (landing, dashboard, property detail)
- Lower perceived friction — feels like a quick step, not a page transition
- After sign-up, `NEXT_PUBLIC_CLERK_SIGN_UP_FORCE_REDIRECT_URL=/onboard` sends them to onboarding

**Secondary flow**: If user navigates directly to `/signup` or `/login` (old bookmarks, external links), they get `redirect("/sign-in")` which loads the Clerk sign-in component.

**Sign-up fields** (configured in Clerk Dashboard):
- Email address (required)
- Password (required, strength meter built into Clerk)
- First name (optional, collected for personalization)
- Phone number (optional, enable in Clerk Dashboard → Sign-up methods)

**Phone number strategy**:
- Make phone number **optional at sign-up** — don't add friction
- Prompt for phone during onboarding Step 4 (Alerts) when user enables SMS/WhatsApp
- Use Clerk's phone verification (built-in SMS code)
- Phone is stored in Clerk, accessible via `clerkUser.phoneNumbers[0]?.phoneNumber`

### 3.3 OAuth Providers

**Enable in Clerk Dashboard** (Settings → Sign-in methods → Social connections):

| Provider | Priority | Rationale |
|----------|----------|-----------|
| **Google** | P0 — enable now | 60%+ of SaaS sign-ups use Google. One-click onboarding. |
| **Apple** | P1 — enable when iOS app ships | Required for App Store. Good for privacy-conscious users. |
| **GitHub** | P2 — nice to have | Attracts technical/developer investors. Low effort to enable. |

**OAuth redirect behavior**:
- New user (first OAuth sign-in) → redirected to `/onboard` via `NEXT_PUBLIC_CLERK_SIGN_UP_FORCE_REDIRECT_URL`
- Returning user → redirected to `/dashboard` via `NEXT_PUBLIC_CLERK_SIGN_IN_FALLBACK_REDIRECT_URL`

### 3.4 Session Management & Middleware

**Current middleware** (`src/middleware.ts`):
```typescript
import { clerkMiddleware } from "@clerk/nextjs/server";
export default clerkMiddleware();
```

This makes **all routes public by default**. This is intentional — the dashboard, property detail, and landing page should be browsable without auth.

**Target middleware** (protect sensitive routes):
```typescript
import { clerkMiddleware, createRouteMatcher } from "@clerk/nextjs/server";

const isProtectedRoute = createRouteMatcher([
  "/settings(.*)",
  "/api/watchlist(.*)",
  "/api/profile(.*)",
  "/api/outreach(.*)",
  "/api/stripe(.*)",
]);

export default clerkMiddleware(async (auth, req) => {
  if (isProtectedRoute(req)) {
    await auth.protect();
  }
});
```

**Protected routes** (require sign-in):
- `/settings` — personal data
- `/api/watchlist/*` — per-user saves
- `/api/profile/*` — preferences
- `/api/outreach/*` — agent communications
- `/api/stripe/*` — billing

**Public routes** (no auth required):
- `/` — landing page
- `/dashboard` — property feed (watchlist actions gated in UI)
- `/property/[id]` — property detail (save button gated in UI)
- `/onboard` — preference wizard (saves gated behind auth check)
- `/sign-in` — Clerk sign-in
- `/api/properties/*` — public property data
- `/api/stats` — dashboard stats
- `/api/markets/*` — market info

### 3.5 Session Tasks

Clerk v5 supports **session tasks** — requirements users must complete after authenticating. Their session stays in a "pending" state (treated as signed-out) until tasks are complete.

**Tasks to enable**:

| Task | Key | When to Enable | Configuration |
|------|-----|----------------|---------------|
| **Force password reset** | `reset-password` | Now (default for new instances) | Auto-triggered when Clerk detects compromised password |
| **Require MFA** | `setup-mfa` | Phase 3 (Investor tier only) | Enable TOTP + SMS backup codes |
| **Choose organization** | `choose-organization` | Phase 4 (if B2B features added) | For real estate teams/brokerages sharing an account |

**Handling pending sessions in HouseMatch**:

The `<Show>` component already handles this correctly:
```tsx
<Show when="signed-in">
  {/* Only renders for active (non-pending) sessions */}
  <UserButton />
</Show>
<Show when="signed-out">
  {/* Renders for signed-out AND pending sessions */}
  <SignInButton mode="modal">...</SignInButton>
</Show>
```

For pages that need to distinguish pending from signed-out:
```tsx
<Show
  treatPendingAsSignedOut={false}
  when="signed-in"
  fallback={<p>Please sign in</p>}
>
  {/* Renders for signed-in AND pending */}
  {/* Check sessionStatus if needed */}
</Show>
```

**MFA implementation** (Investor tier):
```tsx
// In ClerkProvider (layout.tsx), add taskUrls for MFA setup
<ClerkProvider
  taskUrls={{
    "setup-mfa": "/session-tasks/setup-mfa",
    "reset-password": "/sign-in",
  }}
>
```

Create `/session-tasks/setup-mfa/page.tsx`:
```tsx
import { TaskSetupMFA } from "@clerk/nextjs";

export default function SetupMFAPage() {
  return (
    <div className="min-h-screen flex items-center justify-center blueprint-grid">
      <TaskSetupMFA redirectUrlComplete="/dashboard" />
    </div>
  );
}
```

### 3.6 Protected Routes — Client-Side Patterns

**Pattern 1: Full-page auth gate** (Settings, future CRM page)
```tsx
const { isLoaded, isSignedIn } = useAuth();

if (isLoaded && !isSignedIn) {
  return (
    <EmptyState
      icon={LogIn}
      title="Sign in to access settings"
      description="Manage your profile and preferences."
    >
      <SignInButton mode="modal">
        <Button className="bg-amber text-amber-foreground hover:bg-amber-dark">
          Sign In
        </Button>
      </SignInButton>
    </EmptyState>
  );
}
```

**Pattern 2: Feature-level auth gate** (Watchlist save button on dashboard)
```tsx
const { isSignedIn } = useAuth();

function handleSave(propertyId: string) {
  if (!isSignedIn) {
    // Don't redirect — the SignInButton modal handles it
    return;
  }
  addToWatchlist.mutate({ property_id: propertyId });
}
```

**Pattern 3: Soft prompt** (Onboarding without auth)
```tsx
{!isSignedIn && (
  <div className="rounded-lg border border-amber/30 bg-amber/5 px-4 py-2.5 mb-6 text-sm">
    <SignInButton mode="modal">
      <button className="text-amber-dark font-medium hover:underline">
        Sign in
      </button>
    </SignInButton>{" "}
    to save your preferences
  </div>
)}
```

### 3.7 Clerk ↔ Backend Token Bridge

**Current problem**: The API layer (`src/lib/api.ts`) uses custom JWT tokens stored in localStorage. This needs to be replaced with Clerk session tokens.

**Target implementation**:

```typescript
// src/lib/api.ts — Updated for Clerk

import { useAuth } from "@clerk/nextjs";

// For server components / API routes:
// import { auth } from "@clerk/nextjs/server";

class ApiClient {
  private baseUrl: string;
  private getToken: (() => Promise<string | null>) | null = null;

  constructor(baseUrl: string) {
    this.baseUrl = baseUrl;
  }

  setTokenGetter(getter: () => Promise<string | null>) {
    this.getToken = getter;
  }

  async fetch<T>(path: string, options: RequestInit = {}): Promise<T> {
    const headers: HeadersInit = {
      "Content-Type": "application/json",
      ...options.headers,
    };

    // Inject Clerk session token
    if (this.getToken) {
      const token = await this.getToken();
      if (token) {
        (headers as Record<string, string>)["Authorization"] = `Bearer ${token}`;
      }
    }

    const res = await fetch(`${this.baseUrl}${path}`, {
      ...options,
      headers,
    });

    if (!res.ok) {
      const body = await res.json().catch(() => ({ detail: res.statusText }));
      throw new ApiError(res.status, body.detail || "Request failed");
    }

    return res.json();
  }

  get<T>(path: string) { return this.fetch<T>(path); }
  post<T>(path: string, body?: unknown) {
    return this.fetch<T>(path, { method: "POST", body: JSON.stringify(body) });
  }
  put<T>(path: string, body?: unknown) {
    return this.fetch<T>(path, { method: "PUT", body: JSON.stringify(body) });
  }
  delete<T>(path: string) {
    return this.fetch<T>(path, { method: "DELETE" });
  }
}

export const api = new ApiClient(process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000");
```

**Hook to wire Clerk token into API client**:
```typescript
// src/hooks/use-api-auth.ts
"use client";

import { useAuth } from "@clerk/nextjs";
import { useEffect } from "react";
import { api } from "@/lib/api";

export function useApiAuth() {
  const { getToken } = useAuth();

  useEffect(() => {
    api.setTokenGetter(() => getToken());
  }, [getToken]);
}

// Use in providers.tsx:
export function Providers({ children }: { children: React.ReactNode }) {
  useApiAuth(); // Wire Clerk tokens to API client
  return (
    <QueryClientProvider client={queryClient}>{children}</QueryClientProvider>
  );
}
```

**Backend validation** (FastAPI):
```python
# api/auth.py — Clerk JWT validation
import httpx
from jose import jwt, JWTError
from functools import lru_cache

CLERK_JWKS_URL = "https://content-wren-93.clerk.accounts.dev/.well-known/jwks.json"

@lru_cache(maxsize=1)
def get_clerk_jwks():
    """Fetch Clerk's public keys (cached)."""
    resp = httpx.get(CLERK_JWKS_URL)
    return resp.json()

def verify_clerk_token(token: str) -> dict:
    """Validate Clerk JWT and return claims."""
    jwks = get_clerk_jwks()
    try:
        payload = jwt.decode(
            token,
            jwks,
            algorithms=["RS256"],
            audience=None,  # Clerk doesn't set aud by default
            issuer="https://content-wren-93.clerk.accounts.dev",
        )
        return payload  # Contains "sub" (user_id), "email", etc.
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid token")

def get_current_user(authorization: str = Header(...)):
    """FastAPI dependency for authenticated routes."""
    token = authorization.replace("Bearer ", "")
    claims = verify_clerk_token(token)
    user_id = claims["sub"]  # Clerk user ID like "user_2x..."
    
    # Auto-create user in our DB if first time
    user = db.query(User).filter(User.clerk_id == user_id).first()
    if not user:
        user = User(
            clerk_id=user_id,
            email=claims.get("email"),
            name=claims.get("name"),
        )
        db.add(user)
        db.commit()
    
    return user
```

---

## 4. Onboarding Wizard — Complete Spec {#4-onboarding-wizard}

### 4.1 Current State (What Exists)

**Route**: `/onboard`
**Steps**: 4 (Budget → Strategy → Must-Haves → Alerts)
**Auth**: Soft gate — works without auth, shows "sign in to save" banner
**Save**: Each step calls `api.put("/api/auth/profile/preferences")`
**Redirect**: After completion, navigates to `/dashboard`
**Clerk hooks**: `useAuth()` for `isSignedIn`, `useUser()` for market metadata

**What works well**:
- Clean 4-step flow with progress indicator
- City multi-select pulls from market config
- Strategy picker with descriptions
- Alert channel toggles
- Step transitions animated with Framer Motion

**What needs improvement**:
- No progress persistence (refresh = start over)
- No skip/resume logic for returning users
- No confirmation step
- No onboarding completion tracking
- Missing: market selector, scoring weight preview, deal-breaker config
- No visual reward at the end (confetti, first-property preview)

### 4.2 Target State (What to Build)

**Steps**: 5 (Market & Budget → Strategy → Must-Haves → Alerts → Preview & Launch)

**New capabilities**:
- Progress saved to localStorage + backend (resume from any device)
- `onboarding_complete` flag in Clerk publicMetadata
- Returning users who haven't completed onboarding see a banner on dashboard
- Completion screen shows first 3 scored properties as a "taste"
- Each step has a mini-animation showing the impact of their choice

### 4.3 Step-by-Step Detailed Spec

#### Step 1: Market & Budget

**Title**: "Where are you looking?"
**Subtitle**: "Set your market, budget, and target cities."

**Fields**:

| Field | Type | Default | Validation |
|-------|------|---------|------------|
| Market | Card selector (1 of N) | Bay Area | Required. Currently only Bay Area available, show "Coming Soon" for Austin, Denver |
| Max Price | Slider | $850,000 | Range: $100k–$3M. Step: $25k. Format: "$850k" or "$1.2M" |
| Down Payment % | Segmented buttons | 20% | Options: 3.5%, 5%, 10%, 15%, 20%, 25% |
| Target Cities | Multi-select pills | None | Required: ≥1 city. Cities loaded from market config. Show "Select All" button |

**Behavior**:
- Market selector loads cities dynamically via `useMarket(marketId)`
- Budget slider updates a live monthly payment estimate below: "~$4,200/mo at 7.25%"
- Down payment buttons highlight PMI warning for <20%: "PMI adds ~$200/mo"
- City pills show count: "(5 selected)"
- "Select All" and "Clear" quick actions

**Visual enhancement**:
- Show a small map thumbnail of the selected market
- Each city pill shows a tiny color dot indicating price tier (green=affordable, amber=mid, red=premium)

**Can proceed when**: ≥1 city selected

**Saves**: `max_price`, `down_payment_pct`, `target_cities`, `market_id`

---

#### Step 2: Strategy

**Title**: "Pick your strategy"
**Subtitle**: "This shapes how we score every property for you."

**Options** (radio-style cards):

| Strategy | Icon | Description | Badge |
|----------|------|-------------|-------|
| House-Hack | Home | "Live in one unit, rent the others. Offset your mortgage." | "Most Popular" |
| Buy & Hold | Repeat | "Long-term rental income and appreciation play." | — |
| Primary Residence | Building | "Finding the perfect home to live in." | — |
| Fix & Flip | Wrench | "Buy undervalued, renovate, sell for profit." | — |

**Behavior**:
- Selecting a strategy shows a brief ROI example in a callout box below:
  - House-Hack: "Example: Buy a 4BR in Oakland for $650k → rent 3 rooms at $1,400/ea → cover 85% of your mortgage from day one."
  - Buy & Hold: "Example: Buy a duplex in Richmond for $550k → rent both units → $400/mo positive cash flow after PITI."
  - Primary: "Example: Find a 3BR in Fremont near BART for $850k → score 80+ on transit, schools, and neighborhood safety."
  - Fix & Flip: "Example: Buy a fixer in El Cerrito for $500k → $80k renovation → sell for $700k → $120k profit before tax."
- Strategy affects scoring weights shown in a mini radar chart preview (8 dimensions adjust)

**Can proceed when**: Strategy selected

**Saves**: `strategy`

---

#### Step 3: Must-Haves

**Title**: "What matters most?"
**Subtitle**: "Select features you care about. We'll boost scores for matches."

**Options** (multi-select grid, 2 cols mobile / 3 cols desktop):

| Must-Have | Icon | Scoring Impact |
|-----------|------|---------------|
| 3+ Bedrooms | Bed | Boosts House-Hack dimension |
| ADU / In-law | Building | Boosts ADU Upside dimension |
| Near Transit | Train | Boosts Transit Access dimension |
| Pool | Bath | Tags properties, no scoring impact |
| Garage | Car | Tags properties, minor neighborhood boost |
| Large Lot | Trees | Boosts Lot Expansion dimension |
| Duplex / Multi-unit | Home | Boosts House-Hack + Rental Income |
| Good Schools | GraduationCap | Boosts Neighborhood dimension |
| Low Crime | ShieldCheck | Boosts Neighborhood dimension |

**New section: Deal-Breakers** (things to filter OUT):
- HOA > $500/mo
- Flood zone
- Age > 50 years
- Busy street / highway adjacent
- Full renovation needed

**Behavior**:
- Each must-have shows a tooltip on hover/tap explaining how it affects scoring
- Selected items get amber ring + filled icon
- Deal-breakers get red ring when selected
- Show count: "4 must-haves, 1 deal-breaker"

**Can proceed when**: Always (step is optional — some users have no strong preferences)

**Saves**: `must_haves`, `deal_breakers`

---

#### Step 4: Alerts

**Title**: "How should we reach you?"
**Subtitle**: "Choose your alert channels and preferred delivery time."

**Channels** (toggle cards):

| Channel | Icon | Description | Setup Required |
|---------|------|-------------|----------------|
| SMS | 💬 | "Text message alerts" | Phone number (via Clerk) |
| WhatsApp | 📱 | "Rich property cards with score breakdowns" | Phone number + WhatsApp opt-in |
| Email | 📧 | "Daily digest with full details" | Auto-enabled (from sign-up email) |

**Alert Time**:
- Time picker for daily digest delivery
- Default: 08:00 AM (market timezone)
- Show timezone label: "Pacific Time"

**Score Threshold** (new addition to this step):
- Slider: 0–100
- Default: 65
- Label: "Only alert me for properties scoring above **65**"
- Color-coded: <50 red zone, 50-64 yellow, 65-79 amber, 80+ green

**Phone number collection**:
- If user enables SMS or WhatsApp and has no phone on file:
  - Show inline phone input + "Verify" button
  - Uses Clerk's phone verification flow (SMS code)
  - On success: phone saved to Clerk, channel enabled
- If phone already on file (from sign-up): show as pre-filled, editable

**Can proceed when**: Always (defaults are reasonable)

**Saves**: `alert_channels`, `alert_time`, `alert_score_threshold`

---

#### Step 5: Preview & Launch (NEW)

**Title**: "Your scout is ready"
**Subtitle**: "Here's a preview of what we found for you."

**Summary card**:
```
┌─────────────────────────────────────────────┐
│  YOUR PROFILE                               │
│                                             │
│  Market:    Bay Area                        │
│  Budget:    Up to $850k (20% down)          │
│  Strategy:  House-Hack                      │
│  Cities:    Oakland, Fremont, El Cerrito    │
│  Must-haves: 3+ bed, Near BART, ADU        │
│  Alerts:    SMS + Email at 8:00 AM          │
│                                             │
│  [Edit Budget] [Edit Strategy] [Edit Alerts]│
└─────────────────────────────────────────────┘
```

**Property preview** (the magic moment):
- Fetch top 3 scored properties matching user's new preferences
- Show them as mini PropertyCards with score rings
- Animate scores filling in (like the hero demo card)
- "We found **47 properties** scored for you. These are your top 3."

**CTA**: "Launch My Scout" (amber button, full width)
- On click:
  1. Save all preferences (final save)
  2. Set `onboarding_complete: true` in Clerk publicMetadata
  3. Fire confetti animation (use `canvas-confetti` package)
  4. Navigate to `/dashboard` after 1.5s delay

**Skip option**: Small text link "Skip for now → Go to Dashboard"
- Skipping does NOT set `onboarding_complete`
- User will see a banner on dashboard prompting them to finish

### 4.4 Progress Persistence

**localStorage** (immediate, offline-capable):
```typescript
const STORAGE_KEY = "hm_onboard_progress";

interface OnboardProgress {
  step: number;
  data: {
    market_id?: string;
    max_price?: number;
    down_payment_pct?: number;
    target_cities?: string[];
    strategy?: string;
    must_haves?: string[];
    deal_breakers?: string[];
    alert_channels?: { sms: boolean; whatsapp: boolean; email: boolean };
    alert_time?: string;
    alert_score_threshold?: number;
  };
  updated_at: string; // ISO timestamp
}
```

**Backend** (on each step transition):
- Call `api.put("/api/profile/preferences", stepData)` if authenticated
- Silent failure — don't block progression if API is down

**Resume logic**:
1. On mount, check localStorage for saved progress
2. If found and `updated_at` < 30 days: restore step + data, resume from saved step
3. If authenticated, also fetch `/api/profile/preferences` and merge (backend wins on conflicts)
4. If `onboarding_complete` is already true in Clerk metadata: redirect to `/dashboard`

### 4.5 Skip & Resume Logic

**Skip onboarding entirely**:
- User closes tab during onboarding → progress saved to localStorage
- User navigates to `/dashboard` directly → allowed (public route)
- Dashboard shows a persistent banner: "Complete your profile to get personalized scores → Finish Setup"
- Banner has a dismiss button (don't show again for 7 days, stored in localStorage)

**Detect incomplete onboarding**:
```tsx
// In dashboard or layout
const { user } = useUser();
const onboardingComplete = user?.publicMetadata?.onboarding_complete === true;

{!onboardingComplete && isSignedIn && (
  <motion.div
    initial={{ y: -40, opacity: 0 }}
    animate={{ y: 0, opacity: 1 }}
    className="bg-amber/10 border-b border-amber/20 px-4 py-2.5 text-sm text-center"
  >
    Your scout isn't fully configured yet.{" "}
    <Link href="/onboard" className="font-semibold text-amber-dark underline">
      Finish setup →
    </Link>
  </motion.div>
)}
```

### 4.6 Activation Metrics

| Event | Trigger | Analytics Key |
|-------|---------|---------------|
| Onboard started | User lands on `/onboard` | `onboard_started` |
| Step 1 completed | Clicks "Continue" from Budget | `onboard_step_1` |
| Step 2 completed | Clicks "Continue" from Strategy | `onboard_step_2` |
| Step 3 completed | Clicks "Continue" from Must-Haves | `onboard_step_3` |
| Step 4 completed | Clicks "Continue" from Alerts | `onboard_step_4` |
| Onboard completed | Clicks "Launch My Scout" | `onboard_complete` |
| Onboard skipped | Clicks "Skip for now" | `onboard_skipped` |
| Onboard abandoned | Started but never completed (>7 days) | `onboard_abandoned` |
| Onboard resumed | Returns to `/onboard` after abandoning | `onboard_resumed` |

**Funnel target**:
```
Visitors → Sign-up: 8%
Sign-up → Step 1: 95%
Step 1 → Step 2: 85%
Step 2 → Step 3: 80%
Step 3 → Step 4: 75%
Step 4 → Launch: 70%
Overall: Sign-up → Complete: ~36%
```

---

## 5. Post-Auth Redirects — The Decision Tree {#5-post-auth-redirects}

```
User signs up (Clerk)
  │
  ├─ NEXT_PUBLIC_CLERK_SIGN_UP_FORCE_REDIRECT_URL = /onboard
  │   → Always goes to onboarding after sign-up
  │
User signs in (Clerk)
  │
  ├─ Has redirect_url query param? (e.g., clicked sign-in from /property/123)
  │   └─ YES → return to that page
  │
  ├─ No redirect_url?
  │   └─ NEXT_PUBLIC_CLERK_SIGN_IN_FALLBACK_REDIRECT_URL = /dashboard
  │       → Goes to dashboard
  │
User has pending session task? (MFA, password reset)
  │
  ├─ reset-password → Clerk handles in <SignIn /> component
  │
  ├─ setup-mfa → taskUrls config routes to /session-tasks/setup-mfa
  │
  └─ Session stays "pending" until task complete
       → <Show when="signed-in"> won't render
       → Protected middleware routes will redirect to /sign-in
```

**Environment variables** (`.env.local`):
```bash
# Clerk keys
NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY=pk_test_...
CLERK_SECRET_KEY=sk_test_...

# Route config
NEXT_PUBLIC_CLERK_SIGN_IN_URL=/sign-in

# Redirect config
NEXT_PUBLIC_CLERK_SIGN_IN_FALLBACK_REDIRECT_URL=/dashboard
NEXT_PUBLIC_CLERK_SIGN_UP_FALLBACK_REDIRECT_URL=/onboard
NEXT_PUBLIC_CLERK_SIGN_UP_FORCE_REDIRECT_URL=/onboard
```

---

## 6. Navbar & Auth UI Components {#6-navbar-auth-ui}

### Current Navbar Auth Section (Desktop)

```tsx
<div className="ml-2 pl-2 border-l border-border/60 flex items-center gap-2">
  <Show when="signed-out">
    <SignInButton mode="modal">
      <button className="...">Sign In</button>
    </SignInButton>
    <SignUpButton mode="modal">
      <button className="... bg-amber text-amber-foreground">Sign Up</button>
    </SignUpButton>
  </Show>
  <Show when="signed-in">
    <UserButton
      appearance={{ elements: { avatarBox: "h-7 w-7" } }}
    />
  </Show>
</div>
```

### Enhancements

**Notification bell** (signed-in users):
```tsx
<Show when="signed-in">
  <NotificationBell count={unreadAlerts} />
  <UserButton
    appearance={{ elements: { avatarBox: "h-7 w-7" } }}
  />
</Show>
```

**Onboarding prompt** (signed-in but onboarding incomplete):
```tsx
<Show when="signed-in">
  {!onboardingComplete && (
    <Link href="/onboard">
      <Button size="sm" variant="outline" className="text-amber-dark border-amber/30">
        Finish Setup
      </Button>
    </Link>
  )}
  <UserButton />
</Show>
```

**UserButton customization**:
```tsx
<UserButton
  appearance={{
    elements: {
      avatarBox: "h-7 w-7",
      userButtonPopoverCard: "shadow-xl border border-border/60",
      userButtonPopoverActionButton: "hover:bg-amber/10",
    },
  }}
  userProfileProps={{
    appearance: {
      elements: {
        formButtonPrimary: "bg-amber hover:bg-amber-dark",
      },
    },
  }}
/>
```

---

## 7. Settings Page — Clerk Integration {#7-settings-clerk}

### Profile Tab

**Data sources**:
| Field | Source | Editable Via |
|-------|--------|-------------|
| Full Name | `clerkUser.firstName` + `clerkUser.lastName` | Clerk `<UserProfile>` or our form → `clerkUser.update()` |
| Email | `clerkUser.emailAddresses[0].emailAddress` | Clerk only (managed, not editable in our UI) |
| Phone | `clerkUser.phoneNumbers[0].phoneNumber` | Clerk phone verification flow |
| Avatar | `clerkUser.imageUrl` | Clerk `<UserButton>` profile modal |
| Market | `clerkUser.publicMetadata.market_id` | Our form → Clerk Backend API |
| Subscription | `clerkUser.publicMetadata.subscription_tier` | Stripe webhook → Clerk Backend API |

**Target cities, strategy, must-haves, alerts**: All stored in our backend (`UserPreferences` table), fetched via `/api/profile/preferences`.

### Subscription Tab

**Tier stored in**: `clerkUser.publicMetadata.subscription_tier`

**Set by**: Stripe webhook handler:
```python
# On successful subscription
import clerk
clerk.users.update(user_id, public_metadata={
    "subscription_tier": "pro",  # or "investor"
    "stripe_customer_id": customer_id,
})
```

**Read by**: Frontend:
```typescript
const tier = (clerkUser?.publicMetadata?.subscription_tier as string) || "free";
```

### Security Tab (NEW — Clerk handles this)

Instead of building custom password change, MFA setup, and session management:
```tsx
import { UserProfile } from "@clerk/nextjs";

// In settings page, add a Security tab:
<TabsContent value="security">
  <UserProfile
    appearance={{
      elements: {
        rootBox: "w-full",
        card: "shadow-none border-0",
        navbar: "hidden", // Hide Clerk's internal nav, we have our own tabs
      },
    }}
  />
</TabsContent>
```

This gives users:
- Password change
- MFA setup (TOTP + SMS)
- Active sessions (with sign-out)
- Connected accounts (Google, Apple, GitHub)
- Delete account

All built by Clerk, zero custom code.

---

## 8. Environment Variables — Complete Reference {#8-env-vars}

```bash
# ═══════════════════════════════════════════════
# Clerk Authentication
# ═══════════════════════════════════════════════

# Required — from Clerk Dashboard → API Keys
NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY=pk_test_...
CLERK_SECRET_KEY=sk_test_...

# Sign-in page route
NEXT_PUBLIC_CLERK_SIGN_IN_URL=/sign-in

# After sign-in: go to dashboard (if no redirect_url in query)
NEXT_PUBLIC_CLERK_SIGN_IN_FALLBACK_REDIRECT_URL=/dashboard

# After sign-up: ALWAYS go to onboarding (force, ignores redirect_url)
NEXT_PUBLIC_CLERK_SIGN_UP_FORCE_REDIRECT_URL=/onboard

# After sign-up: fallback if force isn't set
NEXT_PUBLIC_CLERK_SIGN_UP_FALLBACK_REDIRECT_URL=/onboard

# ═══════════════════════════════════════════════
# Backend API
# ═══════════════════════════════════════════════

NEXT_PUBLIC_API_URL=http://localhost:8000

# ═══════════════════════════════════════════════
# Stripe (Phase 3)
# ═══════════════════════════════════════════════

# NEXT_PUBLIC_STRIPE_PUBLISHABLE_KEY=pk_test_...
# STRIPE_SECRET_KEY=sk_test_...
# STRIPE_WEBHOOK_SECRET=whsec_...

# ═══════════════════════════════════════════════
# Mapbox (Phase 4)
# ═══════════════════════════════════════════════

# NEXT_PUBLIC_MAPBOX_TOKEN=pk.eyJ1...
```

---

## 9. API Layer — Auth Endpoints {#9-api-auth-endpoints}

### Endpoints to Keep (Updated for Clerk)

| Endpoint | Method | Auth | Purpose |
|----------|--------|------|---------|
| `/api/v1/properties` | GET | Public | Property feed |
| `/api/v1/properties/:id` | GET | Public | Property detail |
| `/api/v1/properties/:id/underwrite` | GET | Public | Financial analysis |
| `/api/v1/stats` | GET | Public | Dashboard stats |
| `/api/v1/markets` | GET | Public | Available markets |
| `/api/v1/markets/:id` | GET | Public | Market detail + cities |
| `/api/v1/price-drops` | GET | Public | Recent price drops |
| `/api/profile` | GET | Clerk JWT | User profile + preferences |
| `/api/profile` | PUT | Clerk JWT | Update name, phone |
| `/api/profile/preferences` | PUT | Clerk JWT | Update strategy, budget, cities, alerts |
| `/api/watchlist` | GET | Clerk JWT | Saved properties |
| `/api/watchlist/:property_id` | POST | Clerk JWT | Save property |
| `/api/watchlist/:property_id` | DELETE | Clerk JWT | Remove property |
| `/api/watchlist/:property_id/notes` | PUT | Clerk JWT | Update notes |

### Endpoints to Remove (Replaced by Clerk)

| Old Endpoint | Replacement |
|-------------|-------------|
| `POST /api/auth/signup` | Clerk sign-up (frontend) |
| `POST /api/auth/login` | Clerk sign-in (frontend) |
| `POST /api/auth/refresh` | Clerk session management (automatic) |
| `POST /api/auth/forgot-password` | Clerk password reset |
| `GET /api/auth/me` | `useUser()` on frontend / Clerk JWT claims on backend |

### New Endpoints Needed

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/api/webhooks/clerk` | POST | Clerk webhook handler (user.created, user.updated, user.deleted) |
| `/api/webhooks/stripe` | POST | Stripe webhook handler (subscription events) |
| `/api/profile/onboarding-complete` | POST | Mark onboarding as done (sets Clerk metadata) |

---

## 10. Subscription Tier Gating {#10-tier-gating}

### Frontend Tier Checks

```typescript
// Hook: useTier()
import { useUser } from "@clerk/nextjs";

export function useTier() {
  const { user } = useUser();
  const tier = (user?.publicMetadata?.subscription_tier as string) || "free";
  
  return {
    tier,
    isFree: tier === "free",
    isPro: tier === "pro",
    isInvestor: tier === "investor",
    isPaid: tier === "pro" || tier === "investor",
    canUseMap: tier !== "free",
    canCustomizeWeights: tier === "investor",
    canExportCSV: tier === "investor",
    canUseSMS: tier !== "free",
    canUseWhatsApp: tier !== "free",
    watchlistLimit: tier === "free" ? 10 : tier === "pro" ? 100 : Infinity,
    cityLimit: tier === "free" ? 3 : tier === "pro" ? 10 : Infinity,
  };
}
```

### Upgrade Prompts

**Pattern**: When user hits a tier limit, show contextual upgrade prompt — not a wall.

```tsx
// Example: Free user trying to save 11th watchlist item
function handleSave(propertyId: string) {
  if (!isSignedIn) return;
  
  if (watchlist.length >= watchlistLimit) {
    toast({
      title: "Watchlist is full",
      description: `Free accounts can save up to ${watchlistLimit} properties. Upgrade to Pro for 100.`,
      action: <Link href="/settings?tab=subscription">Upgrade →</Link>,
    });
    return;
  }
  
  addToWatchlist.mutate({ property_id: propertyId });
}
```

---

## 11. Security & Edge Cases {#11-security}

### Auth Edge Cases

| Scenario | Handling |
|----------|---------|
| User refreshes during onboarding | localStorage restores progress + step |
| User signs up on mobile, continues on desktop | Backend preferences sync on mount |
| Clerk session expires mid-use | `useAuth()` returns `isSignedIn: false`, UI updates reactively |
| User deletes Clerk account | Webhook fires `user.deleted` → soft-delete our User + preferences |
| OAuth user has no email | Clerk requires email — won't happen |
| Rate limiting on sign-up | Clerk handles (bot protection, 429 responses) |
| Concurrent sessions | Clerk supports multi-device. Preferences last-write-wins. |
| Token replay attack | Clerk JWTs are short-lived (60s default). JWKS rotation handled by Clerk. |

### Security Best Practices

1. **Never store Clerk tokens in localStorage** — Clerk uses httpOnly cookies automatically
2. **Never expose `CLERK_SECRET_KEY` to the client** — it's server-only
3. **Validate JWTs on every backend request** — don't trust client-side `isSignedIn`
4. **Use Clerk webhooks for critical state changes** — don't rely on client API calls for subscription tier changes
5. **Rate-limit our API endpoints independently** — Clerk protects auth, but our `/api/properties` needs its own rate limiting
6. **Sanitize all user input** — Clerk handles auth input, but our preferences fields (city names, notes) need XSS protection

---

## 12. Implementation Checklist {#12-implementation-checklist}

### Phase A: Clerk Cleanup (Now) ✅ Mostly Done

- [x] Install `@clerk/nextjs`
- [x] Add `ClerkProvider` to root layout
- [x] Create `clerkMiddleware()` in `middleware.ts`
- [x] Create `/sign-in/[[...sign-in]]/page.tsx`
- [x] Replace navbar auth with Clerk components (`Show`, `SignInButton`, `SignUpButton`, `UserButton`)
- [x] Replace `useAuthStore` with `useAuth()` / `useUser()` across all pages
- [x] Redirect old `/login`, `/signup`, `/forgot-password` to `/sign-in`
- [x] Set env vars: publishable key, secret key, redirect URLs
- [x] Remove `useAuthStore` dependency from settings page
- [ ] Delete old auth layout (`src/app/(auth)/layout.tsx`) — no longer needed
- [ ] Clean up `stores.ts` — remove `useAuthStore` entirely (keep `useUIStore`)
- [ ] Clean up `api.ts` — remove `setTokens`, `clearTokens`, `getAccessToken`, `refreshAccessToken`

### Phase B: Token Bridge (Next)

- [ ] Update `api.ts` to use Clerk's `getToken()` instead of localStorage tokens
- [ ] Create `useApiAuth` hook to wire Clerk session tokens into API client
- [ ] Update backend auth to validate Clerk JWTs (JWKS)
- [ ] Add `clerk_id` column to User model, migrate existing users
- [ ] Set up Clerk webhook endpoint (`/api/webhooks/clerk`)
- [ ] Auto-create User record on first authenticated API call

### Phase C: Onboarding Enhancement

- [ ] Add localStorage persistence for onboarding progress
- [ ] Add Step 5: Preview & Launch (summary card + 3 property preview)
- [ ] Add confetti animation on launch
- [ ] Set `onboarding_complete` in Clerk publicMetadata
- [ ] Add "Finish Setup" banner on dashboard for incomplete onboarding
- [ ] Add deal-breakers sub-section to Step 3
- [ ] Add score threshold slider to Step 4 (Alerts)
- [ ] Add phone verification flow in Step 4 when SMS/WhatsApp enabled

### Phase D: Branding & Polish

- [ ] Style Clerk `<SignIn />` component with HouseMatch branding (appearance prop)
- [ ] Style `<UserButton>` dropdown to match design system
- [ ] Add Security tab to Settings using Clerk's `<UserProfile>`
- [ ] Configure Clerk Dashboard: enable Google OAuth, bot protection, email templates
- [ ] Customize Clerk email templates (verification, password reset) with HouseMatch branding

### Phase E: Subscription Integration

- [ ] Implement `useTier()` hook reading from Clerk publicMetadata
- [ ] Gate features by tier (map view, custom weights, CSV export, SMS)
- [ ] Set up Stripe Checkout for upgrade flow
- [ ] Stripe webhook → update `subscription_tier` in Clerk publicMetadata
- [ ] Add upgrade prompts at tier boundaries
- [ ] Add 14-day Pro trial for new sign-ups

---

*This spec is the single source of truth for HouseMatch authentication and onboarding. Every auth decision references this document. Update it as features ship.*

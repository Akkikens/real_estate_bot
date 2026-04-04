# HouseMatch — Product & Frontend Specification

> **Version**: 1.0  
> **Date**: 2026-04-03  
> **Status**: Implementation-ready  
> **Goal**: Build HouseMatch into a globally scalable property intelligence platform for house-hackers and first-time investors.

---

## Table of Contents

1. [Vision & Market Opportunity](#1-vision--market-opportunity)
2. [Architecture Overview](#2-architecture-overview)
3. [API Layer (FastAPI)](#3-api-layer-fastapi)
4. [Authentication & Multi-Tenancy](#4-authentication--multi-tenancy)
5. [Pages & Features — Detailed Spec](#5-pages--features--detailed-spec)
   - 5.1 Landing / Marketing
   - 5.2 Auth (Sign Up / Login / OAuth)
   - 5.3 Onboarding Wizard
   - 5.4 Dashboard (Property Feed)
   - 5.5 Property Detail
   - 5.6 Watchlist
   - 5.7 Underwriting Calculator
   - 5.8 Agent Outreach / CRM
   - 5.9 Reports & Analytics
   - 5.10 Settings & Subscription
   - 5.11 Admin Panel
   - 5.12 Market Selector
6. [Component Library](#6-component-library)
7. [State Management & Data Layer](#7-state-management--data-layer)
8. [Real-Time Features](#8-real-time-features)
9. [Mobile Strategy](#9-mobile-strategy)
10. [Internationalization & Multi-Market](#10-internationalization--multi-market)
11. [Monetization & Subscription Tiers](#11-monetization--subscription-tiers)
12. [SEO & Growth](#12-seo--growth)
13. [Performance & Infrastructure](#13-performance--infrastructure)
14. [Analytics & Metrics](#14-analytics--metrics)
15. [Implementation Phases](#15-implementation-phases)

---

## 1. Vision & Market Opportunity

### The Problem

First-time buyers and small investors waste 10–20 hours/week scrolling Redfin, Zillow, and Craigslist. They manually evaluate each listing against their strategy (house-hack? ADU? rental income?) with no systematic framework. Most miss the best deals because they can't process 200+ new listings daily.

### The Solution

HouseMatch scores every property 0–100 against the user's personal strategy, budget, and must-haves — then delivers the top picks daily via WhatsApp, SMS, or the app. It's a **personal property analyst** that never sleeps.

### Why This Can Be a $100M+ Business

| Lever | Opportunity |
|-------|-------------|
| **TAM** | 6.5M homes sold/year in US alone. 40% are first-time buyers (2.6M). Each spends 4+ months searching. |
| **Willingness to pay** | Buyers spend $400k–$2M on a home. $19–49/mo for intelligence is a rounding error. |
| **Network effects** | More users → better comp data → better scoring → more users. Agent referral marketplace creates two-sided network. |
| **Multi-market expansion** | Market config system already abstracted. Bay Area → Austin → Denver → London → Mumbai. |
| **Revenue stacking** | Subscriptions + agent referrals ($500–2k/deal) + lender referrals ($50–200/lead) + data licensing. |

### Competitive Moat

1. **Strategy-first scoring** — Nobody else scores against house-hack/ADU/rental income strategy.
2. **Multi-source aggregation** — Redfin + Zillow + Realtor + Craigslist + FSBO. No single-source blind spots.
3. **Financial underwriting built-in** — PITI, house-hack scenarios, appreciation projections, room rental modeling.
4. **Market-aware intelligence** — BART distance, neighborhood safety, grocery walkability, school ratings — not just beds/baths/price.
5. **CRM + outreach** — Draft agent emails, track responses, follow-up reminders. Full deal pipeline.

---

## 2. Architecture Overview

```
┌─────────────────────────────────────────────────────────────────────┐
│                        FRONTEND (Next.js 16)                        │
│  Landing · Auth · Onboard · Dashboard · Detail · Watchlist · CRM   │
│  Underwriting · Reports · Settings · Admin · Market Selector        │
└────────────────────────────┬────────────────────────────────────────┘
                             │ REST + WebSocket
┌────────────────────────────▼────────────────────────────────────────┐
│                        API LAYER (FastAPI)                           │
│  /auth · /profile · /properties · /scores · /watchlist              │
│  /underwrite · /outreach · /alerts · /reports · /admin · /markets   │
│  /stripe (webhooks) · /ws (real-time)                               │
└────────────────────────────┬────────────────────────────────────────┘
                             │
┌────────────────────────────▼────────────────────────────────────────┐
│                     BACKEND (Python Engine)                          │
│  Ingestion → Normalize → Sanity → Enrich → Score → Alert           │
│  Underwriting · CRM · Reports · Market Config                       │
└────────────────────────────┬────────────────────────────────────────┘
                             │
┌────────────────────────────▼────────────────────────────────────────┐
│                     DATA (PostgreSQL + Redis)                        │
│  Property · PriceHistory · Underwriting · Alert · User · Subscription│
│  OutreachRecord · PropertyAnomaly · WatchlistItem · UserPreferences  │
└─────────────────────────────────────────────────────────────────────┘
```

### New Database Tables Needed

```
User
  id, email, phone, name, password_hash, avatar_url
  market_id, created_at, last_login_at
  stripe_customer_id, subscription_tier (free/pro/investor)

UserPreferences
  user_id (FK), max_price, down_payment_pct, target_cities (JSON)
  strategy (house_hack/buy_hold/primary/fix_flip)
  must_haves (JSON array), scoring_weight_overrides (JSON)
  alert_channels (JSON: {sms, whatsapp, email})
  alert_time, rental_alert_time, timezone

WatchlistItem
  user_id (FK), property_id (FK), saved_at
  price_at_save, notes

UserPropertyView
  user_id, property_id, viewed_at, duration_seconds
  (for recommendation engine)
```

---

## 3. API Layer (FastAPI)

Every frontend page maps to API endpoints. All responses paginated, cached in Redis.

### Auth Endpoints

```
POST   /api/auth/signup          — email + password + phone
POST   /api/auth/login           — returns JWT (access + refresh)
POST   /api/auth/refresh         — refresh token rotation
POST   /api/auth/forgot-password — sends reset link
POST   /api/auth/reset-password  — with token
GET    /api/auth/me              — current user profile
POST   /api/auth/oauth/google    — Google OAuth callback
POST   /api/auth/oauth/apple     — Apple Sign-In callback
```

### Profile & Preferences

```
GET    /api/profile              — user profile + preferences
PUT    /api/profile              — update name, email, phone, avatar
PUT    /api/profile/preferences  — update strategy, budget, cities, must-haves, alerts
GET    /api/profile/usage        — API usage, alerts sent this month, watchlist count
```

### Properties

```
GET    /api/properties                    — paginated feed, sorted by score
  ?page=1&limit=20
  &min_score=65&max_price=850000
  &cities=Oakland,Fremont
  &tags=adu,near_bart
  &sort=score|price|newest|price_drop
  &listing_type=sale|rental
GET    /api/properties/:id                — full detail + score breakdown
GET    /api/properties/:id/score          — 8-dimension breakdown with explanations
GET    /api/properties/:id/underwriting   — financial scenarios
GET    /api/properties/:id/price-history  — price change timeline
GET    /api/properties/:id/similar        — 5 similar properties by dimensions
POST   /api/properties/:id/view           — track user viewed (for recommendations)
```

### Watchlist

```
GET    /api/watchlist                     — user's saved properties with price deltas
POST   /api/watchlist/:property_id        — save to watchlist
DELETE /api/watchlist/:property_id        — remove from watchlist
PUT    /api/watchlist/:property_id/notes  — add/update notes on saved property
```

### Outreach / CRM

```
GET    /api/outreach                      — all outreach records for user
POST   /api/outreach/draft                — generate draft email for property
PUT    /api/outreach/:id/approve          — approve draft for sending
PUT    /api/outreach/:id/send             — send approved outreach
PUT    /api/outreach/:id/reply            — record agent reply + sentiment
GET    /api/outreach/follow-ups           — due follow-ups
```

### Alerts & Notifications

```
GET    /api/alerts                        — alert history (sent, pending, errors)
PUT    /api/alerts/preferences            — update channels + times
POST   /api/alerts/test                   — send test alert to verify setup
```

### Reports

```
GET    /api/reports/daily                 — today's daily digest
GET    /api/reports/weekly                — weekly summary with trends
GET    /api/reports/market-pulse          — market stats (avg price, inventory, DOM)
GET    /api/reports/export/csv            — CSV download (Investor tier)
```

### Subscriptions (Stripe)

```
POST   /api/stripe/create-checkout       — create Stripe Checkout session
POST   /api/stripe/create-portal         — Stripe Customer Portal for manage/cancel
POST   /api/stripe/webhook               — handle subscription events
GET    /api/subscription                  — current plan + usage + limits
```

### Markets

```
GET    /api/markets                       — available markets with metadata
GET    /api/markets/:id                   — market detail (cities, transit, config)
```

### Admin

```
GET    /api/admin/users                   — user list with subscription info
GET    /api/admin/pipeline/status         — ingestion pipeline health
POST   /api/admin/pipeline/trigger        — manually trigger pipeline run
GET    /api/admin/anomalies               — rejected listings audit trail
GET    /api/admin/metrics                 — KPIs dashboard data
```

---

## 4. Authentication & Multi-Tenancy

### Auth Flow

```
Landing → Sign Up (email/Google/Apple) → Onboarding Wizard → Dashboard
                                           ↕
                                     Returning users → Login → Dashboard
```

### Implementation

- **NextAuth.js** (Auth.js v5) for frontend session management
- **JWT tokens** (access: 15min, refresh: 7 days) for API auth
- **Google OAuth** + **Apple Sign-In** for frictionless signup
- **Phone verification** via Twilio Verify (for SMS/WhatsApp channel activation)

### Multi-Tenancy

Every query filters by `user_id`. Properties are shared (read-only), but:
- Scores are computed per-user (based on their preferences)
- Watchlist, outreach, alerts are per-user
- Subscription tier gates feature access

### Rate Limits by Tier

| Resource | Free | Pro | Investor |
|----------|------|-----|----------|
| Property views/day | 50 | Unlimited | Unlimited |
| Watchlist items | 10 | 100 | Unlimited |
| Alerts/day | 1 digest | 3 digests + instant | Unlimited |
| API calls/day | — | — | 1,000 |
| CSV exports/month | — | — | 10 |

---

## 5. Pages & Features — Detailed Spec

### 5.1 Landing Page (`/`)

**Purpose**: Convert visitors to sign-ups. SEO-optimized, fast, no auth required.

**Sections** (scroll order):

1. **Hero**
   - Headline: "Your AI Property Scout" (Playfair Display, 72px)
   - Subhead: "Stop scrolling. Start scoring. Get personalized property picks delivered daily."
   - CTA: "Get Started Free" (amber) + "Watch Demo" (outline, opens modal with Loom/YouTube embed)
   - Floating demo card showing a real scored property (animated score ring filling to 87)
   - Blueprint grid background with grain texture

2. **Social Proof Bar**
   - "Trusted by 2,400+ Bay Area buyers" (counter animates on scroll)
   - Logos: "As featured in" placeholder for future press
   - Star rating: "4.9/5 from 340 reviews"

3. **How It Works** (3-step horizontal)
   - Step 1: "Tell us your strategy" — illustration of onboarding
   - Step 2: "We score every listing" — score ring animation
   - Step 3: "Top picks delivered daily" — phone mockup with WhatsApp message

4. **Feature Grid** (6 cards, current implementation is good)
   - AI Scoring, Daily Alerts, Market Focus, House-Hack Ready, Multi-Source, Watchlist

5. **Live Demo Section** (NEW)
   - Interactive: visitor can pick a city + strategy → shows 3 sample scored properties
   - No signup required — taste of the product
   - Upsell: "Sign up to see all 47 properties scored for Oakland today"

6. **Score Breakdown Preview** (NEW)
   - Show the 8 dimensions with example bars
   - Explain what each means in plain English
   - "Most sites show you beds and baths. We show you if you can retire on this property."

7. **Testimonials** (current 3 + expand to 6 with photos)

8. **Pricing** (current 3 tiers — update to match backend tier structure)

9. **FAQ Accordion** (NEW)
   - "How do you score properties?"
   - "What markets do you cover?"
   - "Can I customize scoring weights?"
   - "How do alerts work?"
   - "Is my data safe?"
   - "Can I cancel anytime?"

10. **Final CTA**
    - "Find your first deal this week" + email input + "Start Free" button
    - Below: "No credit card required. Cancel anytime."

11. **Footer**
    - Links: About, Blog, Pricing, Contact, Privacy, Terms
    - Social: Twitter/X, LinkedIn, Instagram
    - Market badges: "Now available in Bay Area, Austin, Denver"

**Tech notes**:
- Server Component (no "use client") for SEO — only interactive sections use client islands
- Structured data (JSON-LD) for SaaS schema
- Open Graph + Twitter cards with custom preview image
- Lighthouse target: 95+ performance, 100 accessibility

---

### 5.2 Auth Pages (`/login`, `/signup`, `/forgot-password`)

**Sign Up** (`/signup`)
- Fields: Full name, Email, Password (strength meter), Phone (optional)
- OAuth buttons: "Continue with Google" / "Continue with Apple"
- On submit → create account → redirect to `/onboard`
- Phone field shows: "Add phone to enable SMS/WhatsApp alerts"
- Password requirements shown inline (8+ chars, 1 uppercase, 1 number)

**Login** (`/login`)
- Email + Password
- "Remember me" checkbox
- "Forgot password?" link
- OAuth buttons
- On submit → redirect to `/dashboard`
- Failed attempts: show error, lock after 5 attempts for 15min

**Forgot Password** (`/forgot-password`)
- Email input → sends reset link
- Success state: "Check your inbox" with countdown timer for resend

**Design**: Clean centered card, grain background, logo at top. No navbar — standalone flow.

---

### 5.3 Onboarding Wizard (`/onboard`)

**Purpose**: Capture user preferences to personalize scoring. Critical for activation.

**Step 1: Market & Budget**
- Market selector: dropdown or card grid (Bay Area, Austin, Denver... more coming)
- When market selected: show map of that market with cities highlighted
- Max price: slider ($100k–$5M, step $25k) with formatted display
- Down payment: segmented buttons (3.5%, 5%, 10%, 15%, 20%, 25%, Custom)
- Target cities: multi-select pills, grouped by market. Show avg price + listing count per city
- "Select All" / "Clear" buttons

**Step 2: Strategy**
- 4 cards (current design is good), add:
  - Estimated monthly numbers preview per strategy
  - "Most popular" badge on House-Hack
  - Brief ROI example: "House-hack a 4BR in Oakland → rent 3 rooms at $1,400/ea → cover 85% of your mortgage"

**Step 3: Must-Haves & Deal-Breakers** (SPLIT into two sub-sections)
- **Must-haves** (boost score): 3+ beds, ADU/in-law, near transit, garage, large lot, duplex, good schools, low crime, pool, new construction, single story, corner lot
- **Deal-breakers** (filter out): flood zone, HOA > $X, no garage, busy street, fixer-upper, age > X years
- Each item: icon + label + optional tooltip explaining scoring impact
- Drag-to-reorder for priority (nice-to-have)

**Step 4: Scoring Weights** (NEW — Pro/Investor only)
- Show the 8 dimensions as sliders (default weights from YAML)
- Visual: radar chart that updates in real-time as user adjusts weights
- Presets: "Balanced", "Cash Flow Focused", "Appreciation Play", "Transit-First"
- Free users see this step but it's locked: "Upgrade to Pro to customize"

**Step 5: Alerts**
- Channels: SMS, WhatsApp, Email — each with setup flow
  - SMS: enter phone → verify via Twilio Verify code
  - WhatsApp: show QR code / link to send join message
  - Email: auto-enabled from signup
- Delivery time: time picker for each alert type (sale digest, rental digest)
- Frequency: "Daily digest" (default) / "Instant" (Pro+) / "Weekly summary"
- Score threshold slider: "Only alert me for properties scoring above ___" (65 default)

**Step 6: Confirmation**
- Summary card showing all selections
- "Edit" links per section
- "Launch My Scout" CTA → redirect to `/dashboard`
- Confetti animation on launch

**Tech notes**:
- Save progress to localStorage between steps (resume if user leaves)
- Save to API on each step completion (not just at end)
- Show completion % in navbar during onboarding
- If user visits `/dashboard` before completing onboard, show modal to finish

---

### 5.4 Dashboard — Property Feed (`/dashboard`)

**Purpose**: The daily home screen. Show the best properties, let users browse and filter.

**Layout**: Full-width with sidebar filters on desktop, sheet/drawer on mobile.

**Header Bar**
- "Your Feed" title + market badge (e.g., "Bay Area")
- "Last updated 2 hours ago" + manual refresh button
- View toggle: Grid (cards) / List (compact rows) / Map
- Sort dropdown: Score (default), Price ↑↓, Newest, Biggest Price Drop, BART Distance

**Filters Sidebar** (desktop: left sidebar, mobile: bottom sheet)
- Score range slider (0–100)
- Price range slider (uses user's max as ceiling)
- Beds: 1+ / 2+ / 3+ / 4+ / 5+
- Baths: 1+ / 2+ / 3+
- Cities: checkboxes (from user's target cities)
- Property type: SFR, Duplex/Multi, Condo/TH
- Tags: ADU, Near BART, Large Lot, Price Reduced, New Listing, Open House
- Listing type: For Sale / For Rent / Both
- Quick filters (pill row above grid): "Excellent 80+", "Good 65+", "House Hack", "ADU Potential", "Price Drops"
- "Reset filters" + "Save this search" (Pro+)

**Property Cards** (Grid View)
- **Current implementation + enhancements**:
  - Property photo (placeholder/gradient if no image — scrape from listing URL later)
  - Score ring (top-right)
  - Address, City, Price (bold, large)
  - Stats row: beds, baths, sqft, lot size, BART distance
  - Tags (amber pills)
  - Price change indicator if applicable (↓$26k in green, ↑ in red)
  - Days on market badge (< 7 days = "New" badge, > 60 = "Stale" badge)
  - Footer: Save button, Listing link, Details arrow
  - Hover: slight lift + border glow

**Property Cards** (List View — NEW)
- Compact single-row: Score | Address | City | Price | Beds | Baths | Sqft | BART | Tags | Actions
- Sortable columns
- Checkbox multi-select for bulk actions (save all, export)

**Map View** (NEW — Pro+)
- Mapbox GL JS or Google Maps embed
- Pins colored by score (green/amber/yellow/red)
- Click pin → popup card with quick stats + score
- Draw polygon to filter area
- Transit overlay: show BART lines + station markers
- Cluster markers when zoomed out

**Infinite Scroll / Pagination**
- Load 20 properties at a time
- Skeleton loading cards while fetching
- "End of results" message with "Broaden your filters" CTA

**Empty States**
- No results: "No properties match your filters. Try expanding your search."
- New user (no preferences): "Complete your profile to see personalized scores." → link to onboard
- Pipeline hasn't run yet: "We're gathering listings for your market. Check back in a few hours."

**Real-Time Updates**
- WebSocket: when pipeline finishes, toast notification: "12 new properties scored. Refresh to see them."
- Badge on navbar: red dot on Dashboard icon when new properties available

---

### 5.5 Property Detail (`/property/:id`)

**Purpose**: Deep dive into a single property. The place where users decide to save, contact agent, or skip.

**Hero Section**
- Photo gallery (carousel if multiple images available, placeholder if not)
- Breadcrumb: Dashboard → Oakland → 1247 Elm St
- Address, City, State, Zip
- Price (large) + price history sparkline (inline mini chart)
- Score ring (large, 90px) + rating badge
- Tags row
- Quick actions: Save to Watchlist, Share (copy link), View Listing (external)

**Key Stats Grid** (2 rows × 4 cols)
Row 1: Price, Beds/Baths, Sqft, Lot Size
Row 2: Year Built, $/Sqft, Days on Market, BART Distance (with station name)

**Score Breakdown** (Primary section)
- Full 8-dimension bar chart (current ScoreBars component)
- Each dimension expandable: click to see explanation text
  - e.g., "Price Fit: 8.5/10 — This property is at 82% of your max budget ($789k vs $950k max), leaving room for negotiation."
  - e.g., "Transit: 9.0/10 — 0.8 miles from Fremont BART. Oakland/SF commute bonus applied."
- Radar chart visualization (alternative view toggle)
- Overall confidence indicator: "Scored with 87% data confidence (6/8 dimensions had real data)"

**Financial Underwriting** (NEW — from calculator.py)
- **Monthly Cost Breakdown** (stacked bar chart):
  - Principal + Interest
  - Property Tax
  - Insurance
  - PMI (if applicable)
  - HOA (if applicable)
  - Maintenance reserve
  - = Total PITI
- **Scenario Cards** (side-by-side):
  - Owner-Occupant: "You'd pay $4,200/mo out of pocket"
  - House-Hack: "Rent 3 rooms at $1,400/ea → net cost $0/mo" (highlight if positive cash flow)
  - Full Rental: "Potential rental income $3,800/mo → cash flow +$200/mo"
  - Room Rental: Low/Mid/High scenarios with slider
- **Cash to Close**: Down payment + closing costs + reserves = total
- **5-Year Equity Projection** (line chart):
  - 3 lines: conservative (2%), moderate (4%), optimistic (6%)
  - Shows total equity gained (appreciation + principal paydown)
- **Verdict Badge**: "Good First Property" ✅ or "Review Carefully" ⚠️ with explanation
- **Editable Assumptions**: inline edit mortgage rate, down payment, rent estimates → recalculates live

**Listing Remarks**
- Full text from MLS/source
- Highlighted keywords: ADU-related terms in amber, risk terms in red, deal terms in green
- "AI Summary" (future): GPT-generated 2-sentence plain-English summary

**Location**
- Map (Mapbox/Google) centered on property
- Nearby markers: BART stations, schools, grocery stores
- Walk/transit/bike scores (when available)
- Neighborhood name + safety score bar

**Similar Properties** (NEW)
- "You might also like" — 3–5 cards of similar-scored properties in same city/price range
- Dimension comparison table: side-by-side scores

**Agent Outreach** (inline CRM)
- Agent name + brokerage (from listing)
- "Draft Inquiry" button → opens modal with pre-filled email template
- Template selector: Initial Inquiry, ADU Questions, Disclosure Request
- Edit body → Approve → Send (or save as draft)
- If outreach exists: show status (draft/sent/replied) + reply content

**Activity Timeline** (NEW)
- Chronological feed: "Listed Apr 1 at $815k" → "Price reduced Apr 3 to $789k" → "You saved this property" → "Inquiry sent to agent"

---

### 5.6 Watchlist (`/watchlist`)

**Purpose**: Track saved properties, monitor price changes, manage deal pipeline.

**Views**: List (default) / Board (Kanban)

**List View** (current + enhancements)
- Each item shows: score, address, city, price, price change (delta + %), beds, baths, BART
- Tags + saved date
- User notes (editable inline)
- Quick actions: Remove, View Detail, Open Listing
- Sort: Score, Price, Date Saved, Biggest Price Drop
- Filter: Cities, Score Range

**Board View** (NEW — Kanban-style)
- Columns: "Watching" → "Touring" → "Offer Sent" → "Under Contract" → "Closed" / "Passed"
- Drag cards between columns
- Each column shows count + total value
- Great for tracking actual deal pipeline

**Price Alerts**
- Red/green indicators for price changes since save
- Daily delta: "$-26,000 (−3.2%) since you saved"
- Sparkline mini-chart showing price history
- "This property has dropped $41k in 2 weeks — consider making an offer" (smart nudge)

**Bulk Actions**
- Multi-select checkbox
- "Export Selected" (CSV — Investor tier)
- "Remove Selected"
- "Draft Outreach for Selected" (batch email drafts)

**Empty State**: Illustrated graphic + "Start saving properties from your feed" CTA

---

### 5.7 Underwriting Calculator (`/calculator`) — NEW

**Purpose**: Standalone financial calculator (not tied to a specific property). Let users model scenarios.

**Input Panel**
- Purchase price
- Down payment (% or $)
- Mortgage rate (default from market config)
- Property tax rate (default from market, editable)
- Insurance, HOA, maintenance
- Estimated rent (full property or per-room)
- Number of rentable rooms

**Output Panel** (live-updating as inputs change)
- Monthly PITI breakdown (stacked bar)
- Cash to close
- All 5 scenarios: owner-occupant, house-hack, full rental, room rental low/mid/high
- Break-even analysis: "You need to rent at $X/room to break even"
- 5-year equity chart

**Presets**: "Use Bay Area defaults" / "Load from property" (paste a property ID)

**Share**: Generate shareable link with pre-filled inputs

---

### 5.8 Agent Outreach / CRM (`/outreach`) — NEW

**Purpose**: Manage all agent communications in one place.

**Outreach Inbox**
- Table: Property | Agent | Status (Draft/Sent/Replied) | Last Activity | Actions
- Filter by status
- Click to expand: full email thread

**Compose**
- Template picker: Initial Inquiry, Follow-up, Disclosure Request, ADU Questions, Custom
- Property context auto-filled (address, price, questions based on scoring gaps)
- Rich text editor
- "Preview" / "Save Draft" / "Send"
- Schedule send: "Send tomorrow at 9am"

**Follow-Up Reminders**
- Dashboard widget: "3 follow-ups due today"
- Auto-suggest: "No reply from agent on 1247 Elm St after 6 days. Send follow-up?"

**Analytics**
- Response rate by template type
- Average reply time
- Sentiment breakdown (positive/neutral/negative)

---

### 5.9 Reports & Analytics (`/reports`) — NEW

**Purpose**: Market intelligence and personal performance tracking.

**Daily Digest** (mirror of SMS/WhatsApp alert)
- Top 10 properties today
- Price drops in the last 24h
- New listings matching your criteria
- "Your market pulse": avg price, inventory count, DOM trend

**Weekly Summary**
- Properties scored this week
- Your engagement: properties viewed, saved, outreach sent
- Score distribution chart (how many excellent/good/watch/skip)
- Top improving properties (score went up due to price drops or new data)

**Market Pulse** (NEW)
- City-by-city stats: median price, inventory, avg DOM, price trend (30d/90d)
- Chart: inventory trend over time
- Chart: median price by city (bar chart)
- "Buyer's market" vs "Seller's market" indicator per city

**Portfolio View** (Investor tier)
- If user has purchased properties, track actual ROI
- Rental income tracking
- Equity tracker
- Net worth impact

---

### 5.10 Settings & Subscription (`/settings`)

**Tabs**: Profile, Preferences, Notifications, Subscription, Security

**Profile**
- Name, email, phone, avatar upload
- Market selector (change market)
- Target cities (market-aware list)
- Timezone

**Preferences**
- Strategy picker (can change anytime, rescores all properties)
- Budget: max price, down payment
- Must-haves and deal-breakers (same as onboard step 3)
- Scoring weights (Pro+): 8 sliders + radar chart preview

**Notifications**
- Channel toggles: SMS, WhatsApp, Email
- Per-channel setup:
  - SMS: verify phone number
  - WhatsApp: show sandbox join instructions (or production QR)
  - Email: verified by default from signup
- Alert schedule: sale digest time, rental digest time
- Score threshold: "Only alert me above ___"
- Alert types: new matches, price drops, status changes, follow-up reminders

**Subscription**
- Current plan card with features
- "Upgrade" / "Downgrade" buttons
- Usage this month: alerts sent, properties viewed, watchlist count
- Billing history (via Stripe Customer Portal)
- "Cancel Subscription" with retention flow: "Before you go, here's what you'd lose..."

**Security**
- Change password
- Two-factor authentication (TOTP)
- Active sessions (with logout option)
- Delete account (with confirmation + data export)

---

### 5.11 Admin Panel (`/admin`) — Internal

**Purpose**: Monitor platform health and manage users. Not customer-facing.

**Sections**:
- **Pipeline Health**: last run time, properties ingested, errors, anomalies
- **User Management**: user list, subscription tiers, engagement metrics
- **Anomaly Audit**: rejected listings with reason codes (from PropertyAnomaly table)
- **Market Config**: view/edit market configs (eventually a UI for adding new markets)
- **Feature Flags**: enable/disable features per tier or globally
- **Revenue**: MRR, churn, conversion rates (from Stripe data)

---

### 5.12 Market Selector (Global — accessible from navbar/settings)

**Purpose**: Let users switch between markets or see which markets are available.

**Available Markets** (Phase 1–3)
- Bay Area (launched)
- Austin, TX
- Denver, CO
- (each shows: # cities, # active listings, "Available" / "Coming Soon" / "Beta")

**Market Preview** (for "Coming Soon")
- "Join waitlist for [Market Name]"
- Email capture + city preference
- "We'll notify you when we launch"

---

## 6. Component Library

### Existing Components (keep)
| Component | Status | Notes |
|-----------|--------|-------|
| `ScoreRing` | ✅ Good | Add size="sm" (32px) variant for list views |
| `ScoreBars` | ✅ Good | Add expandable explanations per bar |
| `PropertyCard` | ✅ Good | Add image slot, price change, DOM badge |
| `Navbar` | ✅ Good | Add user avatar, notification bell, market badge |

### New Components Needed

| Component | Purpose |
|-----------|---------|
| `PropertyListRow` | Compact row for list view (sortable table row) |
| `PropertyMap` | Mapbox GL integration with score-colored pins |
| `MapPopupCard` | Mini property card inside map popup |
| `UnderwritingPanel` | Full financial breakdown with editable inputs |
| `ScenarioCard` | Single financial scenario (owner/house-hack/rental) |
| `EquityChart` | 5-year appreciation line chart (3 scenarios) |
| `RadarChart` | 8-axis radar for score dimensions |
| `PriceSparkline` | Inline mini price history chart |
| `TimelineEvent` | Single event in activity timeline |
| `KanbanBoard` | Drag-and-drop columns for watchlist pipeline |
| `KanbanCard` | Draggable property card for board view |
| `FilterSidebar` | Collapsible filter panel with range sliders |
| `FilterSheet` | Mobile bottom sheet version of filters |
| `EmptyState` | Reusable illustrated empty state with CTA |
| `SkeletonCard` | Loading placeholder matching PropertyCard dimensions |
| `AlertBanner` | Toast/banner for real-time notifications |
| `TemplateEditor` | Rich text editor for outreach emails |
| `StepIndicator` | Onboarding progress bar (current, enhanced) |
| `MarketCard` | Market selector card with stats |
| `PricingCard` | Enhanced pricing tier card |
| `FAQAccordion` | Expandable FAQ items |
| `DemoWidget` | Interactive live demo on landing page |
| `PhotoGallery` | Image carousel for property detail |
| `UserAvatar` | Avatar with fallback initials |
| `NotificationBell` | Navbar bell with unread count badge |
| `SearchCommand` | Cmd+K command palette for quick navigation |

### Chart Library

Use **Recharts** (lightweight, React-native) for:
- Stacked bar (PITI breakdown)
- Line chart (equity projection, price history)
- Radar chart (score dimensions)
- Bar chart (market stats by city)
- Sparklines (inline price trends)

---

## 7. State Management & Data Layer

### Stack

| Concern | Tool |
|---------|------|
| Server state | **TanStack Query (React Query)** — caching, background refetching, pagination |
| Client state | **Zustand** — lightweight, no boilerplate. Stores: user, filters, UI state |
| Forms | **React Hook Form** + **Zod** — validation, controlled inputs |
| URL state | **nuqs** — sync filters to URL params (shareable filter states) |

### Key Stores (Zustand)

```typescript
// User store
interface UserStore {
  user: User | null
  preferences: UserPreferences | null
  subscription: SubscriptionTier
  setUser, logout, updatePreferences
}

// UI store
interface UIStore {
  sidebarOpen: boolean
  viewMode: 'grid' | 'list' | 'map'
  filterSheetOpen: boolean
  commandPaletteOpen: boolean
}
```

### Query Keys (React Query)

```typescript
['properties', { filters, sort, page }]     // property feed
['property', id]                              // single property
['property', id, 'score']                     // score breakdown
['property', id, 'underwriting']              // financial analysis
['property', id, 'history']                   // price history
['watchlist']                                 // user's watchlist
['outreach']                                  // outreach records
['reports', 'daily']                          // daily digest
['reports', 'market-pulse']                   // market stats
['profile']                                   // user profile
['subscription']                              // subscription info
```

### Optimistic Updates

- Watchlist save/remove: update UI immediately, rollback on error
- Outreach status changes: optimistic with retry
- Filter changes: debounced 300ms before API call

---

## 8. Real-Time Features

### WebSocket Events (via FastAPI WebSocket + Redis pub/sub)

```typescript
// Server → Client
'pipeline:complete'    — new properties scored, show refresh banner
'price:drop'           — watched property price changed
'status:change'        — watched property went pending/sold
'outreach:reply'       — agent replied to your email
'alert:sent'           — alert delivered successfully

// Client → Server
'subscribe:property'   — watch specific property for changes
'unsubscribe:property' — stop watching
```

### Push Notifications (PWA)

- Service worker for push notifications (in addition to SMS/WhatsApp)
- "New properties scored" notification with deep link to dashboard
- "Price drop on watched property" with link to detail

---

## 9. Mobile Strategy

### Phase 1: Progressive Web App (PWA)

- Service worker for offline access (cached property data)
- Add to Home Screen prompt
- Push notifications
- Responsive design (already implemented)
- Bottom navigation bar on mobile (instead of top hamburger)

### Phase 2: React Native App (Future)

- Shared API layer
- Native maps (better performance)
- Native push notifications
- Biometric auth (Face ID / fingerprint)
- Camera: scan a property address to look up score

### Mobile-Specific UI

- Bottom tab bar: Feed, Map, Watchlist, Alerts, Profile
- Pull-to-refresh on feed
- Swipe gestures: swipe right to save, swipe left to dismiss
- Property detail: sticky bottom bar with "Save" + "Contact Agent" + "View Listing"

---

## 10. Internationalization & Multi-Market

### Market Expansion Model

Each market is a `MarketConfig` (already built in `config/market.py`). To launch a new market:

1. Define market config: state, timezone, transit system, cities, tax rates, rent ratios
2. Add transit stations (subway, light rail, bus rapid transit)
3. Set city-level data: price floors, safety, walkability, avg rents
4. Configure ingestion: Redfin region IDs, Realtor slugs, Craigslist URLs
5. Add outreach templates with market-specific disclosures

### Phase 1 Markets (US)
- **Bay Area** ✅ (launched)
- **Austin, TX** — tech hub, strong investor community
- **Denver, CO** — fast-growing, transit-oriented (RTD light rail)

### Phase 2 Markets (US expansion)
- Phoenix, AZ — affordability play
- Raleigh-Durham, NC — research triangle
- Nashville, TN — growth market
- Seattle, WA — tech hub, ADU-friendly
- Portland, OR — ADU legislation leader

### Phase 3 Markets (International)
- **Toronto, Canada** — similar housing challenges
- **London, UK** — massive market, stamp duty complexity
- **Mumbai, India** — huge demand, different data sources (MagicBricks, 99acres)
- **Sydney, Australia** — investor-heavy market

### Localization

- Currency formatting (USD, CAD, GBP, INR, AUD)
- Unit conversion (sqft ↔ sqm)
- Tax system differences (property tax, stamp duty, GST)
- Transit system terminology (BART → Tube → Metro → Local Train)
- Disclosure forms (TDS/SPQ → SPIS → TA6/TA7 → varies)
- Date formats (MM/DD vs DD/MM)
- Language: English first, then Spanish, Hindi, French, Mandarin

---

## 11. Monetization & Subscription Tiers

### Pricing Structure

| Feature | Free | Pro ($19/mo) | Investor ($49/mo) |
|---------|------|-------------|-------------------|
| Markets | 1 | 3 | Unlimited |
| Target cities | 3 | 10 | Unlimited |
| Daily picks | Top 3 | Top 15 | All |
| Scoring | Basic (5 dims) | Full (8 dims) | Full + custom weights |
| Alerts | Email only | SMS + WhatsApp + Email | All + Slack + instant |
| Watchlist | 10 items | 100 items | Unlimited |
| Underwriting | View only | Full + edit assumptions | Full + export |
| CRM / Outreach | — | 5 drafts/mo | Unlimited |
| Map view | — | ✅ | ✅ |
| Price history | 30 days | 90 days | Full history |
| Reports | Daily digest | Daily + weekly | All + market pulse |
| API access | — | — | 1,000 calls/day |
| CSV export | — | — | 10/month |
| Saved searches | — | 3 | Unlimited |
| Board view (Kanban) | — | — | ✅ |

### Additional Revenue Streams

1. **Agent Referrals**: Partner with buyer's agents. When user clicks "Contact Agent" and closes → $500–2,000 referral fee.
2. **Lender Referrals**: "Get pre-approved" CTA → partner lender → $50–200/qualified lead.
3. **Premium Data**: Anonymized market intelligence sold to brokerages and developers.
4. **White-Label**: License scoring engine to real estate teams ($500–2,000/mo).
5. **Courses/Community**: "House-Hacking 101" course ($199) + private Discord/community.

### Stripe Integration

- Checkout: redirect to Stripe Checkout for upgrades
- Customer Portal: manage billing, update card, cancel
- Webhooks: `customer.subscription.created`, `updated`, `deleted`, `invoice.paid`, `payment_failed`
- Trial: 14-day free trial of Pro (no credit card required)
- Annual discount: Pro $190/yr (save $38), Investor $490/yr (save $98)

---

## 12. SEO & Growth

### SEO Pages (Auto-Generated)

- `/markets/bay-area` — Bay Area market overview + stats
- `/markets/bay-area/oakland` — City-level page with aggregate stats
- `/markets/bay-area/oakland/house-hack` — Strategy-specific city page
- `/blog/house-hacking-guide-bay-area` — Long-form content
- `/tools/mortgage-calculator` — Free tool for organic traffic
- `/tools/house-hack-calculator` — Strategy-specific calculator

### Content Strategy

- **Blog**: Weekly posts on house-hacking, ADU regulations, market analysis
- **Market Reports**: Monthly free reports (gated for email capture)
- **Property Spotlights**: "Property of the Week" — deep-dive analysis

### Growth Loops

1. **Viral sharing**: "Share this property score" → non-users see score page with CTA
2. **Agent loop**: agents see value in scored leads → recommend to buyer clients
3. **Content SEO**: calculator pages and guides rank for long-tail keywords
4. **Community**: Discord/Reddit presence in r/realestateinvesting, r/househacking
5. **Referral program**: "Give $10, Get $10" credit for referred signups

---

## 13. Performance & Infrastructure

### Frontend

- **Hosting**: Vercel (Edge Network, auto-scaling)
- **Images**: Next.js Image component with Vercel Image Optimization
- **Bundle**: Code-split per route, dynamic imports for heavy components (Mapbox, Recharts)
- **Caching**: ISR for marketing pages (1hr), SWR for dashboard data
- **Targets**: LCP < 1.5s, FID < 100ms, CLS < 0.1, TTI < 3s

### Backend

- **API**: FastAPI on Railway/Fly.io (auto-scaling)
- **Database**: PostgreSQL (Supabase or Neon — serverless Postgres)
- **Cache**: Redis (Upstash — serverless Redis)
- **Queue**: Redis + Celery for background jobs (ingestion, scoring, email sending)
- **Storage**: S3/R2 for property images (if scraped)

### Monitoring

- **Error tracking**: Sentry (frontend + backend)
- **Analytics**: PostHog (self-hosted) or Mixpanel
- **Uptime**: BetterUptime
- **Logs**: Axiom or Datadog
- **Performance**: Vercel Analytics + Web Vitals

---

## 14. Analytics & Metrics

### North Star Metric

**Weekly Active Scored Views**: Users who view a property detail page with scoring at least once per week.

### KPIs by Layer

| Layer | Metric | Target |
|-------|--------|--------|
| **Acquisition** | Signups/week | 100+ |
| **Activation** | Complete onboarding (%) | > 60% |
| **Engagement** | Properties viewed/user/week | > 10 |
| **Retention** | 30-day retention | > 40% |
| **Revenue** | Free → Pro conversion | > 8% |
| **Revenue** | Pro → Investor upgrade | > 15% |
| **Revenue** | Monthly churn | < 5% |

### Events to Track

```
page_view         — every page
property_viewed   — detail page opened
property_saved    — added to watchlist
property_shared   — share button clicked
outreach_drafted  — email composed
outreach_sent     — email sent to agent
filter_changed    — dashboard filter adjusted
score_expanded    — dimension detail opened
underwriting_run  — calculator used
alert_clicked     — user clicked property from alert
signup_started    — began signup flow
onboard_step_N    — completed onboarding step N
subscription_upgrade — tier change
```

---

## 15. Implementation Phases

### Phase 1: Foundation (Weeks 1–3)
**Goal**: API layer + auth + real data flowing to frontend

- [ ] FastAPI project setup with auth (JWT + OAuth)
- [ ] User + UserPreferences + WatchlistItem models + migrations
- [ ] Core API endpoints: /properties, /property/:id, /watchlist, /profile
- [ ] Connect frontend to real API (replace all mock data)
- [ ] Auth pages (signup, login, forgot password)
- [ ] Protected routes (middleware)
- [ ] React Query + Zustand setup
- [ ] Onboarding wizard saves to API

### Phase 2: Core Experience (Weeks 4–6)
**Goal**: Dashboard is fully functional with real data

- [ ] Dashboard filters → API query params
- [ ] Infinite scroll pagination
- [ ] Watchlist persistence (API-backed)
- [ ] Property detail with real score breakdown
- [ ] Underwriting panel with editable assumptions
- [ ] Price history timeline
- [ ] Loading skeletons and error states
- [ ] Mobile-responsive refinements

### Phase 3: Monetization (Weeks 7–9)
**Goal**: Stripe live, users can pay

- [ ] Stripe integration (checkout, portal, webhooks)
- [ ] Tier-gated features (map, custom weights, outreach, exports)
- [ ] Subscription management in settings
- [ ] Usage tracking and limits
- [ ] 14-day trial flow
- [ ] Upgrade prompts in UI (contextual, not annoying)

### Phase 4: Intelligence (Weeks 10–12)
**Goal**: The features that make users stay

- [ ] Map view with Mapbox GL
- [ ] CRM / outreach page
- [ ] Reports page (daily digest, weekly summary, market pulse)
- [ ] Real-time WebSocket updates
- [ ] Push notifications (PWA)
- [ ] Cmd+K command palette
- [ ] Similar properties recommendations

### Phase 5: Growth (Weeks 13–16)
**Goal**: Ready for public launch

- [ ] Landing page polish (live demo widget, FAQ, video)
- [ ] SEO pages (market, city, strategy)
- [ ] Blog/content CMS integration
- [ ] Referral program
- [ ] Second market launch (Austin or Denver)
- [ ] Public launch on Product Hunt, Hacker News
- [ ] Agent referral partnership pilot

### Phase 6: Scale (Months 5–8)
**Goal**: Multi-market, multi-language, mobile app

- [ ] 5+ US markets live
- [ ] React Native app (or Capacitor PWA wrapper)
- [ ] Advanced analytics (cohort analysis, funnel tracking)
- [ ] White-label/API product for agents
- [ ] Community features (user reviews, tips)
- [ ] International market pilot (Toronto or London)

---

## Appendix A: Tech Stack Summary

| Layer | Technology |
|-------|-----------|
| Frontend framework | Next.js 16 (App Router, RSC) |
| UI components | shadcn/ui + custom components |
| Styling | Tailwind CSS 4 (oklch colors) |
| Animations | Framer Motion |
| Charts | Recharts |
| Maps | Mapbox GL JS |
| Icons | Lucide React |
| State (server) | TanStack Query v5 |
| State (client) | Zustand |
| Forms | React Hook Form + Zod |
| URL state | nuqs |
| Auth | Auth.js v5 (NextAuth) |
| Backend | FastAPI (Python) |
| Database | PostgreSQL (Neon/Supabase) |
| Cache | Redis (Upstash) |
| Queue | Celery + Redis |
| Payments | Stripe |
| SMS/WhatsApp | Twilio |
| Email | Resend (transactional) |
| Hosting (FE) | Vercel |
| Hosting (BE) | Railway / Fly.io |
| Monitoring | Sentry + PostHog |
| CI/CD | GitHub Actions |

## Appendix B: File Structure (Target)

```
frontend/
├── src/
│   ├── app/
│   │   ├── (marketing)/           — Landing, pricing, about (no auth)
│   │   │   ├── page.tsx
│   │   │   ├── pricing/page.tsx
│   │   │   └── layout.tsx
│   │   ├── (auth)/                — Login, signup, forgot-password
│   │   │   ├── login/page.tsx
│   │   │   ├── signup/page.tsx
│   │   │   └── layout.tsx
│   │   ├── (app)/                 — Protected app routes
│   │   │   ├── dashboard/page.tsx
│   │   │   ├── property/[id]/page.tsx
│   │   │   ├── watchlist/page.tsx
│   │   │   ├── calculator/page.tsx
│   │   │   ├── outreach/page.tsx
│   │   │   ├── reports/page.tsx
│   │   │   ├── settings/page.tsx
│   │   │   ├── onboard/page.tsx
│   │   │   └── layout.tsx         — App shell with navbar + auth check
│   │   ├── (admin)/               — Admin routes
│   │   │   └── admin/page.tsx
│   │   ├── markets/[market]/page.tsx  — SEO market pages
│   │   └── layout.tsx             — Root layout
│   ├── components/
│   │   ├── ui/                    — shadcn base components
│   │   ├── property/              — PropertyCard, PropertyListRow, PropertyMap
│   │   ├── scoring/               — ScoreRing, ScoreBars, RadarChart
│   │   ├── underwriting/          — UnderwritingPanel, ScenarioCard, EquityChart
│   │   ├── outreach/              — TemplateEditor, OutreachTimeline
│   │   ├── layout/                — Navbar, Sidebar, Footer, MobileNav
│   │   └── shared/                — EmptyState, SkeletonCard, SearchCommand
│   ├── lib/
│   │   ├── api.ts                 — API client (fetch wrapper with auth)
│   │   ├── auth.ts                — Auth.js config
│   │   ├── queries.ts             — React Query hooks
│   │   ├── stores.ts              — Zustand stores
│   │   ├── utils.ts               — Formatting, helpers
│   │   └── types.ts               — TypeScript interfaces matching API
│   └── hooks/
│       ├── use-watchlist.ts       — Optimistic watchlist mutations
│       ├── use-filters.ts         — URL-synced filter state
│       └── use-websocket.ts       — Real-time event handler
```

---

*This spec is a living document. Update as features ship and priorities shift.*

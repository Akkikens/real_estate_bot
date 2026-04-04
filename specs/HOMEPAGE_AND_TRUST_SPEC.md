# HouseMatch — Homepage Redesign & Trust Infrastructure Spec

> **Version**: 1.0
> **Date**: 2026-04-04
> **Status**: Implementation-ready
> **Goal**: Transform the landing page from "weekend project" to "funded startup" — and build the full trust/compliance layer that makes enterprise buyers, investors, and cautious first-time users feel safe handing over their data.

---

## Table of Contents

1. [Why This Matters](#1-why-this-matters)
2. [Current State — What's Wrong](#2-current-state)
3. [Homepage Redesign — Section by Section](#3-homepage-redesign)
   - 3.1 Navigation Bar (upgraded)
   - 3.2 Hero Section
   - 3.3 Social Proof Bar
   - 3.4 How It Works
   - 3.5 Live Demo / Interactive Preview
   - 3.6 Features Grid
   - 3.7 Testimonials
   - 3.8 Pricing
   - 3.9 FAQ
   - 3.10 Final CTA
   - 3.11 Footer
4. [Trust & Compliance Infrastructure](#4-trust-compliance)
   - 4.1 Privacy Policy (`/privacy`)
   - 4.2 Terms of Service (`/terms`)
   - 4.3 Cookie Policy & Consent Banner
   - 4.4 Data Processing Agreement (DPA) page
   - 4.5 Security Page (`/security`)
   - 4.6 SOC 2 Alignment Checklist
5. [SEO & Technical Infrastructure](#5-seo-infrastructure)
   - 5.1 Metadata & Open Graph
   - 5.2 Sitemap & Robots
   - 5.3 Structured Data (JSON-LD)
   - 5.4 Performance Targets
6. [Shared Components](#6-shared-components)
   - 6.1 Footer Component
   - 6.2 Cookie Consent Banner
   - 6.3 Trust Badge Strip
7. [Implementation Checklist](#7-implementation-checklist)

---

## 1. Why This Matters {#1-why-this-matters}

The homepage is doing 3 jobs simultaneously:

| Job | Audience | What They Need to See |
|-----|----------|----------------------|
| **Convert visitors → signups** | First-time buyers Googling "bay area house hack tool" | Value prop in 5 seconds, social proof, low friction CTA |
| **Convert free → paid** | Existing free users who land on `/` | Feature comparison, clear upgrade path, testimonials from paid users |
| **Build institutional trust** | Investors, partners, agents considering integration | Security page, privacy policy, SOC 2 badge, professional footer |

The current homepage covers job #1 poorly and jobs #2 and #3 not at all. There's no footer with legal links, no privacy policy, no terms, no security page, no FAQ, no "how it works" section, and the social proof is 3 fake testimonials with no substance.

**Benchmark apps**: Linear.app (clean authority), Notion (social proof density), Lemonade (insurance trust signals), Plaid (security/compliance pages), Mercury (financial services trust).

---

## 2. Current State — What's Wrong {#2-current-state}

### Homepage Sections (what exists)

| Section | Status | Problem |
|---------|--------|---------|
| Hero | Exists | Decent copy but generic layout. Floating card only shows on XL screens. No video/animation showing the product. |
| Features | Exists (6 cards) | Generic icon-text cards. Nothing interactive. Doesn't show the actual product. |
| Testimonials | Exists (3) | Obviously fabricated. No photos, no specifics, no verification. |
| Pricing | Exists (3 tiers) | Functional but no FAQ, no annual toggle, no "most popular" emphasis. |
| Footer | Inline, minimal | Just logo + copyright. No nav links, no legal, no social, no trust signals. |

### Missing Entirely

| Item | Impact |
|------|--------|
| **Privacy Policy** | Required by law (CCPA/GDPR), required by Google Ads, required by App Store |
| **Terms of Service** | Legal liability shield. Required for paid subscriptions. |
| **Cookie Policy + Consent** | GDPR requirement for EU visitors. CCPA for CA residents. |
| **Security page** | Required for SOC 2. Required for enterprise/agent partnerships. |
| **FAQ section** | Reduces support load by 40%. Addresses pricing/data objections. |
| **How It Works** | Users need to understand the product before signing up. |
| **Sitemap + robots.txt** | SEO basics. Google can't properly index the site without these. |
| **Open Graph / Twitter Cards** | Links shared on social media show no preview image. |
| **Structured data** | No JSON-LD for SoftwareApplication schema. Missing from Google's rich results. |
| **Footer** | No reusable footer component. Only the landing page has one. |

---

## 3. Homepage Redesign — Section by Section {#3-homepage-redesign}

### Design Language

- **Font**: Keep Playfair Display (headings) + DM Sans (body) — they're distinctive
- **Color**: Amber/warm palette stays. Add a subtle gradient mesh background to hero.
- **Motion**: Upgrade from basic fade-in to scroll-triggered staggered reveals, parallax on hero, and micro-interactions on hover
- **Layout**: Break the "stacked rectangles" monotony with asymmetric sections, overlapping elements, and full-bleed color breaks

---

### 3.1 Navigation Bar (upgraded)

**Current**: Logo + Dashboard/Watchlist/Settings + Auth buttons
**Target**: Context-aware — show different nav for landing page vs logged-in app pages

```
Landing page nav:
┌─────────────────────────────────────────────────────────────────┐
│ [H] HouseMatch    Features  Pricing  FAQ  Security    [Sign In] [Get Started →] │
└─────────────────────────────────────────────────────────────────┘
```

**Implementation**:
- Detect `pathname === "/"` in `<Navbar>`
- On landing page: show anchor links (Features, Pricing, FAQ, Security) instead of Dashboard/Watchlist/Settings
- Sticky with background blur + border that appears on scroll (`scroll > 10px`)
- Mobile: same hamburger but with landing-page-appropriate links

---

### 3.2 Hero Section

**Philosophy**: The hero has one job — make the visitor think "this is for me" in 5 seconds. That means: (1) headline that names their problem, (2) subhead that names the solution, (3) visual proof that the product works, (4) one CTA.

**Layout**:
```
┌────────────────────────────────────────────────────────────────────┐
│  ┌──────────────────────────┐  ┌──────────────────────────────┐   │
│  │ badge: "Bay Area Beta"   │  │                              │   │
│  │                          │  │   [Product screenshot or     │   │
│  │ YOUR AI                  │  │    animated property card     │   │
│  │ PROPERTY SCOUT           │  │    cycling through real       │   │
│  │                          │  │    listings with scores]      │   │
│  │ Stop doom-scrolling      │  │                              │   │
│  │ Redfin. Get the top 5    │  │                              │   │
│  │ properties for YOUR      │  │                              │   │
│  │ strategy, delivered       │  │                              │   │
│  │ daily.                   │  │                              │   │
│  │                          │  │                              │   │
│  │ [Get Started Free →]     │  │                              │   │
│  │                          │  │                              │   │
│  │ ✓ Free forever plan      │  │                              │   │
│  │ ✓ No credit card         │  │                              │   │
│  │ ✓ 2-min setup            │  │                              │   │
│  └──────────────────────────┘  └──────────────────────────────┘   │
└────────────────────────────────────────────────────────────────────┘
```

**Key changes from current**:
- Two-column layout (text left, visual right) on desktop. Stacks on mobile.
- Replace the static floating card with an **animated property card carousel** that cycles through 3 real-looking listings with scores, tags, and price — shows the actual product value
- Add trust micro-copy below CTA: "Free forever plan · No credit card · 2-min setup"
- Background: subtle gradient mesh (warm amber → transparent) instead of flat blueprint grid
- Badge changes from "AI-powered property intelligence" (generic) to "Bay Area Beta — 1,400+ properties scored" (specific, credible)

**Hero visual — animated card**:
```tsx
// Cycles every 4 seconds between 3 properties
const heroProperties = [
  { address: "1247 Elm St, Fremont", score: 87, price: "$789k", tags: ["House Hack", "ADU", "Near BART"] },
  { address: "482 Oak Ave, Oakland", score: 92, price: "$625k", tags: ["Duplex", "Deal Signal", "Large Lot"] },
  { address: "3901 Pine Dr, Richmond", score: 78, price: "$510k", tags: ["House Hack", "Price Drop", "4 Bed"] },
];
```
Each card fades in with a score ring animation (0 → 87 in 1.5s), tags appear staggered, then fades out to the next. This is the single most impactful visual on the page — it shows exactly what the user gets.

---

### 3.3 Social Proof Bar

**New section** — a thin strip between hero and features. High information density, low visual weight.

```
┌─────────────────────────────────────────────────────────────────┐
│  🏠 1,400+ properties scored   👥 200+ Bay Area buyers         │
│  ⭐ 4.8 avg rating             📊 Updated daily                │
└─────────────────────────────────────────────────────────────────┘
```

**Implementation**:
- Single row of 4 stats with icons, subtle separator lines
- Numbers should be fetched from the `/api/v1/stats` endpoint where possible (total_active)
- Light background tint, small text, monospace numbers
- Animates numbers counting up on scroll into view

---

### 3.4 How It Works

**New section** — 3 steps with connected timeline visual.

```
Step 1: Tell Us Your Strategy        Step 2: We Score Everything        Step 3: Get Your Top Picks
[Icon: Target]                       [Icon: BarChart3]                  [Icon: Bell]
Pick house-hack, buy & hold,         Every listing gets scored          Top 5 delivered to your
or primary residence. Set your       0–100 across 8 dimensions          phone daily via SMS or
budget and target cities.            tailored to YOUR criteria.         WhatsApp. One tap to save.

          ─────────────────────○─────────────────────○─────────────────────
```

**Design**:
- Connected dots timeline (horizontal on desktop, vertical on mobile)
- Each step has a subtle illustration or product screenshot showing that step
- Step 1: mini screenshot of the onboarding city picker
- Step 2: mini screenshot of a score breakdown with bars
- Step 3: mini screenshot of a phone with an SMS alert
- Background: alternating bg-card/50 section

---

### 3.5 Live Demo / Interactive Preview

**New section** — The highest-converting element on the entire page. Let the visitor **try the product** without signing up.

```
┌─────────────────────────────────────────────────────────────────┐
│  See what HouseMatch finds for you                              │
│                                                                 │
│  Budget: [$500k ──────●────── $1.5M]   Strategy: [House Hack ▾]│
│                                                                 │
│  ┌───────────┐  ┌───────────┐  ┌───────────┐                   │
│  │ 482 Oak   │  │ 1247 Elm  │  │ 3901 Pine │                   │
│  │ Oakland   │  │ Fremont   │  │ Richmond  │                   │
│  │ Score: 92 │  │ Score: 87 │  │ Score: 78 │                   │
│  │ $625k     │  │ $789k     │  │ $510k     │                   │
│  └───────────┘  └───────────┘  └───────────┘                   │
│                                                                 │
│  ✨ 847 more properties waiting → [Get My Full Feed →]          │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

**Implementation**:
- Budget slider (reuse from onboarding) + strategy dropdown
- Fetch from `GET /api/v1/properties?max_price={}&page_size=3&sort=score` (public, no auth)
- Show 3 real property cards with real scores
- Below: "X more properties waiting → Get My Full Feed" CTA
- This is essentially a mini-dashboard. The user sees real value before signing up.

---

### 3.6 Features Grid

**Upgrade from current**: Replace generic icon+text cards with **feature sections** — alternating left-right layouts with product screenshots or illustrations.

**6 features, shown as 3 pairs**:

```
Feature 1: AI-Powered Scoring (LEFT text, RIGHT visual)
────────────────────────────────────────────────────────
Every listing scored 0–100 across 8 dimensions:
Price Fit · House Hack · Rental Income · ADU Upside
Transit · Neighborhood · Deal Signal · Lot Expansion

See exactly WHY a property scored high — and what to watch out for.

[Visual: score breakdown bars, animated on scroll]


Feature 2: Your Strategy, Your Scores (RIGHT text, LEFT visual)
────────────────────────────────────────────────────────
Pick House-Hack, Buy & Hold, or Primary Residence.
We re-weight every dimension to match your playbook.

A duplex near BART scores 92 for a house-hacker but 61 for
someone who just wants a quiet family home. Same property,
different score — because your strategy matters.

[Visual: side-by-side comparison showing same property with
different scores for different strategies]


Feature 3: Daily Alerts — Right to Your Phone (LEFT text, RIGHT visual)
────────────────────────────────────────────────────────
Top picks delivered via SMS, WhatsApp, or email at the
time you choose. We filter out the noise so you only
see properties that actually match.

Stop refreshing Redfin 12 times a day.

[Visual: phone mockup showing SMS alert]
```

Then the remaining 3 features as a compact grid below:
- **Multi-Source Data** — Redfin + Zillow + Realtor.com + Craigslist. No blind spots.
- **Price Drop Tracking** — Get alerted when a saved property drops. Know the real market.
- **ADU & Lot Analysis** — Spot in-law unit potential and lot expansion opportunities automatically.

---

### 3.7 Testimonials (upgraded)

**Current**: 3 obviously fake quotes
**Target**: 6 testimonials in a 2-row marquee/carousel with depth

Each testimonial card:
```
┌──────────────────────────────────────────┐
│ ⭐⭐⭐⭐⭐                                  │
│                                          │
│ "Found my house-hack duplex in 2 weeks.  │
│  The ADU scoring alone saved me months." │
│                                          │
│ ┌──┐ Priya M.                           │
│ │🟡│ First-time buyer · Fremont          │
│ └──┘ Saved $45k on her first deal        │
│                                          │
│ Property score: [87 ring]                │
└──────────────────────────────────────────┘
```

**Key upgrades**:
- Add a **quantified outcome** line: "Saved $45k", "Covers 80% of mortgage", "Found deal in 2 weeks"
- Add avatar placeholder circles (colored initials, not stock photos)
- Auto-scrolling marquee (2 rows, opposite directions) for a dynamic feel
- If possible, link to real Trustpilot or Google reviews in the future

---

### 3.8 Pricing (upgraded)

**Current**: 3 static cards
**Target**: Add annual toggle, FAQ below, and "compare all features" expandable table

```
┌─────────────────────────────────────────────────────────────────┐
│  Simple, transparent pricing                                     │
│  [Monthly ○ Annual (save 20%)]                                  │
│                                                                 │
│  ┌─────────┐   ┌──────────────┐   ┌─────────┐                  │
│  │  Free   │   │ ✦ PRO        │   │ Investor│                  │
│  │  $0/mo  │   │   $19/mo     │   │ $49/mo  │                  │
│  │         │   │   $15/mo ann │   │ $39/mo  │                  │
│  │  ...    │   │   ...        │   │ ...     │                  │
│  └─────────┘   └──────────────┘   └─────────┘                  │
│                                                                 │
│  [▾ Compare all features]                                       │
│                                                                 │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │ Feature          │ Free │ Pro  │ Investor │              │   │
│  │ Target cities    │ 3    │ ∞    │ ∞        │              │   │
│  │ Scoring dims     │ 5    │ 8    │ 8+custom │              │   │
│  │ Watchlist slots  │ 10   │ 100  │ ∞        │              │   │
│  │ SMS/WhatsApp     │ ✗    │ ✓    │ ✓        │              │   │
│  │ API access       │ ✗    │ ✗    │ ✓        │              │   │
│  │ CSV export       │ ✗    │ ✗    │ ✓        │              │   │
│  │ Support          │ Email│ Chat │ Priority │              │   │
│  └──────────────────────────────────────────────────────────┘   │
│                                                                 │
│  All plans include: Unlimited property views · Daily updates    │
│  · Price drop alerts · Bay Area coverage                        │
└─────────────────────────────────────────────────────────────────┘
```

**Annual pricing**: Monthly prices × 10 (2 months free) = $0, $15/mo, $39/mo

---

### 3.9 FAQ

**New section** — Collapsible accordion. Addresses the top 10 objections that prevent signup.

```
Q: Where does HouseMatch get its data?
A: We aggregate from Redfin, Zillow, Realtor.com, Craigslist, and public records.
   Data is refreshed daily. We cross-reference multiple sources to catch listings
   others miss and verify pricing accuracy.

Q: How does the scoring work?
A: Every property is scored 0–100 across 8 weighted dimensions: Price Fit, House
   Hack Potential, Rental Income, ADU Upside, Transit Access, Neighborhood Quality,
   Deal Opportunity, and Lot Expansion. Weights adjust based on your strategy.

Q: Is my data safe?
A: Yes. We use Clerk for authentication (SOC 2 Type II certified), encrypt all data
   in transit (TLS 1.3) and at rest. We never sell your personal information. See
   our [Privacy Policy](/privacy) and [Security](/security) page for details.

Q: Can I use HouseMatch outside the Bay Area?
A: We're currently Bay Area only (15 cities from Richmond to San Jose). We're
   expanding to Sacramento, LA, and Portland in 2026. Join the waitlist to be first.

Q: What's a "house hack"?
A: House hacking means buying a property, living in one part, and renting out the
   rest to offset your mortgage. Example: buy a 4BR, rent 3 rooms at $1,400/ea,
   cover 85% of your mortgage from day one.

Q: Do I need to pay to browse properties?
A: No. Browsing the full property feed, viewing scores, and property details are
   free forever. Paid plans add SMS/WhatsApp alerts, unlimited watchlist, and
   advanced scoring dimensions.

Q: How is this different from Zillow or Redfin?
A: Zillow and Redfin show you every listing equally. HouseMatch scores every
   listing against YOUR specific strategy, budget, and preferences — then delivers
   only the best ones. We don't sell ads or promote agent listings.

Q: Can I cancel anytime?
A: Yes. No contracts, no cancellation fees. Cancel from Settings → Subscription
   and your plan reverts to Free at the end of your billing period.

Q: Who built this?
A: HouseMatch is built by a team of Bay Area house-hackers who were tired of
   spending hours on Redfin every day. We built the tool we wished existed.

Q: How do I get support?
A: Email support@housematch.io. Pro and Investor customers get priority response
   within 4 hours during business hours.
```

---

### 3.10 Final CTA

**Full-bleed amber/warm background section — last push before footer.**

```
┌─────────────────────────────────────────────────────────────────┐
│                                                                 │
│         Stop scrolling. Start scoring.                          │
│                                                                 │
│         Your next investment property is already listed.        │
│         We just need 2 minutes to find it for you.              │
│                                                                 │
│         [Get Started Free →]                                    │
│                                                                 │
│         ✓ No credit card required                               │
│         ✓ Cancel anytime                                        │
│         ✓ 1,400+ Bay Area properties scored                     │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

---

### 3.11 Footer

**Create a reusable `<Footer>` component** used on all pages.

```
┌─────────────────────────────────────────────────────────────────┐
│                                                                 │
│  [H] HouseMatch              Product        Legal       Connect │
│  AI-powered property         Dashboard      Privacy     Twitter │
│  intelligence for            Pricing        Terms       GitHub  │
│  house-hackers.              Security       Cookies     Email   │
│                              FAQ            DPA                 │
│                              Changelog                          │
│                                                                 │
│  ─────────────────────────────────────────────────────────────  │
│                                                                 │
│  © 2026 HouseMatch Inc.   All rights reserved.                  │
│                                                                 │
│  [SOC 2 badge] [Clerk badge] [SSL badge]                        │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

**Footer links organized in 3 columns**:

| Product | Legal | Connect |
|---------|-------|---------|
| Dashboard | Privacy Policy | Twitter/X |
| Pricing | Terms of Service | GitHub |
| Security | Cookie Policy | support@housematch.io |
| FAQ | DPA | |
| Changelog | | |

---

## 4. Trust & Compliance Infrastructure {#4-trust-compliance}

### 4.1 Privacy Policy (`/privacy`)

**Route**: `/privacy`
**SEO title**: "Privacy Policy — HouseMatch"

**Must cover (CCPA + GDPR)**:
1. **What data we collect** — email, name, phone (optional), property preferences, search history, watchlist, IP address, device info (via Clerk)
2. **Why we collect it** — to provide personalized property scores, deliver alerts, improve the product
3. **How we store it** — Supabase PostgreSQL (encrypted at rest), Clerk (SOC 2 Type II for auth data)
4. **Who we share with** — nobody. We do not sell personal data. Third parties: Clerk (auth), Stripe (payments), Twilio (SMS/WhatsApp delivery)
5. **Data retention** — account data retained while account is active. Deleted within 30 days of account deletion request.
6. **User rights (CCPA)** — right to know, right to delete, right to opt-out of sale (we don't sell, but must state this), right to non-discrimination
7. **User rights (GDPR)** — right of access, rectification, erasure, portability, restrict processing, object to processing
8. **Cookies** — see Cookie Policy. We use essential cookies only (Clerk session). No advertising cookies.
9. **Children** — not directed at users under 18
10. **Contact** — privacy@housematch.io
11. **Effective date** — April 2026
12. **Updates** — we'll notify by email for material changes

**Format**: Clean typography, table of contents, accordion sections. NOT a wall of legal text.

---

### 4.2 Terms of Service (`/terms`)

**Route**: `/terms`
**SEO title**: "Terms of Service — HouseMatch"

**Must cover**:
1. **Acceptance** — by creating an account, you agree
2. **Description of service** — property scoring, alerts, watchlist
3. **Accounts** — Clerk manages auth; you're responsible for your account security
4. **Subscriptions & billing** — Stripe handles billing. Cancellation policy. No refunds for partial months. Free tier is genuinely free with no hidden charges.
5. **Acceptable use** — no scraping, no automated access (except via Investor API), no reselling data
6. **Data accuracy disclaimer** — property data sourced from third parties. We don't guarantee accuracy. Not a substitute for professional real estate advice.
7. **Intellectual property** — our scoring algorithms, UI, and content are ours. Property data belongs to respective sources.
8. **Limitation of liability** — standard limitation. Not responsible for investment decisions made based on our scores.
9. **Termination** — we can terminate accounts that violate terms
10. **Governing law** — State of California
11. **Dispute resolution** — binding arbitration, opt-out clause within 30 days
12. **Contact** — legal@housematch.io

---

### 4.3 Cookie Policy & Consent Banner

**Route**: `/cookies` (policy page)
**Component**: `<CookieConsent>` (banner)

**Cookies we use**:

| Cookie | Provider | Purpose | Type | Duration |
|--------|----------|---------|------|----------|
| `__clerk_db_jwt` | Clerk | Session authentication | Essential | Session |
| `__client_uat` | Clerk | Session state | Essential | Session |
| `hm_cookie_consent` | Us | Remember consent choice | Essential | 1 year |
| `hm_onboard_progress` | Us (localStorage) | Onboarding resume | Functional | 30 days |

**Consent banner** — appears on first visit, bottom of screen:

```
┌─────────────────────────────────────────────────────────────────┐
│ 🍪 We use essential cookies to keep you signed in. No tracking, │
│ no ads. Read our [Cookie Policy].         [Got it]              │
└─────────────────────────────────────────────────────────────────┘
```

- We only use essential cookies (Clerk auth), so we don't need a complex preference manager
- Single "Got it" button stores `hm_cookie_consent=accepted` in localStorage
- Banner does NOT show again after acceptance
- For GDPR: essential cookies don't require consent, but showing the banner builds trust

---

### 4.4 Data Processing Agreement (`/dpa`)

**Route**: `/dpa`
**Purpose**: Required for B2B/enterprise customers. Shows we take data seriously.

**Content**: Standard DPA covering:
- Data processing scope (what data, what processing)
- Sub-processors list (Clerk, Supabase/AWS, Stripe, Twilio)
- Security measures (encryption, access controls, monitoring)
- Data breach notification (72 hours per GDPR)
- Data deletion upon termination
- Audit rights

**Note**: This can be a simpler page at MVP stage — just the sub-processor list and key commitments. Full legal DPA can be a downloadable PDF later.

---

### 4.5 Security Page (`/security`)

**Route**: `/security`
**SEO title**: "Security — HouseMatch"
**Purpose**: Single page that answers "is my data safe?" for all audiences.

**Sections**:

```
1. Our Security Commitment
   Brief statement: "We treat your data like we treat our own home search —
   with serious care."

2. Infrastructure
   ┌──────────────────────────────────────────────────────────┐
   │ ✓ Encryption in transit (TLS 1.3)                        │
   │ ✓ Encryption at rest (AES-256 via Supabase)              │
   │ ✓ Database hosted on Supabase (AWS us-east-1)            │
   │ ✓ Frontend hosted on Vercel (edge network)               │
   │ ✓ Authentication via Clerk (SOC 2 Type II)               │
   │ ✓ Payment processing via Stripe (PCI DSS Level 1)        │
   └──────────────────────────────────────────────────────────┘

3. Authentication & Access
   - Clerk manages all authentication (we never see or store passwords)
   - OAuth via Google (optional)
   - Session tokens with automatic rotation
   - No shared accounts — each user has isolated data

4. Data Practices
   - We collect only what we need (email, preferences, watchlist)
   - We never sell personal data
   - Property data is sourced from public listings
   - Data deletion available on request (Settings → Delete Account)

5. Third-Party Sub-Processors
   | Service   | Purpose                  | Certification     |
   |-----------|--------------------------|-------------------|
   | Clerk     | Authentication           | SOC 2 Type II     |
   | Supabase  | Database                 | SOC 2 Type II     |
   | Stripe    | Payments                 | PCI DSS Level 1   |
   | Twilio    | SMS/WhatsApp delivery    | SOC 2 Type II     |
   | Vercel    | Frontend hosting         | SOC 2 Type II     |

6. Vulnerability Reporting
   Found a security issue? Email security@housematch.io
   We respond within 24 hours and don't pursue legal action
   against good-faith security researchers.

7. SOC 2 Compliance Status
   "We are working toward SOC 2 Type II compliance. Our key
   sub-processors (Clerk, Supabase, Stripe, Vercel) are all
   SOC 2 Type II certified. Contact security@housematch.io
   for our current security questionnaire."
```

---

### 4.6 SOC 2 Alignment Checklist

SOC 2 is organized around 5 Trust Service Criteria. Here's what HouseMatch needs:

#### CC1: Control Environment

| Requirement | Status | Action Needed |
|-------------|--------|---------------|
| Security policy documented | Not started | Write `SECURITY_POLICY.md` internal doc |
| Roles & responsibilities defined | Not started | Define admin vs user vs service account roles |
| Code of conduct | Not started | Internal document |

#### CC2: Communication & Information

| Requirement | Status | Action Needed |
|-------------|--------|---------------|
| Privacy policy published | Not started | Build `/privacy` page |
| Terms of service published | Not started | Build `/terms` page |
| Security page published | Not started | Build `/security` page |
| Sub-processor list published | Not started | Include in `/security` and `/dpa` |

#### CC3: Risk Assessment

| Requirement | Status | Action Needed |
|-------------|--------|---------------|
| Risk register maintained | Not started | Create internal risk register |
| Vendor risk assessment | Partial | Clerk, Supabase, Stripe are all SOC 2 — document this |

#### CC6: Logical & Physical Access Controls

| Requirement | Status | Action Needed |
|-------------|--------|---------------|
| Authentication via SSO/MFA | ✅ Done | Clerk handles this (MFA optional, can be enforced) |
| Role-based access control | Partial | Backend has user roles; need admin vs user enforcement |
| Session management | ✅ Done | Clerk handles session rotation, expiry |
| API authentication | ✅ Done | Clerk JWT verification on all protected endpoints |
| Secrets management | ✅ Done | `.env` files excluded from git, Vercel env vars for production |

#### CC7: System Operations

| Requirement | Status | Action Needed |
|-------------|--------|---------------|
| Monitoring & alerting | Not started | Add error tracking (Sentry), uptime monitoring |
| Incident response plan | Not started | Document incident response procedure |
| Backup & recovery | ✅ Done | Supabase handles automated backups |
| Change management | Partial | Git + PR reviews; need formal policy |

#### CC8: Change Management

| Requirement | Status | Action Needed |
|-------------|--------|---------------|
| Version control | ✅ Done | Git |
| Code review process | Not started | Enforce PR reviews |
| Deployment process documented | Not started | Document Vercel deployment flow |

#### CC9: Risk Mitigation

| Requirement | Status | Action Needed |
|-------------|--------|---------------|
| Vendor agreements | Partial | Clerk, Stripe have standard DPAs |
| Business continuity plan | Not started | Document what happens if a sub-processor goes down |

**Priority for MVP**: Build the public-facing trust pages (privacy, terms, security, cookies). The internal SOC 2 policies can come later when pursuing formal certification.

---

## 5. SEO & Technical Infrastructure {#5-seo-infrastructure}

### 5.1 Metadata & Open Graph

**`layout.tsx` metadata export**:

```typescript
export const metadata: Metadata = {
  metadataBase: new URL("https://housematch.io"),
  title: {
    default: "HouseMatch — Your AI Property Scout",
    template: "%s | HouseMatch",
  },
  description:
    "Personalized property scores for Bay Area house-hackers and first-time investors. Get the top 5 deals delivered daily.",
  keywords: [
    "house hack", "bay area real estate", "property scoring",
    "first time home buyer", "investment property", "ADU",
    "oakland real estate", "fremont homes", "BART proximity",
  ],
  authors: [{ name: "HouseMatch" }],
  creator: "HouseMatch",
  openGraph: {
    type: "website",
    locale: "en_US",
    url: "https://housematch.io",
    siteName: "HouseMatch",
    title: "HouseMatch — Your AI Property Scout",
    description: "Personalized property scores for Bay Area house-hackers. 1,400+ properties scored daily.",
    images: [{ url: "/og-image.png", width: 1200, height: 630, alt: "HouseMatch" }],
  },
  twitter: {
    card: "summary_large_image",
    title: "HouseMatch — Your AI Property Scout",
    description: "Personalized property scores for Bay Area house-hackers.",
    images: ["/og-image.png"],
  },
  robots: {
    index: true,
    follow: true,
  },
};
```

**Per-page metadata** (each page.tsx exports its own):
- `/dashboard` → "Dashboard | HouseMatch"
- `/property/[id]` → "{address} — Score {score} | HouseMatch" (dynamic)
- `/watchlist` → "Watchlist | HouseMatch"
- `/privacy` → "Privacy Policy | HouseMatch"
- `/terms` → "Terms of Service | HouseMatch"
- `/security` → "Security | HouseMatch"

### 5.2 Sitemap & Robots

**`app/sitemap.ts`**:
```typescript
export default function sitemap(): MetadataRoute.Sitemap {
  return [
    { url: "https://housematch.io", lastModified: new Date(), changeFrequency: "weekly", priority: 1 },
    { url: "https://housematch.io/dashboard", lastModified: new Date(), changeFrequency: "daily", priority: 0.9 },
    { url: "https://housematch.io/privacy", lastModified: new Date(), changeFrequency: "monthly", priority: 0.3 },
    { url: "https://housematch.io/terms", lastModified: new Date(), changeFrequency: "monthly", priority: 0.3 },
    { url: "https://housematch.io/security", lastModified: new Date(), changeFrequency: "monthly", priority: 0.5 },
  ];
}
```

**`app/robots.ts`**:
```typescript
export default function robots(): MetadataRoute.Robots {
  return {
    rules: { userAgent: "*", allow: "/", disallow: ["/api/", "/settings", "/onboard"] },
    sitemap: "https://housematch.io/sitemap.xml",
  };
}
```

### 5.3 Structured Data (JSON-LD)

Add to landing page `<head>`:
```json
{
  "@context": "https://schema.org",
  "@type": "SoftwareApplication",
  "name": "HouseMatch",
  "applicationCategory": "BusinessApplication",
  "operatingSystem": "Web",
  "description": "AI-powered property scoring for Bay Area house-hackers and investors",
  "offers": [
    { "@type": "Offer", "price": "0", "priceCurrency": "USD", "name": "Free" },
    { "@type": "Offer", "price": "19", "priceCurrency": "USD", "name": "Pro" },
    { "@type": "Offer", "price": "49", "priceCurrency": "USD", "name": "Investor" }
  ],
  "aggregateRating": {
    "@type": "AggregateRating",
    "ratingValue": "4.8",
    "reviewCount": "127"
  }
}
```

### 5.4 Performance Targets

| Metric | Target | Why |
|--------|--------|-----|
| LCP | < 2.5s | Core Web Vital — Google ranking factor |
| FID | < 100ms | Core Web Vital |
| CLS | < 0.1 | Core Web Vital |
| Bundle size (homepage) | < 200kb gzipped | Mobile load time |
| Time to Interactive | < 3.5s on 3G | Accessibility |

**Actions**:
- Lazy load below-fold sections (testimonials, pricing, FAQ) with `dynamic()` or intersection observer
- Optimize hero image / animation — don't load Framer Motion for below-fold sections
- Use `next/image` for any images
- Preload hero fonts

---

## 6. Shared Components {#6-shared-components}

### 6.1 Footer Component (`components/footer.tsx`)

Reusable across all pages. 3-column link grid + bottom bar with copyright and trust badges.

**Props**: none (static content)
**Used in**: landing page, all legal pages, settings, potentially dashboard

### 6.2 Cookie Consent Banner (`components/cookie-consent.tsx`)

- Renders at bottom of viewport, fixed position
- Checks `localStorage.getItem("hm_cookie_consent")`
- If not set: show banner with "Got it" button
- On accept: set `hm_cookie_consent=accepted`, hide banner
- Renders in root layout (always present)
- Animate in from bottom with Framer Motion

### 6.3 Trust Badge Strip

Reusable component showing security certifications:
```
[🔒 SSL Encrypted] [Clerk Auth · SOC 2] [Stripe · PCI DSS] [CCPA Compliant]
```

Used in: footer, security page, pricing section

---

## 7. Implementation Checklist {#7-implementation-checklist}

### Phase 1: Trust Infrastructure (do first — these are legal requirements)

- [ ] Create `/privacy` page with full CCPA/GDPR privacy policy
- [ ] Create `/terms` page with terms of service
- [ ] Create `/cookies` page with cookie policy
- [ ] Create `/security` page with security overview
- [ ] Create `/dpa` page with sub-processor list
- [ ] Build `<Footer>` component with all legal links
- [ ] Build `<CookieConsent>` banner component
- [ ] Add footer to all pages (landing, dashboard, watchlist, settings, property detail)
- [ ] Add `sitemap.ts` and `robots.ts`
- [ ] Update `layout.tsx` with full metadata, Open Graph, Twitter cards
- [ ] Create OG image (`public/og-image.png`) — 1200x630

### Phase 2: Homepage Redesign

- [ ] Upgrade hero: two-column layout, animated property card carousel, trust micro-copy
- [ ] Add social proof bar with real stats from API
- [ ] Build "How It Works" section with 3-step timeline
- [ ] Build interactive preview section (budget slider + live property fetch)
- [ ] Upgrade features to alternating left-right layout with visuals
- [ ] Upgrade testimonials with quantified outcomes and auto-scroll marquee
- [ ] Add annual/monthly pricing toggle with comparison table
- [ ] Build FAQ accordion section (10 questions)
- [ ] Build final CTA section (full-bleed warm background)
- [ ] Context-aware navbar (different links for landing page vs app pages)

### Phase 3: SEO & Performance

- [ ] Add JSON-LD structured data to landing page
- [ ] Per-page metadata for all routes
- [ ] Dynamic OG metadata for property pages (`/property/[id]`)
- [ ] Lazy load below-fold sections
- [ ] Test Core Web Vitals and optimize
- [ ] Submit sitemap to Google Search Console

### Phase 4: SOC 2 Internal (not user-facing — do when pursuing certification)

- [ ] Write internal security policy document
- [ ] Document incident response procedure
- [ ] Set up error tracking (Sentry)
- [ ] Set up uptime monitoring
- [ ] Enforce PR reviews
- [ ] Document deployment process
- [ ] Create risk register
- [ ] Enable MFA enforcement for admin accounts in Clerk

---

**End of spec.**

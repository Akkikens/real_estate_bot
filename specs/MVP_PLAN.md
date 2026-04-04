# HouseMatch — Personalized Property Intelligence

## The Problem

First-time buyers and house-hackers waste 10+ hours/week scrolling Zillow/Redfin with dumb filters (beds, price, sqft). Nobody scores listings against their **actual strategy** — house-hack potential, ADU upside, transit to their job, rental income vs their mortgage terms, deal signals.

## The Product

A **strategy-first property search engine** that:
1. User builds a **buyer profile** (budget, down payment, strategy, commute, must-haves)
2. We ingest every listing from MLS/Redfin/Zillow/Craigslist
3. Score each listing 0-100 against their profile
4. Push **daily top picks via WhatsApp** (and SMS/email)
5. Users pay for premium scoring + instant alerts + more markets

## Target Customer

- First-time buyers doing house-hacking (live in one unit, rent the rest)
- Small real estate investors (1-4 units)
- Bay Area first, then expand to Austin, Denver, Phoenix, Atlanta

---

## MVP Architecture

```
┌─────────────────────────────────────────────────────────┐
│                    FRONTEND (Next.js)                     │
│                                                           │
│  ┌──────────┐  ┌──────────────┐  ┌───────────────────┐  │
│  │  Onboard  │  │  Dashboard   │  │  Property Detail  │  │
│  │  Wizard   │  │  (Top Picks) │  │  + Score Breakdown│  │
│  └──────────┘  └──────────────┘  └───────────────────┘  │
│                                                           │
│  ┌──────────────┐  ┌─────────────┐  ┌────────────────┐  │
│  │ Profile      │  │ Saved /     │  │ Subscription   │  │
│  │ Builder      │  │ Watchlist   │  │ + Billing      │  │
│  └──────────────┘  └─────────────┘  └────────────────┘  │
└───────────────────────┬─────────────────────────────────┘
                        │ API
┌───────────────────────▼─────────────────────────────────┐
│                  BACKEND (FastAPI / Python)               │
│                                                           │
│  ┌──────────┐  ┌───────────┐  ┌────────────────────┐    │
│  │ Auth     │  │ Scoring   │  │ Notification       │    │
│  │ (Clerk)  │  │ Engine    │  │ Service            │    │
│  │          │  │           │  │ (WhatsApp/SMS/Email)│    │
│  └──────────┘  └───────────┘  └────────────────────┘    │
│                                                           │
│  ┌──────────────┐  ┌───────────────┐  ┌──────────────┐  │
│  │ Ingestion    │  │ Enrichment    │  │ Subscription │  │
│  │ Pipeline     │  │ (BART, Walk   │  │ Manager      │  │
│  │ (MLS/Redfin/ │  │  Score, etc.) │  │ (Stripe)     │  │
│  │  Zillow/CL)  │  │               │  │              │  │
│  └──────────────┘  └───────────────┘  └──────────────┘  │
└───────────────────────┬─────────────────────────────────┘
                        │
┌───────────────────────▼─────────────────────────────────┐
│                     DATA LAYER                            │
│                                                           │
│  ┌──────────────┐  ┌───────────┐  ┌──────────────────┐  │
│  │ PostgreSQL   │  │ Redis     │  │ S3 / Supabase    │  │
│  │ (Supabase)   │  │ (Queue +  │  │ Storage          │  │
│  │              │  │  Cache)   │  │ (listing images) │  │
│  └──────────────┘  └───────────┘  └──────────────────┘  │
└─────────────────────────────────────────────────────────┘
```

---

## WhatsApp Integration (Twilio WhatsApp Business API)

### How It Works

```
User signs up → picks WhatsApp as channel → gets daily digest at their chosen time

Morning message example:
━━━━━━━━━━━━━━━━━━━
🏠 HouseMatch Daily — 3 New Picks

#1 ⭐ 82/100 — $499k Oakland 6BR
   0.3mi to BART | Duplex | ADU lot
   House-hack: rent 4 rooms @ $1,400 = $5,600/mo
   → redfin.com/CA/Oakland/1655-8th-St...

#2 ⭐ 78/100 — $599k Oakland 5BR
   0.4mi to BART | 6,850sqft lot
   House-hack: rent 3 rooms @ $1,400 = $4,200/mo
   → redfin.com/CA/Oakland/1538-39th...

#3 ⭐ 75/100 — $499k Oakland 6BR
   1.2mi to BART | 5,201sqft lot
   → redfin.com/CA/Oakland/10419-San-Leandro...

Reply 1/2/3 for full breakdown
Reply SAVE 1 to add to watchlist
Reply SETTINGS to change preferences
━━━━━━━━━━━━━━━━━━━
```

### Twilio WhatsApp Setup

You already have Twilio. To enable WhatsApp:

1. **Twilio Console → Messaging → WhatsApp Senders**
2. Register your Twilio number for WhatsApp Business
3. Submit message templates for approval (required by Meta):
   - `daily_digest` — daily property picks
   - `price_drop_alert` — price reduction notification
   - `new_match_alert` — new high-score listing
4. Use the Twilio WhatsApp API (same SDK, just prefix number with `whatsapp:`)

```python
# Sending WhatsApp is nearly identical to SMS:
client.messages.create(
    body=message,
    from_='whatsapp:+18666213250',
    to='whatsapp:+17746969534',
)
```

### Two-Way Conversation

WhatsApp supports **reply-based interaction** (24-hour session window):
- User replies "1" → get full score breakdown for pick #1
- User replies "SAVE 1" → add to watchlist
- User replies "MORE" → next 3 picks
- User replies "STOP" → unsubscribe

This is powerful because users engage **inside WhatsApp** — no app download needed.

---

## Subscription Model

### Tiers

| Feature | Free | Pro ($19/mo) | Investor ($49/mo) |
|---|---|---|---|
| Markets | 1 city | 5 cities | Unlimited |
| Daily picks | Top 3 | Top 10 | Top 25 |
| Channels | Email only | WhatsApp + SMS + Email | All + Slack webhook |
| Score threshold | 70+ only | Custom (50-90) | Custom + saved searches |
| Alerts | Daily digest | Daily + instant alerts | Instant + price drops |
| Profile filters | Basic (beds, price) | Full (ADU, transit, lot, pool, etc.) | Full + investment calc |
| History | 7 days | 90 days | Unlimited |
| Watchlist | 5 properties | 50 properties | Unlimited |
| Underwriting | — | Basic (PITI + rent est.) | Full (ROI, cap rate, cash-on-cash) |
| Data export | — | — | CSV + API access |

### Revenue Math

- 1,000 free users → 10% convert = 100 Pro ($1,900/mo)
- 100 Pro users → 20% upgrade = 20 Investor ($980/mo)
- **MRR: ~$2,880/mo at 1,000 users**
- At 10,000 users: ~$28,800/mo

### Additional Revenue Streams

1. **Agent referrals** — connect buyers with agents, charge $500-2,000 per closed deal
2. **Lender referrals** — mortgage lead gen, $50-200 per qualified lead
3. **Premium data** — sell anonymized market insights to agents/brokerages
4. **White-label** — license scoring engine to brokerages

---

## Tech Stack

| Layer | Choice | Why |
|---|---|---|
| Frontend | Next.js 15 + Tailwind + shadcn/ui | Fast, SEO-friendly, great DX |
| Auth | Clerk | Social login + phone auth, free tier |
| Backend API | FastAPI (Python) | Already built, async, fast |
| Database | Supabase (PostgreSQL) | Already using, realtime, auth, storage |
| Queue | Redis + Celery (or BullMQ) | Background ingestion + scoring jobs |
| WhatsApp/SMS | Twilio | Already integrated |
| Email | Resend or SendGrid | Transactional + digest emails |
| Payments | Stripe | Subscriptions + usage billing |
| Hosting | Vercel (frontend) + Railway/Fly.io (backend) | Cheap, auto-scaling |
| Data | MLS IDX feed + Redfin CSV + Craigslist | Start scrappy, add MLS later |
| Monitoring | Sentry + Posthog | Error tracking + product analytics |

---

## Onboarding Flow (Profile Builder)

```
Step 1: BASICS
  "What's your budget?"        → slider $200k - $2M
  "How much can you put down?" → $20k - $500k
  "Which cities?"              → map picker / multi-select

Step 2: STRATEGY
  "What's your plan?"
  ○ House-hack (live in one room/unit, rent the rest)
  ○ Buy & hold rental
  ○ Primary residence (just living there)
  ○ Fix & flip

Step 3: MUST-HAVES (checkboxes)
  □ 3+ bedrooms          □ Swimming pool
  □ 4+ bedrooms          □ Garage / parking
  □ In-law unit / ADU    □ Large lot (5,000+ sqft)
  □ Near BART (< 1 mi)   □ Good schools (7+)
  □ Duplex / multi-unit  □ Low crime area
  □ Yard / outdoor space  □ Year built after 1960

Step 4: ALERTS
  "How do you want to hear from us?"
  ○ WhatsApp daily digest (recommended)
  ○ SMS alerts
  ○ Email digest
  "What time?"  → 8:00 AM / 12:00 PM / 6:00 PM

Step 5: DONE
  "We're scanning 5,000+ listings for you.
   Your first picks arrive tomorrow at 8am. 🏠"
```

---

## Data Access Strategy

### Phase 1: MVP (Now)
- **Redfin CSV imports** (manual or user-uploaded)
- **Craigslist scraping** (already built)
- **Enrichment** (BART distance, geocoding — already built)
- Cost: $0

### Phase 2: Scale (Month 2-3)
- **IDX feed** via brokerage partnership or own RE license ($500 CA license + $50-200/mo MLS dues)
- **Zillow/Mashvisor API** via RapidAPI ($10-50/mo)
- **Walk Score API** ($0.001/request, ~$50/mo at scale)
- Cost: ~$300/mo

### Phase 3: Moat (Month 4+)
- **Direct MLS access** (CRMLS in CA covers most of the state)
- **County assessor data** (zoning, permits, tax history)
- **Rental comps** (Rentometer API or build own from Craigslist data)
- **Permit data** (ADU permits filed — signals neighborhood ADU activity)
- Cost: ~$500-1,000/mo

---

## Go-to-Market

### Week 1-2: Launch MVP
- Deploy backend (you already have the scoring engine)
- Build simple Next.js frontend (profile builder + dashboard)
- WhatsApp daily digest working
- Stripe subscription page

### Week 3-4: Get First 50 Users
- Post on r/realestateinvesting, r/househacking, r/bayarea
- Post on BiggerPockets forums
- Twitter/X thread: "I built an AI that scores every Bay Area listing for house-hackers"
- Product Hunt launch

### Month 2: Iterate
- Add more cities based on demand
- Refine scoring based on user feedback
- Add two-way WhatsApp (reply to save, get details)
- Agent referral partnerships

### Month 3: Monetize
- Launch Pro tier
- Partner with 2-3 local agents for referral revenue
- Add mortgage calculator + lender referrals

---

## Competitive Moat

1. **Personalized scoring** — nobody else does strategy-based ranking
2. **WhatsApp-first** — meet users where they are, not another app to download
3. **House-hack focus** — underserved niche that Zillow/Redfin ignore
4. **Network effects** — more users = better rent estimates, better scoring calibration
5. **Data flywheel** — user engagement data improves the model over time

---

## Immediate Next Steps

1. ✅ Scoring engine (built)
2. ✅ Multi-source ingestion (built)
3. ✅ SMS alerts (built)
4. ✅ BART enrichment (built)
5. ⬜ Add WhatsApp channel to notifier
6. ⬜ Build FastAPI endpoints (profile CRUD, listing feed, score details)
7. ⬜ Build Next.js frontend (onboarding wizard + dashboard)
8. ⬜ Stripe subscription integration
9. ⬜ Deploy to Vercel + Railway
10. ⬜ Launch on ProductHunt + Reddit

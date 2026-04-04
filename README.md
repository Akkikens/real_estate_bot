<p align="center">
  <img src="https://img.shields.io/badge/python-3.11%2B-blue?logo=python" alt="Python" />
  <img src="https://img.shields.io/badge/Next.js-16-black?logo=next.js" alt="Next.js" />
  <img src="https://img.shields.io/badge/FastAPI-0.115-009688?logo=fastapi" alt="FastAPI" />
  <img src="https://img.shields.io/badge/license-MIT-green" alt="License" />
</p>

# 🏠 HouseMatch — AI-Powered Property Intelligence

> **Stop scrolling Redfin for hours.** Get every listing scored 0–100 against your exact strategy — budget, house-hack potential, ADU upside, transit access, and more — delivered to your phone daily.

HouseMatch is a **strategy-first property search engine** built for house-hackers and small real estate investors. It ingests listings from multiple sources, scores them across 8 dimensions using configurable AI-driven analysis, and pushes daily top picks via WhatsApp, SMS, or email.

---

## ✨ What Makes This Special

| Feature | Zillow/Redfin | HouseMatch |
|---|---|---|
| **Scoring** | Generic "Zestimate" | 8-dimension strategy-specific scoring |
| **House-hack analysis** | ❌ | ✅ Room rental, PITI offset, cash flow |
| **ADU detection** | ❌ | ✅ Keywords + lot size + zoning signals |
| **Transit scoring** | Basic walk score | BART/transit distance + commute corridor bonuses |
| **Underwriting** | ❌ | ✅ Full mortgage + house-hack + appreciation scenarios |
| **Price drop alerts** | Email only | WhatsApp + SMS + Email + Telegram |
| **Multi-source** | Single source | Redfin + Zillow + Realtor.com + Craigslist |
| **Market portable** | N/A | Config-driven: add any US market in ~50 lines |

---

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    FRONTEND (Next.js 16)                      │
│  Landing · Onboard Wizard · Dashboard · Property Detail      │
│  Watchlist · Settings · Score Breakdown                      │
└───────────────────────┬─────────────────────────────────────┘
                        │  REST API
┌───────────────────────▼─────────────────────────────────────┐
│                  BACKEND (FastAPI + Python)                    │
│                                                               │
│  ┌──────────────┐  ┌────────────┐  ┌──────────────────────┐ │
│  │ Ingestion    │  │ Scoring    │  │ Alerts & Outreach    │ │
│  │ Pipeline     │  │ Engine     │  │ (SMS/WA/Email/TG)    │ │
│  │ 4 adapters   │  │ 8 dims     │  │                      │ │
│  └──────────────┘  └────────────┘  └──────────────────────┘ │
│                                                               │
│  ┌──────────────┐  ┌────────────┐  ┌──────────────────────┐ │
│  │ Enrichment   │  │ Under-     │  │ CRM / Outreach       │ │
│  │ (geocode,    │  │ writing    │  │ Tracker              │ │
│  │  transit)    │  │ Calculator │  │                      │ │
│  └──────────────┘  └────────────┘  └──────────────────────┘ │
└───────────────────────┬─────────────────────────────────────┘
                        │
┌───────────────────────▼─────────────────────────────────────┐
│              SQLite / PostgreSQL + Alembic Migrations         │
└─────────────────────────────────────────────────────────────┘
```

---

## 🚀 Quick Start

### 1. Clone & Install

```bash
git clone https://github.com/akshaykalapgar/real_estate_bot.git
cd real_estate_bot

# Python backend
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt

# Frontend
cd frontend && npm install && cd ..
```

### 2. Configure

```bash
cp .env.example .env
# Edit .env with your API keys, alert settings, etc.
```

### 3. Run

```bash
# API server (serves the frontend data)
uvicorn api.main:app --reload --port 8000

# Frontend (in another terminal)
cd frontend && npm run dev

# Or use the CLI directly:
python main.py ingest --source redfin
python main.py list --limit 10
python main.py show <property-id> --underwrite
```

### Docker (one command)

```bash
docker compose up --build
# API:      http://localhost:8000
# Frontend: http://localhost:3000
# API docs: http://localhost:8000/docs
```

---

## 📊 Scoring System (8 Dimensions)

Every property is scored 0–100 using weighted dimensions from `config/scoring_weights.yaml`:

| Dimension | Weight | What It Measures |
|---|---|---|
| **Price Fit** | 25% | How well the price fits your budget |
| **House-Hack Potential** | 20% | Bedrooms, separate entrance, duplex signals |
| **Rental Income** | 15% | Estimated rent vs. PITI coverage ratio |
| **ADU Upside** | 15% | Lot size, ADU keywords, SB9 potential |
| **Transit Access** | 10% | Distance to BART/transit + commute corridor |
| **Neighborhood** | 5% | Schools, crime, walkability |
| **Deal Opportunity** | 5% | Price drops, DOM, motivated seller signals |
| **Lot Expansion** | 5% | Raw lot size and building coverage ratio |

Plus a **complexity penalty** (0–15 pts) for risk signals like fire damage, foundation issues, etc.

---

## 💰 Underwriting Calculator

For any property, get instant financial analysis:

- **Monthly costs**: P&I, tax, insurance, PMI, HOA, maintenance
- **House-hack scenarios**: Room rental at low/mid/high market rates
- **Full rental analysis**: Whole-property rent vs. expenses
- **Cash to close**: Down payment + closing costs + 3-month reserves
- **5-year appreciation**: Conservative (2%), moderate (4%), optimistic (6%)
- **Verdict**: Plain-English "good first property?" assessment

```bash
python main.py underwrite <property-id>
```

---

## 🌎 Multi-Market Support

The system is fully market-portable via `config/market.py`. Each market defines:
- Transit stations (BART, Metro, Subway, etc.)
- City price floors, safety scores, grocery walkability
- Redfin region IDs, Realtor.com slugs, Craigslist URLs
- Property tax rates, closing costs, rent-to-price ratios

```python
# To add a new market:
# 1. Create a MarketConfig in config/market.py
# 2. Set MARKET_ID=your_market in .env
```

Currently supported: **SF Bay Area (East Bay)**. Adding Austin, Denver, Phoenix next.

---

## 🔔 Alert Channels

| Channel | Setup | Status |
|---|---|---|
| Email (SMTP) | Gmail app password | ✅ Working |
| SMS (Twilio) | Twilio account | ✅ Working |
| WhatsApp (Twilio) | WhatsApp Business | ✅ Working |
| Telegram | Bot token + chat ID | ✅ Working |
| Console | Always on | ✅ Working |

---

## 🛠️ API Reference

Start the server and visit `http://localhost:8000/docs` for interactive Swagger docs.

| Endpoint | Method | Description |
|---|---|---|
| `/api/v1/properties` | GET | Paginated feed with filters & sorting |
| `/api/v1/properties/{id}` | GET | Full detail + score breakdown |
| `/api/v1/properties/{id}/underwrite` | GET | Financial underwriting |
| `/api/v1/stats` | GET | Dashboard statistics |
| `/api/v1/watchlist` | GET | Saved properties |
| `/api/v1/watchlist/{id}` | POST/DELETE | Add/remove from watchlist |
| `/api/v1/price-drops` | GET | Recent price reductions |
| `/api/v1/health` | GET | Health check |

---

## 📁 Project Structure

```
real_estate_bot/
├── api/                    # FastAPI REST API
│   └── main.py             # Endpoints, schemas, CORS
├── config/
│   ├── settings.py         # All env-based configuration
│   ├── market.py           # Market-specific config (transit, pricing, etc.)
│   ├── logging.py          # Centralized logging setup
│   └── scoring_weights.yaml
├── database/
│   ├── models.py           # SQLAlchemy ORM models
│   └── db.py               # Engine, session factory, init
├── ingestion/
│   ├── base.py             # SourceAdapter ABC with retry logic
│   ├── redfin_adapter.py   # Redfin CSV/GIS endpoint
│   ├── zillow_adapter.py   # Zillow via RapidAPI
│   ├── realtor_adapter.py  # Realtor.com web + RapidAPI
│   ├── craigslist_adapter.py
│   ├── enrichment.py       # Geocoding + transit distance
│   ├── normalizer.py       # Schema normalization + dedup
│   ├── sanity.py           # Data quality checks
│   └── registry.py         # Adapter factory
├── scoring/
│   ├── engine.py           # 8-dimension scoring engine
│   └── rental_scorer.py    # Rental-specific scoring
├── underwriting/
│   └── calculator.py       # Full financial underwriting
├── alerts/
│   └── notifier.py         # Multi-channel alert system
├── outreach/
│   └── templates.py        # Agent outreach email templates
├── crm/
│   └── tracker.py          # CRM: drafts, follow-ups, replies
├── reports/
│   └── generator.py        # Daily/weekly digest reports
├── dashboard/
│   └── cli.py              # Rich CLI (Typer + Rich)
├── frontend/               # Next.js 16 + Tailwind + shadcn/ui
│   └── src/
│       ├── app/            # Pages: landing, dashboard, detail, onboard
│       └── components/     # PropertyCard, ScoreRing, ScoreBars, etc.
├── tests/                  # pytest suite (scoring, underwriting, API)
├── migrations/             # Alembic database migrations
├── scheduler.py            # APScheduler background jobs
├── main.py                 # CLI entry point
├── Dockerfile
├── docker-compose.yml
└── .github/workflows/ci.yml
```

---

## 🧪 Testing

```bash
# Run all tests
pytest tests/ -v

# Run specific test suite
pytest tests/test_api.py -v          # API endpoints
pytest tests/test_scoring.py -v      # Scoring engine
pytest tests/test_underwriting.py -v # Financial calculations
pytest tests/test_rental_scorer.py -v

# Validate business logic
python validate_logic.py
```

---

## 📋 CLI Commands

```bash
python main.py ingest --source all          # Ingest from all sources
python main.py ingest --source redfin       # Redfin only
python main.py score                        # Re-score all properties
python main.py list --limit 20              # Top 20 by score
python main.py list --adu-only              # ADU candidates only
python main.py show <id> --underwrite       # Property detail + underwriting
python main.py report                       # Generate daily report
python main.py alerts                       # Check and send alerts
python main.py add --address "123 Main St" --city Oakland --price 650000 --beds 4
```

---

## 🗺️ Roadmap

- [ ] Stripe subscription integration (Free / Pro / Investor tiers)
- [ ] Two-way WhatsApp conversation (reply "1" for details, "SAVE" for watchlist)
- [ ] Walk Score API integration
- [ ] Comparable sales / rental comps
- [ ] CSV/PDF export for underwriting reports
- [ ] Additional markets: Austin, Denver, Phoenix, Atlanta
- [ ] MLS IDX feed integration
- [ ] County assessor data (permits, zoning)

---

## 📄 License

MIT — built by [Akshay Kalapgar](https://github.com/akshaykalapgar).

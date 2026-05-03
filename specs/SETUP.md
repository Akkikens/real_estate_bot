# Bay Area Property Acquisition Bot — Setup Guide

## What this is

A local-first, modular property acquisition system built for Akshay. It:
- Pulls listings from Redfin (and mock data for testing)
- Scores every property 0–100 against your house-hack / ADU / value-add strategy
- Runs full financial underwriting for each deal
- Alerts you when strong matches appear
- Drafts professional agent outreach
- Tracks conversations in a CRM
- Generates daily reports

---

## Quick Start (5 minutes)

### 1. Install dependencies

```bash
cd real_estate_bot
pip install -r requirements.txt
```

> **Python 3.10+ required.** Tested on Python 3.11.

### 2. Set up configuration

```bash
cp .env.example .env
# Edit .env to set your preferences (or leave defaults for mock testing)
```

### 3. Run with mock data (no network needed)

```bash
# Full pipeline: ingest mock listings → score → report
python main.py run --source mock

# Or step by step:
python main.py ingest --source mock    # Load 80 synthetic Bay Area listings
python main.py report                  # See ranked opportunities
python main.py list --min-score 70     # Filter to strong matches only
```

### 4. Explore a specific property

```bash
python main.py show "Macdonald"        # Any address fragment works
python main.py show "Richmond"         # Shows top match in Richmond
```

---

## All CLI Commands

| Command | What it does |
|---------|-------------|
| `python main.py run` | Full pipeline (ingest → score → alert → report) |
| `python main.py ingest --source mock` | Pull mock listings |
| `python main.py ingest --source redfin` | Pull real Redfin listings |
| `python main.py ingest --source all` | Both sources |
| `python main.py score` | Re-score all properties |
| `python main.py list` | List properties (filterable) |
| `python main.py list --min-score 70 --adu` | ADU candidates, score 70+ |
| `python main.py list --city Richmond --min-beds 3` | Richmond 3BR+ |
| `python main.py show "123 Main"` | Full detail + underwriting |
| `python main.py underwrite "123 Main"` | Financial analysis only |
| `python main.py underwrite "123 Main" --down 70000` | With custom down payment |
| `python main.py draft "123 Main"` | Draft initial agent outreach |
| `python main.py draft "123 Main" --type followup` | Follow-up email |
| `python main.py draft "123 Main" --type disclosure` | Request disclosures |
| `python main.py crm` | CRM status + follow-ups due |
| `python main.py watch "123 Main"` | Watch a property for changes |
| `python main.py archive "123 Main"` | Hide from reports |
| `python main.py report` | Full daily digest |

---

## Enable Real Redfin Data

1. The Redfin adapter uses their publicly-visible search API (no auth required).
2. **Review Redfin's ToS before use.** This is for personal research only.
3. Add or update city region IDs in `ingestion/redfin_adapter.py` if needed.
4. Run: `python main.py ingest --source redfin`

---

## Enable Email Alerts

Edit `.env`:
```
ALERT_EMAIL_ENABLED=true
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=your_email@gmail.com
SMTP_PASS=your_app_password      # Use a Gmail App Password, not your login password
ALERT_TO_EMAIL=akshaykalapgar23@gmail.com
ALERT_SCORE_THRESHOLD=65          # Only alert on properties scoring 65+
```

Gmail App Passwords: https://myaccount.google.com/apppasswords

---

## Enable SMS Alerts (optional)

1. Sign up for Twilio (free trial)
2. Set in `.env`:
```
SMS_ENABLED=true
TWILIO_ACCOUNT_SID=...
TWILIO_AUTH_TOKEN=...
TWILIO_FROM_NUMBER=+1...
ALERT_TO_PHONE=+1...
```

---

## Run the Continuous Monitor (Scheduler)

This runs 24/7, checking for new listings every 4 hours:

```bash
python scheduler.py

# Or run once:
python scheduler.py --once
```

**With Docker:**
```bash
docker-compose up -d      # Starts continuous scheduler
docker-compose logs -f    # View logs
```

---

## Configure Outreach Mode

In `.env`:
```
OUTREACH_MODE=draft       # Just create drafts (safest, default)
OUTREACH_MODE=approve     # Draft + show for your approval before send
OUTREACH_MODE=auto        # Auto-send first-touch (use carefully)
```

---

## Tune the Scoring Weights

Edit `config/scoring_weights.yaml`:

```yaml
weights:
  price_fit:            0.20   # Raise if budget is your #1 constraint
  house_hack_potential: 0.20   # Raise if you definitely want to house-hack
  rental_income:        0.15
  adu_upside:           0.12   # Raise as ADU legislation improves
  transit_access:       0.10
  neighborhood:         0.08
  deal_opportunity:     0.10   # Raise in a slow market
  lot_expansion:        0.05
```

After editing, re-run: `python main.py score` to apply new weights.

---

## Database

- Default: SQLite at `./real_estate.db` (portable, no setup needed)
- For production/multi-user: set `DATABASE_URL=postgresql://...` in `.env`
- View data directly: `sqlite3 real_estate.db`

---

## Add More Cities

In `ingestion/redfin_adapter.py`, add to `REDFIN_CITY_REGION_IDS`:

```python
"Vallejo": 17456,   # example
```

Or use the lookup helper in Python:
```python
from ingestion.redfin_adapter import RedfinAdapter
adapter = RedfinAdapter()
region_id = adapter.lookup_region_id("Vallejo", "CA")
print(region_id)
```

---

## Day-to-Day Operating Playbook

**Every morning:**
```bash
python main.py run           # Fresh data + report
python main.py crm           # Any follow-ups due?
```

**When a listing catches your eye:**
```bash
python main.py show "address fragment"    # Full analysis
python main.py underwrite "address" --down 60000   # Adjust down payment
python main.py draft "address"            # Draft outreach to agent
python main.py watch "address"            # Watch for price drops
```

**Weekly:**
```bash
python main.py report        # Full digest
python main.py list --min-score 75 --adu  # Best ADU candidates
python main.py list --min-score 75 --min-beds 4  # Best house-hacks
```

---

## Running Tests

```bash
# Full test suite (requires all deps installed)
pytest tests/ -v

# Or just the logic validator (works with minimal deps)
python validate_logic.py
```

---

## Architecture Overview

```
real_estate_bot/
├── main.py               ← Entry point (all CLI commands)
├── scheduler.py          ← Continuous monitor (4h ingest cycle)
├── validate_logic.py     ← Standalone logic tests
│
├── config/
│   ├── settings.py       ← All settings (reads from .env)
│   └── scoring_weights.yaml  ← Tunable weights + keyword lists
│
├── database/
│   ├── models.py         ← Property, PriceHistory, Underwriting, Outreach, Alert
│   └── db.py             ← Engine, sessions, init_db()
│
├── ingestion/
│   ├── base.py           ← Abstract SourceAdapter (rate limiting, headers)
│   ├── mock_adapter.py   ← Synthetic data (testing, no network needed)
│   ├── redfin_adapter.py ← Redfin GIS search API
│   └── normalizer.py     ← Canonical schema + upsert logic
│
├── scoring/
│   └── engine.py         ← 8-dimension weighted scoring + explainer
│
├── underwriting/
│   └── calculator.py     ← PITI, house-hack, room-rental, appreciation scenarios
│
├── outreach/
│   └── templates.py      ← 5 email templates (initial, followup, disclosure, etc.)
│
├── crm/
│   └── tracker.py        ← Draft/send tracking, follow-up reminders
│
├── alerts/
│   └── notifier.py       ← Email/SMS/Telegram with rate limiting
│
├── reports/
│   └── generator.py      ← Top 10, price drops, ADU, house-hack, traps
│
└── dashboard/
    └── cli.py            ← All Typer + Rich CLI commands
```

---

## Key Numbers (based on your profile)

| Metric | Value |
|--------|-------|
| Max budget | $750,000 |
| Down payment | ~$55,000 |
| Mortgage rate assumed | 7.25% (update in .env) |
| Property tax rate | 1.25%/yr (Alameda/Contra Costa avg) |
| Alert threshold | Score 65+ |
| Room rental estimate | $1,000–$1,800/mo |
| Ingest frequency | Every 4 hours (continuous mode) |

---

## Compliance Notes

- Redfin adapter: personal research use only. Respect Redfin's ToS.
- Rate limiting: default 3s delay between Redfin requests.
- Outreach: default mode is "draft" — nothing sends without you reviewing it.
- All data stays local (SQLite) — no data leaves your machine.
- Rents, zoning, and permit status are estimated / labeled as unverified. Always confirm before offering.

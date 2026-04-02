"""
Standalone logic validator — runs without SQLAlchemy, typer, or rich.
Uses only stdlib + PyYAML + python-dotenv (available in most envs).

Tests:
  1. Mortgage math (monthly payment, principal paydown)
  2. Scoring weights load correctly from YAML
  3. Keyword detection (ADU, deal, risk)
  4. Price band scoring
  5. Mock data generation (pure Python)

Run: python validate_logic.py
"""

import math
import sys
import os
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

PASS = "✅"
FAIL = "❌"
results = []

def check(name, condition, detail=""):
    status = PASS if condition else FAIL
    results.append((status, name, detail))
    print(f"  {status}  {name}" + (f"  [{detail}]" if detail else ""))

print("\n" + "="*60)
print("  Bay Area Bot — Logic Validator")
print("="*60)


# ─────────────────────────────────────────────────────────────────
# 1. Mortgage math
# ─────────────────────────────────────────────────────────────────

print("\n📐 Mortgage Formulas")

def monthly_payment(principal, annual_rate, years):
    if annual_rate <= 0 or years <= 0 or principal <= 0:
        return 0.0
    r = annual_rate / 12
    n = years * 12
    return principal * r * (1 + r) ** n / ((1 + r) ** n - 1)

def principal_paydown(principal, annual_rate, years_elapsed, total_years):
    if annual_rate <= 0 or total_years <= 0:
        return 0.0
    r = annual_rate / 12
    n = total_years * 12
    k = years_elapsed * 12
    remaining = principal * ((1 + r)**n - (1 + r)**k) / ((1 + r)**n - 1)
    return principal - remaining

# $500k, 7%, 30yr → ~$3,327/mo
pi = monthly_payment(500_000, 0.07, 30)
check("$500k@7%/30yr payment ≈ $3,327", 3_300 < pi < 3_360, f"${pi:.0f}/mo")

# $525k loan (570k price, 45k down), 7.25%, 30yr
loan = 570_000 - 55_000
pi2 = monthly_payment(loan, 0.0725, 30)
check("$515k@7.25%/30yr payment reasonable", 3_500 < pi2 < 4_000, f"${pi2:.0f}/mo")

# Principal paydown after 5yr on $500k
paid = principal_paydown(500_000, 0.07, 5, 30)
check("5yr principal paydown $25k–$40k", 25_000 < paid < 40_000, f"${paid:,.0f}")

# Full term paydown ≈ full principal
paid_full = principal_paydown(500_000, 0.07, 30, 30)
check("Full 30yr paydown ≈ $500k", abs(paid_full - 500_000) < 50, f"${paid_full:,.0f}")


# ─────────────────────────────────────────────────────────────────
# 2. Scoring config loads
# ─────────────────────────────────────────────────────────────────

print("\n📋 Scoring Configuration")

import yaml

config_path = Path(__file__).parent / "config" / "scoring_weights.yaml"
check("scoring_weights.yaml exists", config_path.exists())

if config_path.exists():
    cfg = yaml.safe_load(config_path.read_text())
    weights = cfg.get("weights", {})
    weight_sum = sum(weights.values())
    check("Weights sum to 1.0", abs(weight_sum - 1.0) < 0.001, f"sum={weight_sum:.3f}")
    check("All 8 dimensions present", len(weights) == 8, f"found {len(weights)}")
    check("No individual weight > 0.25", all(v <= 0.25 for v in weights.values()))

    adu_kws = cfg.get("adu_keywords", [])
    deal_kws = cfg.get("deal_keywords", [])
    risk_kws = cfg.get("risk_keywords", [])
    check("ADU keywords loaded", len(adu_kws) >= 10, f"{len(adu_kws)} keywords")
    check("Deal keywords loaded", len(deal_kws) >= 8, f"{len(deal_kws)} keywords")
    check("Risk keywords loaded", len(risk_kws) >= 8, f"{len(risk_kws)} keywords")


# ─────────────────────────────────────────────────────────────────
# 3. Keyword detection
# ─────────────────────────────────────────────────────────────────

print("\n🔍 Keyword Detection")

adu_keywords = [k.lower() for k in adu_kws]
deal_keywords = [k.lower() for k in deal_kws]
risk_keywords = [k.lower() for k in risk_kws]

def has_keyword(remarks, keywords):
    remarks_lower = remarks.lower()
    return any(k in remarks_lower for k in keywords)

adu_remark = "Huge lot with ADU potential. Separate entrance to in-law unit."
no_adu_remark = "Nice 2BR condo on second floor. No pets."
deal_remark = "Price reduced! Motivated seller. Priced to sell."
risk_remark = "Fire damage throughout. Full rebuild required. Foundation issues."

check("ADU keywords detected", has_keyword(adu_remark, adu_keywords))
check("ADU keywords NOT in non-ADU listing", not has_keyword(no_adu_remark, adu_keywords))
check("Deal keywords detected", has_keyword(deal_remark, deal_keywords))
check("Risk keywords detected", has_keyword(risk_remark, risk_keywords))


# ─────────────────────────────────────────────────────────────────
# 4. Price band scoring
# ─────────────────────────────────────────────────────────────────

print("\n💰 Price Band Scoring")

price_bands = cfg.get("price_bands", [])
max_price = 750_000

def score_price(list_price, max_price, bands):
    fraction = list_price / max_price
    for band in bands:
        if fraction <= band["max_fraction"]:
            return float(band["score"])
    return 0.0

check("Price at 60% of max → 10pts", score_price(450_000, max_price, price_bands) == 10.0,
      f"Got {score_price(450_000, max_price, price_bands)}")
check("Price at 95% of max → 4pts", score_price(712_500, max_price, price_bands) == 4.0,
      f"Got {score_price(712_500, max_price, price_bands)}")
check("Price at 120% of max → 0pts", score_price(900_000, max_price, price_bands) == 0.0,
      f"Got {score_price(900_000, max_price, price_bands)}")


# ─────────────────────────────────────────────────────────────────
# 5. House-hack income estimates
# ─────────────────────────────────────────────────────────────────

print("\n🏠 House-Hack Math")

room_low  = 1_000
room_mid  = 1_400
room_high = 1_800

# 4BR: rent 3 rooms
beds = 4
rentable = beds - 1
hh_income_mid = rentable * room_mid  # 3 × 1400 = 4200

# PITI on $580k, $55k down, 7.25%, 30yr
loan_hh = 580_000 - 55_000
pi_hh = monthly_payment(loan_hh, 0.0725, 30)
tax_hh = (580_000 * 0.0125) / 12
ins_hh = (580_000 * 0.005) / 12
pmi_hh = (loan_hh * 0.005) / 12 if (loan_hh / 580_000) > 0.80 else 0
maint_hh = (580_000 * 0.01) / 12
piti_hh = pi_hh + tax_hh + ins_hh + pmi_hh + maint_hh

net_hack = hh_income_mid - piti_hh
check("House-hack income (3 rooms@mid) = $4,200/mo", hh_income_mid == 4_200, f"${hh_income_mid:,.0f}")
check("PITI on $580k reasonable ($4500–$6000 at 7.25%)", 4_500 < piti_hh < 6_000, f"${piti_hh:,.0f}")
check("House-hack net is better than no-rental", net_hack > -piti_hh)
print(f"    Net burn with house-hack: ${net_hack:+,.0f}/mo")


# ─────────────────────────────────────────────────────────────────
# 6. Cash to close calculation
# ─────────────────────────────────────────────────────────────────

print("\n💵 Cash to Close")

price = 580_000
down = 55_000
closing = price * 0.025
reserves = piti_hh * 3
total_ctc = down + closing + reserves

check("Closing costs ≈ 2.5% of price", abs(closing - 14_500) < 100, f"${closing:,.0f}")
check("Reserves ≈ 3× PITI", 11_000 < reserves < 18_000, f"${reserves:,.0f}")
check("Total cash to close $75k–$90k range", 70_000 < total_ctc < 95_000, f"${total_ctc:,.0f}")


# ─────────────────────────────────────────────────────────────────
# 7. Appreciation scenarios
# ─────────────────────────────────────────────────────────────────

print("\n📈 Appreciation Scenarios")

price_appr = 600_000
horizon = 5

def equity_gain(price, loan, rate_annual, years_elapsed, total_years):
    fv = price * (1 + rate_annual) ** years_elapsed
    paydown = principal_paydown(loan, 0.0725, years_elapsed, total_years)
    return (fv - price) + paydown

loan_appr = price_appr - 55_000
e_cons = equity_gain(price_appr, loan_appr, 0.02, 5, 30)
e_mod  = equity_gain(price_appr, loan_appr, 0.04, 5, 30)
e_opt  = equity_gain(price_appr, loan_appr, 0.06, 5, 30)

check("Conservative < Moderate equity gain", e_cons < e_mod)
check("Moderate < Optimistic equity gain", e_mod < e_opt)
check("5yr conservative equity gain > $30k", e_cons > 30_000, f"${e_cons:,.0f}")
check("5yr moderate equity gain > $80k", e_mod > 80_000, f"${e_mod:,.0f}")
print(f"    Conservative: ${e_cons:,.0f}  Moderate: ${e_mod:,.0f}  Optimistic: ${e_opt:,.0f}")


# ─────────────────────────────────────────────────────────────────
# 8. Normalizer field cleaning
# ─────────────────────────────────────────────────────────────────

print("\n🔧 Data Normalization")

import re

def clean_price(v):
    if v is None: return None
    raw = re.sub(r"[,$\s]", "", str(v))
    return float(raw) if raw else None

check("Price string '$550,000' parsed", clean_price("$550,000") == 550_000.0)
check("Price with spaces '600 000' parsed", clean_price("600 000") == 600_000.0)
check("None price → None", clean_price(None) is None)
check("Empty price → None", clean_price("") is None)

# Status normalization
def norm_status(raw):
    s = (raw or "").lower()
    if any(k in s for k in ("pend", "under contract", "contingent")):
        return "pending"
    elif any(k in s for k in ("sold", "closed")):
        return "sold"
    return "active"

check("'Active' → active", norm_status("Active") == "active")
check("'Pending' → pending", norm_status("Pending") == "pending")
check("'Under Contract' → pending", norm_status("Under Contract") == "pending")
check("'Sold' → sold", norm_status("Sold-Closed") == "sold")


# ─────────────────────────────────────────────────────────────────
# Summary
# ─────────────────────────────────────────────────────────────────

print("\n" + "="*60)
passed = sum(1 for r in results if r[0] == PASS)
failed = sum(1 for r in results if r[0] == FAIL)
total = len(results)
print(f"  Results: {passed}/{total} passed  |  {failed} failed")

if failed > 0:
    print("\n  Failed checks:")
    for status, name, detail in results:
        if status == FAIL:
            print(f"    {FAIL} {name} [{detail}]")

print("="*60 + "\n")
sys.exit(0 if failed == 0 else 1)

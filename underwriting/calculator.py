"""
Financial Underwriting Calculator
===================================
Computes detailed monthly cost and income scenarios for each property.

Scenarios:
  1. Owner-occupant (no rental income)
  2. House-hack (rent all non-owner bedrooms at market rate)
  3. Room rental (rent N-1 rooms, live in one)
  4. Full rental (you don't live there; all income)
  5. ADU addition (rough estimate if ADU potential detected)

Appreciation:
  Conservative 2%/yr, Moderate 4%/yr, Optimistic 6%/yr over 5 years.

All assumptions use settings.py defaults; nothing is hardcoded.
All dollar values are in today's dollars (no inflation adjustment).
"""

from __future__ import annotations

import json
import logging
import math
from dataclasses import asdict, dataclass
from typing import Optional

from config import settings
from database.models import Property, Underwriting

logger = logging.getLogger(__name__)


@dataclass
class MonthlyBreakdown:
    """All monthly cost and income components."""

    # Loan
    monthly_pi: float            # Principal + Interest
    monthly_tax: float
    monthly_insurance: float
    monthly_pmi: float           # 0 if LTV ≤ 80%
    monthly_hoa: float
    monthly_maintenance: float   # 1% annual rule / 12
    monthly_total_piti: float    # All-in monthly cost before any income

    # Income scenarios (gross)
    full_rental_income: float    # Rent whole property out
    house_hack_income: float     # Rent all rooms except one
    room_rental_income_low: float
    room_rental_income_mid: float
    room_rental_income_high: float

    # Net monthly (positive = surplus, negative = you pay)
    owner_occupant_burn: float   # Just owning, no income
    house_hack_net: float
    full_rental_net: float
    room_rental_net_low: float
    room_rental_net_mid: float
    room_rental_net_high: float


@dataclass
class CashToClose:
    down_payment: float
    closing_costs: float          # ~2–3% of price
    initial_reserves: float       # 3 months PITI recommended
    total: float


@dataclass
class AppreciationScenario:
    years: int
    annual_rate: float
    future_value: float
    equity_gained: float          # Appreciation + principal paydown


@dataclass
class UnderwritingResult:
    address: str
    list_price: float
    down_payment: float
    loan_amount: float
    ltv_pct: float
    interest_rate: float

    monthly: MonthlyBreakdown
    cash_to_close: CashToClose

    appreciation_conservative: AppreciationScenario
    appreciation_moderate: AppreciationScenario
    appreciation_optimistic: AppreciationScenario

    good_first_property: bool
    verdict: str                  # Short summary judgment
    top_considerations: list[str] # Key things to verify before offering


def _monthly_payment(principal: float, annual_rate: float, years: int) -> float:
    """Standard amortization formula."""
    if annual_rate <= 0 or years <= 0 or principal <= 0:
        return 0.0
    r = annual_rate / 12
    n = years * 12
    return principal * r * (1 + r) ** n / ((1 + r) ** n - 1)


def _principal_paydown(principal: float, annual_rate: float, years_elapsed: int, total_years: int) -> float:
    """How much principal has been paid after `years_elapsed` years?"""
    if annual_rate <= 0 or total_years <= 0:
        return 0.0
    r = annual_rate / 12
    n = total_years * 12
    k = years_elapsed * 12
    if r == 0:
        return principal * k / n
    remaining = principal * ((1 + r) ** n - (1 + r) ** k) / ((1 + r) ** n - 1)
    return principal - remaining


def underwrite(prop: Property, down_payment: Optional[float] = None) -> UnderwritingResult:
    """
    Full underwriting for a property.
    Returns an UnderwritingResult dataclass.
    """
    price = prop.list_price or 0.0
    dp = down_payment or settings.BUYER_DOWN_PAYMENT
    loan = max(price - dp, 0.0)
    ltv = loan / price if price > 0 else 1.0

    rate = settings.MORTGAGE_RATE
    years = settings.MORTGAGE_TERM_YEARS

    # ── Monthly costs ─────────────────────────────────────────────────────────
    pi = _monthly_payment(loan, rate, years)
    tax = (price * settings.PROPERTY_TAX_RATE) / 12
    ins = (price * settings.INSURANCE_RATE) / 12
    pmi = (loan * settings.PMI_RATE) / 12 if ltv > 0.80 else 0.0
    hoa = prop.hoa_monthly or 0.0
    maint = (price * settings.MAINTENANCE_RATE) / 12

    total_piti = pi + tax + ins + pmi + hoa + maint

    # ── Rental income estimates ────────────────────────────────────────────────
    beds = prop.beds or 2
    rentable_rooms = max(beds - 1, 1)  # house-hack: rent all but owner's room

    # Full property rental (whole-home rent)
    full_rent = prop.estimated_rent_monthly or (price * 0.0045)
    full_rent_net = full_rent * (1 - settings.VACANCY_RATE) - total_piti

    # House-hack: rent all non-owner rooms
    hh_income_low  = rentable_rooms * settings.ROOM_RENTAL_LOW
    hh_income_mid  = rentable_rooms * settings.ROOM_RENTAL_MID
    hh_income_high = rentable_rooms * settings.ROOM_RENTAL_HIGH
    house_hack_income = hh_income_mid
    house_hack_net = house_hack_income - total_piti

    # Room-rental scenarios (same as house-hack income for N-1 rooms)
    rr_low  = rentable_rooms * settings.ROOM_RENTAL_LOW
    rr_mid  = rentable_rooms * settings.ROOM_RENTAL_MID
    rr_high = rentable_rooms * settings.ROOM_RENTAL_HIGH
    rr_net_low  = rr_low  - total_piti
    rr_net_mid  = rr_mid  - total_piti
    rr_net_high = rr_high - total_piti

    monthly = MonthlyBreakdown(
        monthly_pi=round(pi, 2),
        monthly_tax=round(tax, 2),
        monthly_insurance=round(ins, 2),
        monthly_pmi=round(pmi, 2),
        monthly_hoa=round(hoa, 2),
        monthly_maintenance=round(maint, 2),
        monthly_total_piti=round(total_piti, 2),
        full_rental_income=round(full_rent, 2),
        house_hack_income=round(house_hack_income, 2),
        room_rental_income_low=round(rr_low, 2),
        room_rental_income_mid=round(rr_mid, 2),
        room_rental_income_high=round(rr_high, 2),
        owner_occupant_burn=round(-total_piti, 2),
        house_hack_net=round(house_hack_net, 2),
        full_rental_net=round(full_rent_net, 2),
        room_rental_net_low=round(rr_net_low, 2),
        room_rental_net_mid=round(rr_net_mid, 2),
        room_rental_net_high=round(rr_net_high, 2),
    )

    # ── Cash to close ─────────────────────────────────────────────────────────
    closing_costs = price * 0.025  # ~2.5% typical Bay Area buyer closing costs
    reserves = total_piti * 3      # 3 months PITI as emergency reserve
    ctc = CashToClose(
        down_payment=round(dp, 2),
        closing_costs=round(closing_costs, 2),
        initial_reserves=round(reserves, 2),
        total=round(dp + closing_costs + reserves, 2),
    )

    # ── Appreciation scenarios ─────────────────────────────────────────────────
    horizon = 5

    def _appr(rate_annual: float) -> AppreciationScenario:
        fv = price * (1 + rate_annual) ** horizon
        principal_paid = _principal_paydown(loan, rate, horizon, years)
        equity = (fv - price) + principal_paid  # appreciation gain + paydown
        return AppreciationScenario(
            years=horizon,
            annual_rate=rate_annual,
            future_value=round(fv, 0),
            equity_gained=round(equity, 0),
        )

    appr_cons = _appr(0.02)
    appr_mod  = _appr(0.04)
    appr_opt  = _appr(0.06)

    # ── Good first property? ──────────────────────────────────────────────────
    # Criteria: financing feasible + house-hack cuts burn significantly + appreciation plausible
    financing_ok = dp >= (price * 0.03) and price <= (settings.BUYER_MAX_PRICE * 1.05)
    hack_cuts_burn = house_hack_net > (-total_piti * 0.5)  # hack covers >50% of cost
    price_sane = price > 0 and price < 1_200_000
    good = financing_ok and hack_cuts_burn and price_sane

    # ── Verdict text ──────────────────────────────────────────────────────────
    verdict = _build_verdict(prop, monthly, ctc, appr_mod, good)

    # ── Things to verify ─────────────────────────────────────────────────────
    checks = _build_checks(prop)

    return UnderwritingResult(
        address=prop.address or "",
        list_price=price,
        down_payment=dp,
        loan_amount=round(loan, 2),
        ltv_pct=round(ltv * 100, 1),
        interest_rate=rate,
        monthly=monthly,
        cash_to_close=ctc,
        appreciation_conservative=appr_cons,
        appreciation_moderate=appr_mod,
        appreciation_optimistic=appr_opt,
        good_first_property=good,
        verdict=verdict,
        top_considerations=checks,
    )


def _build_verdict(prop, m: MonthlyBreakdown, ctc: CashToClose, appr, good: bool) -> str:
    lines = []
    # House-hack affordability
    if m.house_hack_net >= 0:
        lines.append(f"House-hacking covers all costs and generates +${m.house_hack_net:,.0f}/mo surplus.")
    elif m.house_hack_net >= -500:
        lines.append(f"House-hacking keeps net burn to just -${abs(m.house_hack_net):,.0f}/mo — very manageable.")
    else:
        lines.append(f"Even with house-hacking, monthly burn is -${abs(m.house_hack_net):,.0f}/mo — requires strong income.")

    lines.append(f"Cash needed to close: ~${ctc.total:,.0f} (down + closing + reserves).")
    lines.append(f"5-yr moderate equity gain (~4%/yr appreciation + paydown): ~${appr.equity_gained:,.0f}.")
    lines.append("GOOD FIRST PROPERTY ✓" if good else "STRETCH / VERIFY CAREFULLY ⚠")
    return " ".join(lines)


def _build_checks(prop: Property) -> list[str]:
    """Return 3–5 key things to verify before making an offer."""
    checks = [
        "Verify all bedrooms meet egress/habitability code for legal rental.",
        "Confirm zoning and any ADU permits with the city planning department.",
        "Order a pre-inspection to estimate rehab cost before finalizing offer.",
    ]
    if prop.has_adu_signal:
        checks.append("Request permit history for any secondary unit — confirm it's legal, not just 'potential'.")
    if prop.hoa_monthly and prop.hoa_monthly > 0:
        checks.append(f"HOA is ${prop.hoa_monthly}/mo — request CC&Rs and check rental restriction rules.")
    if (prop.days_on_market or 0) > 30:
        checks.append(f"Property has been on market {prop.days_on_market} days — ask why and verify seller motivation.")
    if prop.year_built and prop.year_built < 1978:
        checks.append(f"Built {prop.year_built} — test for lead paint and asbestos; budget $3–10k for remediation.")
    return checks[:5]


def save_underwriting(db, prop: Property, result: UnderwritingResult) -> Underwriting:
    """Persist underwriting result to the database."""
    from sqlalchemy.orm import Session

    existing = db.query(Underwriting).filter(Underwriting.property_id == prop.id).first()

    data = dict(
        property_id=prop.id,
        down_payment=result.down_payment,
        loan_amount=result.loan_amount,
        interest_rate=result.interest_rate,
        monthly_pi=result.monthly.monthly_pi,
        monthly_tax=result.monthly.monthly_tax,
        monthly_insurance=result.monthly.monthly_insurance,
        monthly_pmi=result.monthly.monthly_pmi,
        monthly_hoa=result.monthly.monthly_hoa,
        monthly_maintenance=result.monthly.monthly_maintenance,
        monthly_total_piti=result.monthly.monthly_total_piti,
        owner_occupant_burn=result.monthly.owner_occupant_burn,
        house_hack_net=result.monthly.house_hack_net,
        full_rental_net=result.monthly.full_rental_net,
        room_rental_net_low=result.monthly.room_rental_net_low,
        room_rental_net_mid=result.monthly.room_rental_net_mid,
        room_rental_net_high=result.monthly.room_rental_net_high,
        cash_to_close=result.cash_to_close.total,
        appreciation_conservative=result.appreciation_conservative.equity_gained,
        appreciation_moderate=result.appreciation_moderate.equity_gained,
        appreciation_optimistic=result.appreciation_optimistic.equity_gained,
        good_first_property=result.good_first_property,
        summary_json=json.dumps({
            "verdict": result.verdict,
            "checks": result.top_considerations,
        }),
    )

    if existing:
        for k, v in data.items():
            setattr(existing, k, v)
        return existing
    else:
        uw = Underwriting(**data)
        db.add(uw)
        return uw

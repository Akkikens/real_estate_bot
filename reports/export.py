"""
Export Module
=============
Generates CSV and PDF exports of property data and underwriting reports.

CSV exports:
  - Property list (filtered or full)
  - Underwriting summary for a single property
  - Comp analysis

PDF exports:
  - Full underwriting report with financials, scenarios, and verdict
  - Comp analysis summary

Uses only stdlib + existing deps (no extra PDF library needed for v1;
generates a clean HTML report that can be printed/saved as PDF from browser,
or uses the API endpoint to serve downloadable content).
"""

from __future__ import annotations

import csv
import io
import json
import logging
from dataclasses import asdict
from datetime import datetime, timezone
from typing import Optional

from database.models import Property
from underwriting.calculator import UnderwritingResult

logger = logging.getLogger(__name__)


# ── CSV Exports ───────────────────────────────────────────────────────────────


def properties_to_csv(props: list[Property]) -> str:
    """
    Export a list of Property objects to a CSV string.
    Columns match the most useful fields for analysis.
    """
    output = io.StringIO()
    writer = csv.writer(output)

    headers = [
        "Address", "City", "State", "Zip", "Price", "Beds", "Baths",
        "Sqft", "Lot Sqft", "Year Built", "Property Type",
        "DOM", "HOA/mo", "Score", "Rating",
        "ADU Signal", "Deal Signal", "Risk Signal",
        "BART Distance (mi)", "Walk Score", "Transit Score",
        "Source", "Listing URL", "First Seen",
    ]
    writer.writerow(headers)

    for p in props:
        writer.writerow([
            p.address or "",
            p.city or "",
            p.state or "",
            p.zip_code or "",
            f"{p.list_price:.0f}" if p.list_price else "",
            p.beds or "",
            p.baths or "",
            p.sqft or "",
            p.lot_size_sqft or "",
            p.year_built or "",
            p.property_type or "",
            p.days_on_market or "",
            f"{p.hoa_monthly:.0f}" if p.hoa_monthly else "0",
            f"{p.total_score:.1f}" if p.total_score else "",
            p.rating or "",
            "Yes" if p.has_adu_signal else "No",
            "Yes" if p.has_deal_signal else "No",
            "Yes" if p.has_risk_signal else "No",
            f"{p.bart_distance_miles:.2f}" if p.bart_distance_miles else "",
            p.walk_score or "",
            p.transit_score or "",
            p.source or "",
            p.listing_url or "",
            p.first_seen_at.strftime("%Y-%m-%d") if p.first_seen_at else "",
        ])

    return output.getvalue()


def underwriting_to_csv(result: UnderwritingResult) -> str:
    """
    Export a single underwriting result to a CSV string.
    Two sections: monthly breakdown + scenarios.
    """
    output = io.StringIO()
    writer = csv.writer(output)
    m = result.monthly

    writer.writerow(["Underwriting Report", result.address])
    writer.writerow(["Generated", datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")])
    writer.writerow([])

    # Property info
    writer.writerow(["List Price", f"${result.list_price:,.0f}"])
    writer.writerow(["Down Payment", f"${result.down_payment:,.0f}"])
    writer.writerow(["Loan Amount", f"${result.loan_amount:,.0f}"])
    writer.writerow(["LTV", f"{result.ltv_pct:.1f}%"])
    writer.writerow(["Interest Rate", f"{result.interest_rate*100:.2f}%"])
    writer.writerow([])

    # Monthly breakdown
    writer.writerow(["Monthly Costs", "Amount"])
    writer.writerow(["Principal + Interest", f"${m.monthly_pi:,.0f}"])
    writer.writerow(["Property Tax", f"${m.monthly_tax:,.0f}"])
    writer.writerow(["Insurance", f"${m.monthly_insurance:,.0f}"])
    writer.writerow(["PMI", f"${m.monthly_pmi:,.0f}"])
    writer.writerow(["HOA", f"${m.monthly_hoa:,.0f}"])
    writer.writerow(["Maintenance", f"${m.monthly_maintenance:,.0f}"])
    writer.writerow(["Total PITI", f"${m.monthly_total_piti:,.0f}"])
    writer.writerow([])

    # Scenarios
    writer.writerow(["Income Scenario", "Monthly Net"])
    writer.writerow(["Owner-Occupant", f"${m.owner_occupant_burn:+,.0f}"])
    writer.writerow(["House-Hack", f"${m.house_hack_net:+,.0f}"])
    writer.writerow(["Room Rental (Low)", f"${m.room_rental_net_low:+,.0f}"])
    writer.writerow(["Room Rental (Mid)", f"${m.room_rental_net_mid:+,.0f}"])
    writer.writerow(["Room Rental (High)", f"${m.room_rental_net_high:+,.0f}"])
    writer.writerow(["Full Rental", f"${m.full_rental_net:+,.0f}"])
    writer.writerow([])

    # Cash to close
    writer.writerow(["Cash to Close", "Amount"])
    writer.writerow(["Down Payment", f"${result.cash_to_close.down_payment:,.0f}"])
    writer.writerow(["Closing Costs", f"${result.cash_to_close.closing_costs:,.0f}"])
    writer.writerow(["Reserves (3mo)", f"${result.cash_to_close.initial_reserves:,.0f}"])
    writer.writerow(["Total", f"${result.cash_to_close.total:,.0f}"])
    writer.writerow([])

    # Appreciation
    writer.writerow(["5-Year Appreciation", "Equity Gained"])
    writer.writerow(["Conservative (2%/yr)", f"${result.appreciation_conservative.equity_gained:,.0f}"])
    writer.writerow(["Moderate (4%/yr)", f"${result.appreciation_moderate.equity_gained:,.0f}"])
    writer.writerow(["Optimistic (6%/yr)", f"${result.appreciation_optimistic.equity_gained:,.0f}"])
    writer.writerow([])

    # Verdict
    writer.writerow(["Good First Property?", "Yes" if result.good_first_property else "No"])
    writer.writerow(["Verdict", result.verdict])
    writer.writerow([])
    writer.writerow(["Key Considerations"])
    for check in result.top_considerations:
        writer.writerow([check])

    return output.getvalue()


# ── HTML/PDF Report ───────────────────────────────────────────────────────────


def underwriting_to_html(result: UnderwritingResult, prop: Optional[Property] = None) -> str:
    """
    Generate a standalone HTML underwriting report.
    Can be rendered in a browser and printed to PDF.
    """
    m = result.monthly
    ctc = result.cash_to_close
    now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")

    verdict_color = "#2d7d2d" if result.good_first_property else "#c9760c"
    verdict_badge = "GOOD FIRST PROPERTY" if result.good_first_property else "STRETCH / VERIFY"

    # Property details section
    prop_info = ""
    if prop:
        prop_info = f"""
        <div class="section">
            <h2>Property Details</h2>
            <div class="grid">
                <div class="stat"><span class="label">Beds/Baths</span><span class="value">{prop.beds or '?'}/{prop.baths or '?'}</span></div>
                <div class="stat"><span class="label">Sqft</span><span class="value">{f"{prop.sqft:,}" if prop.sqft else "?"}</span></div>
                <div class="stat"><span class="label">Lot Size</span><span class="value">{f"{prop.lot_size_sqft:,}" if prop.lot_size_sqft else "?"} sqft</span></div>
                <div class="stat"><span class="label">Year Built</span><span class="value">{prop.year_built or '?'}</span></div>
                <div class="stat"><span class="label">Type</span><span class="value">{prop.property_type or '?'}</span></div>
                <div class="stat"><span class="label">DOM</span><span class="value">{prop.days_on_market or '?'} days</span></div>
                <div class="stat"><span class="label">Score</span><span class="value">{prop.total_score or 0:.0f}/100 ({(prop.rating or 'n/a').upper()})</span></div>
                <div class="stat"><span class="label">HOA</span><span class="value">${prop.hoa_monthly or 0:,.0f}/mo</span></div>
            </div>
        </div>"""

    # Score breakdown
    score_section = ""
    if prop and prop.score_breakdown:
        try:
            breakdown = json.loads(prop.score_breakdown)
            rows = ""
            for dim, val in breakdown.items():
                if isinstance(val, dict):
                    raw = val.get("raw", 0)
                    weighted = val.get("weighted", 0)
                    rows += f"<tr><td>{dim.replace('_', ' ').title()}</td><td>{raw:.1f}</td><td>{weighted:.1f}</td></tr>"
                else:
                    rows += f"<tr><td>{dim.replace('_', ' ').title()}</td><td colspan='2'>{val}</td></tr>"
            score_section = f"""
            <div class="section">
                <h2>Score Breakdown</h2>
                <table>
                    <tr><th>Dimension</th><th>Raw</th><th>Weighted</th></tr>
                    {rows}
                </table>
            </div>"""
        except (json.JSONDecodeError, TypeError):
            pass

    def _net_class(val: float) -> str:
        return "positive" if val >= 0 else "negative"

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Underwriting Report — {result.address}</title>
<style>
  * {{ margin: 0; padding: 0; box-sizing: border-box; }}
  body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
         color: #1a1a1a; background: #fff; padding: 32px; max-width: 900px; margin: 0 auto; }}
  h1 {{ font-size: 24px; margin-bottom: 4px; }}
  h2 {{ font-size: 18px; margin-bottom: 12px; color: #333; border-bottom: 2px solid #e0e0e0; padding-bottom: 4px; }}
  .subtitle {{ color: #666; font-size: 14px; margin-bottom: 24px; }}
  .section {{ margin-bottom: 28px; }}
  .grid {{ display: grid; grid-template-columns: repeat(4, 1fr); gap: 12px; }}
  .stat {{ background: #f8f8f8; padding: 12px; border-radius: 6px; }}
  .stat .label {{ display: block; font-size: 11px; color: #888; text-transform: uppercase; letter-spacing: 0.5px; }}
  .stat .value {{ display: block; font-size: 18px; font-weight: 600; margin-top: 4px; }}
  table {{ width: 100%; border-collapse: collapse; font-size: 14px; }}
  th {{ text-align: left; padding: 8px 12px; background: #f0f0f0; font-weight: 600; }}
  td {{ padding: 8px 12px; border-bottom: 1px solid #eee; }}
  tr:last-child td {{ border-bottom: none; }}
  .positive {{ color: #2d7d2d; font-weight: 600; }}
  .negative {{ color: #c0392b; font-weight: 600; }}
  .verdict-box {{ padding: 16px; border-radius: 8px; margin: 16px 0;
                  background: {verdict_color}15; border-left: 4px solid {verdict_color}; }}
  .verdict-badge {{ display: inline-block; padding: 4px 12px; border-radius: 4px;
                    background: {verdict_color}; color: white; font-size: 12px;
                    font-weight: 700; letter-spacing: 0.5px; margin-bottom: 8px; }}
  .checks {{ margin-top: 16px; }}
  .checks li {{ margin-bottom: 6px; font-size: 14px; }}
  .hero {{ display: grid; grid-template-columns: repeat(3, 1fr); gap: 16px; margin-bottom: 24px; }}
  .hero-card {{ background: #f8f8f8; padding: 16px; border-radius: 8px; text-align: center; }}
  .hero-card .amount {{ font-size: 28px; font-weight: 700; }}
  .hero-card .desc {{ font-size: 12px; color: #666; margin-top: 4px; }}
  @media print {{ body {{ padding: 16px; }} .section {{ break-inside: avoid; }} }}
  .footer {{ margin-top: 32px; padding-top: 16px; border-top: 1px solid #eee;
             font-size: 11px; color: #aaa; text-align: center; }}
</style>
</head>
<body>

<h1>Underwriting Report</h1>
<p class="subtitle">{result.address} &mdash; Generated {now}</p>

<div class="hero">
    <div class="hero-card">
        <div class="amount">${result.list_price:,.0f}</div>
        <div class="desc">List Price</div>
    </div>
    <div class="hero-card">
        <div class="amount ${_net_class(m.house_hack_net)}">${m.house_hack_net:+,.0f}</div>
        <div class="desc">House-Hack Net/mo</div>
    </div>
    <div class="hero-card">
        <div class="amount">${ctc.total:,.0f}</div>
        <div class="desc">Cash to Close</div>
    </div>
</div>

{prop_info}

<div class="section">
    <h2>Loan Summary</h2>
    <div class="grid">
        <div class="stat"><span class="label">Down Payment</span><span class="value">${result.down_payment:,.0f}</span></div>
        <div class="stat"><span class="label">Loan Amount</span><span class="value">${result.loan_amount:,.0f}</span></div>
        <div class="stat"><span class="label">LTV</span><span class="value">{result.ltv_pct:.1f}%</span></div>
        <div class="stat"><span class="label">Rate</span><span class="value">{result.interest_rate*100:.2f}%</span></div>
    </div>
</div>

<div class="section">
    <h2>Monthly Cost Breakdown</h2>
    <table>
        <tr><th>Item</th><th>Monthly</th><th>Annual</th></tr>
        <tr><td>Principal + Interest</td><td>${m.monthly_pi:,.0f}</td><td>${m.monthly_pi*12:,.0f}</td></tr>
        <tr><td>Property Tax</td><td>${m.monthly_tax:,.0f}</td><td>${m.monthly_tax*12:,.0f}</td></tr>
        <tr><td>Insurance</td><td>${m.monthly_insurance:,.0f}</td><td>${m.monthly_insurance*12:,.0f}</td></tr>
        <tr><td>PMI</td><td>${m.monthly_pmi:,.0f}</td><td>${m.monthly_pmi*12:,.0f}</td></tr>
        <tr><td>HOA</td><td>${m.monthly_hoa:,.0f}</td><td>${m.monthly_hoa*12:,.0f}</td></tr>
        <tr><td>Maintenance</td><td>${m.monthly_maintenance:,.0f}</td><td>${m.monthly_maintenance*12:,.0f}</td></tr>
        <tr style="font-weight:700;background:#f0f0f0">
            <td>Total PITI</td><td>${m.monthly_total_piti:,.0f}</td><td>${m.monthly_total_piti*12:,.0f}</td>
        </tr>
    </table>
</div>

<div class="section">
    <h2>Income Scenarios (Monthly Net)</h2>
    <table>
        <tr><th>Scenario</th><th>Net/Month</th><th>Net/Year</th></tr>
        <tr>
            <td>Owner-Occupant (no rental)</td>
            <td class="{_net_class(m.owner_occupant_burn)}">${m.owner_occupant_burn:+,.0f}</td>
            <td class="{_net_class(m.owner_occupant_burn)}">${m.owner_occupant_burn*12:+,.0f}</td>
        </tr>
        <tr>
            <td>Room Rental (Low)</td>
            <td class="{_net_class(m.room_rental_net_low)}">${m.room_rental_net_low:+,.0f}</td>
            <td class="{_net_class(m.room_rental_net_low)}">${m.room_rental_net_low*12:+,.0f}</td>
        </tr>
        <tr>
            <td>Room Rental (Mid)</td>
            <td class="{_net_class(m.room_rental_net_mid)}">${m.room_rental_net_mid:+,.0f}</td>
            <td class="{_net_class(m.room_rental_net_mid)}">${m.room_rental_net_mid*12:+,.0f}</td>
        </tr>
        <tr>
            <td>Room Rental (High)</td>
            <td class="{_net_class(m.room_rental_net_high)}">${m.room_rental_net_high:+,.0f}</td>
            <td class="{_net_class(m.room_rental_net_high)}">${m.room_rental_net_high*12:+,.0f}</td>
        </tr>
        <tr style="background:#f0f0f0">
            <td><strong>House-Hack</strong></td>
            <td class="{_net_class(m.house_hack_net)}"><strong>${m.house_hack_net:+,.0f}</strong></td>
            <td class="{_net_class(m.house_hack_net)}"><strong>${m.house_hack_net*12:+,.0f}</strong></td>
        </tr>
        <tr>
            <td>Full Rental (investment)</td>
            <td class="{_net_class(m.full_rental_net)}">${m.full_rental_net:+,.0f}</td>
            <td class="{_net_class(m.full_rental_net)}">${m.full_rental_net*12:+,.0f}</td>
        </tr>
    </table>
</div>

<div class="section">
    <h2>Cash to Close</h2>
    <table>
        <tr><th>Component</th><th>Amount</th></tr>
        <tr><td>Down Payment</td><td>${ctc.down_payment:,.0f}</td></tr>
        <tr><td>Closing Costs</td><td>${ctc.closing_costs:,.0f}</td></tr>
        <tr><td>Reserves (3 months PITI)</td><td>${ctc.initial_reserves:,.0f}</td></tr>
        <tr style="font-weight:700;background:#f0f0f0"><td>Total</td><td>${ctc.total:,.0f}</td></tr>
    </table>
</div>

<div class="section">
    <h2>5-Year Appreciation Scenarios</h2>
    <div class="grid" style="grid-template-columns: repeat(3, 1fr);">
        <div class="stat">
            <span class="label">Conservative (2%/yr)</span>
            <span class="value">${result.appreciation_conservative.equity_gained:,.0f}</span>
        </div>
        <div class="stat">
            <span class="label">Moderate (4%/yr)</span>
            <span class="value positive">${result.appreciation_moderate.equity_gained:,.0f}</span>
        </div>
        <div class="stat">
            <span class="label">Optimistic (6%/yr)</span>
            <span class="value positive">${result.appreciation_optimistic.equity_gained:,.0f}</span>
        </div>
    </div>
</div>

{score_section}

<div class="section">
    <div class="verdict-box">
        <span class="verdict-badge">{verdict_badge}</span>
        <p style="margin-top:8px;font-size:14px;">{result.verdict}</p>
    </div>
</div>

<div class="section">
    <h2>Key Considerations</h2>
    <ol class="checks">
        {"".join(f'<li>{c}</li>' for c in result.top_considerations)}
    </ol>
</div>

<div class="footer">
    HouseMatch Underwriting Report &mdash; {now} &mdash; For informational purposes only. Not financial advice.
</div>

</body>
</html>"""

    return html

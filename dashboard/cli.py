"""
CLI Dashboard
=============
Typer + Rich based command-line interface.

Commands:
  bot ingest          — Pull new listings from all/selected sources
  bot score           — Re-score all un-scored properties
  bot report          — Print the daily report
  bot list            — List properties with filtering/sorting
  bot show <id>       — Full detail for a single property
  bot underwrite <id> — Run financial underwriting
  bot draft <id>      — Draft agent outreach
  bot crm             — Show CRM summary and follow-ups due
  bot watch <id>      — Mark a property as watched
  bot archive <id>    — Archive / hide a property
  bot run             — Full pipeline: ingest → score → alert → report
"""

from __future__ import annotations

import json
import sys
from datetime import datetime
from typing import Optional

import typer
from rich import box
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.text import Text

app = typer.Typer(name="bot", help="🏠 Bay Area Property Acquisition Bot", add_completion=False)
console = Console()

# ── Rating colors ──────────────────────────────────────────────────────────────

RATING_COLORS = {
    "excellent": "bright_green",
    "good":      "green",
    "watch":     "yellow",
    "skip":      "red",
}


def _rating_text(rating: str, score: float) -> Text:
    color = RATING_COLORS.get(rating, "white")
    return Text(f"{score:.0f} ({rating.upper()})", style=color)


# ── Lazy DB import (avoid circular at module load) ────────────────────────────

def _get_db():
    from database.db import get_db
    return get_db()


def _init():
    from database.db import init_db
    init_db()


# ─────────────────────────────────────────────────────────────────────────────
# ingest
# ─────────────────────────────────────────────────────────────────────────────

@app.command()
def ingest(
    source: str = typer.Option("redfin", "--source", "-s", help="Source: redfin | zillow | realtor | craigslist | mock (test only) | all"),
    max_price: float = typer.Option(None, "--max-price", "-p", help="Override max price"),
    cities: Optional[str] = typer.Option(None, "--cities", "-c", help="Comma-sep city list"),
    rescore: bool = typer.Option(True, "--rescore/--no-rescore", help="Re-score after ingestion"),
    allow_mock: bool = typer.Option(False, "--allow-mock", hidden=True, help="Allow mock data (testing only)"),
):
    """Pull listings from real source(s) and save to database. Default source: redfin."""
    _init()

    from config import settings
    from database.db import get_db
    from ingestion.normalizer import upsert_property
    from ingestion.sanity import check as sanity_check, log_anomaly
    from scoring.engine import score_and_update

    # ── Guard: warn loudly if mock is used ────────────────────────────────────
    if source == "mock" and not allow_mock:
        console.print(
            "\n[bold red]⚠  MOCK DATA BLOCKED[/bold red]\n"
            "The mock source generates synthetic listings with fake prices that are wildly\n"
            "inconsistent with real Bay Area values (e.g. $440k in Albany, $429k in Berkeley).\n\n"
            "Mock data is for pipeline testing only — never for real deal-finding.\n\n"
            "To test the pipeline safely, use:\n"
            "  [bold]python3 main.py ingest --source mock --allow-mock[/bold]\n\n"
            "To ingest real listings, use:\n"
            "  [bold]python3 main.py ingest --source redfin[/bold]\n"
        )
        raise typer.Exit(1)

    price_limit = max_price or settings.BUYER_MAX_PRICE
    city_list = [c.strip() for c in cities.split(",")] if cities else settings.BUYER_TARGET_CITIES

    console.rule(f"[bold]Ingesting from: [cyan]{source}[/cyan]")
    console.print(f"  Cities: {', '.join(city_list)}")
    console.print(f"  Max price: ${price_limit:,.0f}\n")

    adapters = []
    if source in ("mock",) and allow_mock:
        from ingestion.mock_adapter import MockAdapter
        adapters.append(MockAdapter(n_per_city=10))
    if source in ("redfin", "all"):
        from ingestion.redfin_adapter import RedfinAdapter
        adapters.append(RedfinAdapter())
    if source in ("zillow", "all"):
        from ingestion.zillow_adapter import ZillowAdapter
        adapters.append(ZillowAdapter())
    if source in ("realtor", "all"):
        from ingestion.realtor_adapter import RealtorAdapter
        adapters.append(RealtorAdapter())
    if source in ("craigslist", "all"):
        from ingestion.craigslist_adapter import CraigslistAdapter
        adapters.append(CraigslistAdapter())

    if not adapters:
        console.print(f"[red]Unknown source: {source}. Use redfin | zillow | realtor | craigslist | all[/red]")
        raise typer.Exit(1)

    total_new = 0
    total_updated = 0
    total_rejected = 0

    with get_db() as db:
        for adapter in adapters:
            console.print(f"  Fetching from [yellow]{adapter.source_name}[/yellow]...")
            try:
                listings = adapter.fetch_listings(city_list, price_limit)
            except Exception as exc:
                console.print(f"  [red]Error fetching from {adapter.source_name}: {exc}[/red]")
                continue

            console.print(f"  → {len(listings)} raw listings received")

            accepted = 0
            rejected = 0
            for normalized in listings:
                # ── Sanity check before touching the main DB ──────────────────
                sanity = sanity_check(normalized)
                if not sanity.passed:
                    log_anomaly(db, normalized, sanity)
                    rejected += 1
                    total_rejected += 1
                    continue

                prop, created = upsert_property(db, normalized)
                if created:
                    total_new += 1
                else:
                    total_updated += 1
                accepted += 1

                if rescore:
                    score_and_update(prop)

            color = "green" if accepted > 0 else "yellow"
            console.print(
                f"  [{color}]Accepted: {accepted}[/{color}]  "
                f"[red]Rejected: {rejected}[/red]"
                + (f"  (run [bold]bot anomalies[/bold] to see why)" if rejected > 0 else "")
            )

        db.commit()

    console.print(
        f"\n[bold green]Done.[/bold green] "
        f"New: {total_new} | Updated: {total_updated} | Rejected: {total_rejected}"
    )

    if total_rejected > 0:
        console.print(
            f"[yellow]{total_rejected} listings failed sanity checks.[/yellow] "
            "Run [bold]python3 main.py anomalies[/bold] to see the rejection report."
        )

    if rescore and total_new + total_updated > 0:
        console.print("Properties scored. Run [bold]python3 main.py report[/bold] to see top opportunities.")


# ─────────────────────────────────────────────────────────────────────────────
# score
# ─────────────────────────────────────────────────────────────────────────────

@app.command()
def score(
    unscored_only: bool = typer.Option(False, "--unscored-only", help="Only score properties without a score"),
):
    """Re-score properties in the database."""
    _init()

    from database.db import get_db
    from database.models import Property
    from scoring.engine import score_and_update

    with get_db() as db:
        q = db.query(Property).filter(Property.is_archived == False)
        if unscored_only:
            q = q.filter(Property.total_score.is_(None))
        props = q.all()

        console.print(f"Scoring [bold]{len(props)}[/bold] properties...")
        for prop in props:
            score_and_update(prop)
        db.commit()

    console.print(f"[green]Done. {len(props)} properties scored.[/green]")


# ─────────────────────────────────────────────────────────────────────────────
# list
# ─────────────────────────────────────────────────────────────────────────────

@app.command(name="list")
def list_properties(
    limit: int = typer.Option(25, "--limit", "-n"),
    min_score: float = typer.Option(0, "--min-score"),
    city: Optional[str] = typer.Option(None, "--city"),
    min_beds: int = typer.Option(0, "--min-beds"),
    adu_only: bool = typer.Option(False, "--adu"),
    status: str = typer.Option("active", "--status"),
):
    """List properties with optional filters."""
    _init()

    from database.db import get_db
    from database.models import Property

    with get_db() as db:
        q = db.query(Property).filter(Property.is_archived == False)

        if status:
            q = q.filter(Property.status == status)
        if min_score > 0:
            q = q.filter(Property.total_score >= min_score)
        if city:
            q = q.filter(Property.city.ilike(f"%{city}%"))
        if min_beds > 0:
            q = q.filter(Property.beds >= min_beds)
        if adu_only:
            q = q.filter(Property.has_adu_signal == True)

        props = q.order_by(Property.total_score.desc()).limit(limit).all()

        table = Table(
            title=f"🏠 Properties (top {limit})",
            box=box.ROUNDED,
            show_lines=False,
        )
        table.add_column("#", style="dim", width=3)
        table.add_column("Address", min_width=22)
        table.add_column("City", width=14)
        table.add_column("Price", justify="right", width=12)
        table.add_column("Bd/Ba", width=6)
        table.add_column("Sqft", width=6)
        table.add_column("DOM", width=5)
        table.add_column("Score", width=18)
        table.add_column("Flags", width=8)

        for i, prop in enumerate(props, 1):
            score_val = prop.total_score or 0
            rating = prop.rating or "skip"
            flags = ""
            if prop.has_adu_signal:  flags += "A"
            if prop.has_deal_signal: flags += "D"
            if prop.has_risk_signal: flags += "R"
            if prop.is_watched:      flags += "W"

            table.add_row(
                str(i),
                (prop.address or "?")[:24],
                prop.city or "?",
                f"${prop.list_price:,.0f}" if prop.list_price else "?",
                f"{prop.beds or '?'}/{prop.baths or '?'}",
                str(prop.sqft or "?"),
                str(prop.days_on_market or "?"),
                _rating_text(rating, score_val),
                flags or "-",
            )

        console.print(table)
        console.print(f"[dim]Flags: A=ADU  D=Deal  R=Risk  W=Watched[/dim]")
        console.print(f"[dim]Use [bold]bot show <address>[/bold] for full detail.[/dim]")


# ─────────────────────────────────────────────────────────────────────────────
# show
# ─────────────────────────────────────────────────────────────────────────────

@app.command()
def show(
    identifier: str = typer.Argument(help="Property address fragment or UUID"),
    underwrite_flag: bool = typer.Option(True, "--underwrite/--no-underwrite"),
):
    """Show full detail for a property."""
    _init()

    from database.db import get_db
    from database.models import Property
    from underwriting.calculator import underwrite

    with get_db() as db:
        prop = (
            db.query(Property)
            .filter(Property.address.ilike(f"%{identifier}%"))
            .order_by(Property.total_score.desc())
            .first()
        )
        if not prop:
            prop = db.query(Property).filter(Property.id == identifier).first()

        if not prop:
            console.print(f"[red]No property found matching: {identifier}[/red]")
            raise typer.Exit(1)

        _print_property_detail(prop, console)

        if underwrite_flag and prop.list_price:
            result = underwrite(prop)
            _print_underwriting(result, console)


def _print_property_detail(prop, console):
    score_val = prop.total_score or 0
    rating = prop.rating or "skip"
    color = RATING_COLORS.get(rating, "white")

    info = (
        f"[bold]{prop.address}[/bold]\n"
        f"{prop.city}, {prop.state} {prop.zip_code}\n\n"
        f"[bold cyan]Price:[/bold cyan] ${prop.list_price:,.0f}  "
        f"[bold cyan]Beds/Ba:[/bold cyan] {prop.beds}/{prop.baths}  "
        f"[bold cyan]Sqft:[/bold cyan] {prop.sqft or '?'}  "
        f"[bold cyan]Lot:[/bold cyan] {prop.lot_size_sqft or '?'} sqft\n"
        f"[bold cyan]Type:[/bold cyan] {prop.property_type or '?'}  "
        f"[bold cyan]Year:[/bold cyan] {prop.year_built or '?'}  "
        f"[bold cyan]DOM:[/bold cyan] {prop.days_on_market or '?'} days  "
        f"[bold cyan]HOA:[/bold cyan] ${prop.hoa_monthly or 0}/mo\n\n"
        f"[bold cyan]Score:[/bold cyan] [{color}]{score_val:.0f}/100 ({rating.upper()})[/{color}]\n\n"
    )

    if prop.score_explanation:
        info += prop.score_explanation + "\n\n"

    if prop.listing_remarks:
        info += f"[dim]{prop.listing_remarks[:600]}...[/dim]\n\n"

    info += f"[link={prop.listing_url}]{prop.listing_url or 'No URL'}[/link]"
    if prop.agent_name:
        info += f"\n[bold cyan]Agent:[/bold cyan] {prop.agent_name}  {prop.agent_email or ''}  {prop.agent_phone or ''}"

    console.print(Panel(info, title=f"🏠 Property Detail", border_style=color))


def _print_underwriting(result, console):
    m = result.monthly
    ctc = result.cash_to_close

    table = Table(title="💰 Financial Underwriting", box=box.SIMPLE_HEAVY)
    table.add_column("Item", style="cyan")
    table.add_column("Monthly", justify="right")
    table.add_column("Annual", justify="right")

    def _row(label, mo):
        table.add_row(label, f"${mo:,.0f}", f"${mo*12:,.0f}")

    _row("Principal + Interest", m.monthly_pi)
    _row("Property Tax", m.monthly_tax)
    _row("Insurance", m.monthly_insurance)
    if m.monthly_pmi > 0:
        _row("PMI", m.monthly_pmi)
    if m.monthly_hoa > 0:
        _row("HOA", m.monthly_hoa)
    _row("Maintenance Reserve", m.monthly_maintenance)
    table.add_section()
    table.add_row("[bold]Total PITI[/bold]", f"[bold]${m.monthly_total_piti:,.0f}[/bold]", f"[bold]${m.monthly_total_piti*12:,.0f}[/bold]")

    console.print(table)

    # Scenarios
    scen = Table(title="📊 Income Scenarios (Monthly Net)", box=box.SIMPLE_HEAVY)
    scen.add_column("Scenario")
    scen.add_column("Net/Month", justify="right")
    scen.add_column("Note")

    def _srow(label, net, note):
        color = "green" if net >= 0 else "red"
        scen.add_row(label, f"[{color}]${net:+,.0f}[/{color}]", note)

    _srow("Owner-occupant (no rental)", m.owner_occupant_burn, "Full PITI out of pocket")
    _srow("Room rental — low", m.room_rental_net_low, f"Rent {max((result.monthly.monthly_total_piti > 0), 1)} rooms @ ${1000}/mo")
    _srow("Room rental — mid", m.room_rental_net_mid, "Mid Bay Area room rate")
    _srow("Room rental — high", m.room_rental_net_high, "Peak room rate")
    _srow("House-hack (all non-owner)", m.house_hack_net, "Best realistic scenario")
    _srow("Full rental (you move out)", m.full_rental_net, "Investment mode")

    console.print(scen)

    # Cash to close
    console.print(
        f"\n[bold]Cash to Close:[/bold]  Down: ${ctc.down_payment:,.0f}  "
        f"+ Closing: ${ctc.closing_costs:,.0f}  "
        f"+ Reserves: ${ctc.initial_reserves:,.0f}  "
        f"= [bold yellow]${ctc.total:,.0f}[/bold yellow]"
    )

    # Appreciation
    console.print("\n[bold]5-Year Equity Gain (Appreciation + Paydown):[/bold]")
    console.print(
        f"  Conservative (2%/yr): [cyan]${result.appreciation_conservative.equity_gained:,.0f}[/cyan]  "
        f"Moderate (4%/yr): [green]${result.appreciation_moderate.equity_gained:,.0f}[/green]  "
        f"Optimistic (6%/yr): [bright_green]${result.appreciation_optimistic.equity_gained:,.0f}[/bright_green]"
    )

    verdict_color = "green" if result.good_first_property else "yellow"
    console.print(Panel(result.verdict, title="Verdict", border_style=verdict_color))

    if result.top_considerations:
        console.print("[bold]Key things to verify before offering:[/bold]")
        for i, check in enumerate(result.top_considerations, 1):
            console.print(f"  {i}. {check}")


# ─────────────────────────────────────────────────────────────────────────────
# report
# ─────────────────────────────────────────────────────────────────────────────

@app.command()
def report(
    save: bool = typer.Option(False, "--save", help="Save report to file"),
):
    """Print the daily opportunity report."""
    _init()

    from database.db import get_db
    from reports.generator import full_report

    with get_db() as db:
        data = full_report(db)

        console.rule(f"[bold]📊 Daily Report — {datetime.now().strftime('%Y-%m-%d %H:%M')}[/bold]")

        # Top 10
        console.print("\n[bold bright_green]🏆 Top 10 Active Opportunities[/bold bright_green]")
        _print_prop_table(data["top_opportunities"], console)

        # Price drops
        drops = data["price_drops"]
        if drops:
            console.print(f"\n[bold yellow]💰 Price Drops (last 7 days)[/bold yellow]")
            drop_table = Table(box=box.SIMPLE)
            drop_table.add_column("Address")
            drop_table.add_column("City")
            drop_table.add_column("New Price", justify="right")
            drop_table.add_column("Score", justify="right")
            for d in drops[:5]:
                p = d["property"]
                drop_table.add_row(
                    p.address, p.city,
                    f"${d['new_price']:,.0f}",
                    f"{p.total_score or 0:.0f}",
                )
            console.print(drop_table)

        # House hacks
        console.print("\n[bold cyan]🏠 Best House-Hack Candidates[/bold cyan]")
        _print_prop_table(data["best_house_hacks"][:5], console, compact=True)

        # ADU
        console.print("\n[bold magenta]🏗 Best ADU Candidates[/bold magenta]")
        _print_prop_table(data["best_adu_candidates"][:5], console, compact=True)

        # Large lots
        console.print("\n[bold]🌳 Best Large-Lot Opportunities[/bold]")
        _print_prop_table(data["best_large_lots"][:5], console, compact=True)

        # Traps
        traps = data["likely_traps"]
        if traps:
            console.print("\n[bold red]⚠ Likely Traps — Avoid or Verify Carefully[/bold red]")
            for t in traps:
                p = t["property"]
                console.print(f"  • [red]{p.address}, {p.city}[/red] (score {p.total_score or 0:.0f}): {t['reason']}")

        total = sum(1 for _ in data["top_opportunities"])
        console.rule(f"[dim]Run [bold]bot show <address>[/bold] for details on any property[/dim]")


def _print_prop_table(props, console, compact: bool = False):
    if not props:
        console.print("  [dim]No results.[/dim]")
        return

    t = Table(box=box.SIMPLE, show_header=True)
    t.add_column("Address", min_width=20)
    t.add_column("City", width=14)
    t.add_column("Price", justify="right", width=12)
    if not compact:
        t.add_column("Bd/Ba", width=6)
        t.add_column("Lot", width=7)
        t.add_column("DOM", width=5)
    t.add_column("Score", width=18)

    for prop in props:
        score_val = prop.total_score or 0
        rating = prop.rating or "skip"
        row = [
            (prop.address or "?")[:22],
            prop.city or "?",
            f"${prop.list_price:,.0f}" if prop.list_price else "?",
        ]
        if not compact:
            row += [
                f"{prop.beds or '?'}/{prop.baths or '?'}",
                f"{prop.lot_size_sqft or '?'}",
                str(prop.days_on_market or "?"),
            ]
        row.append(_rating_text(rating, score_val))
        t.add_row(*row)

    console.print(t)


# ─────────────────────────────────────────────────────────────────────────────
# draft
# ─────────────────────────────────────────────────────────────────────────────

@app.command()
def draft(
    identifier: str = typer.Argument(help="Property address fragment or UUID"),
    outreach_type: str = typer.Option("initial", "--type", "-t",
                                       help="initial | followup | disclosure | adu_inquiry | price_drop"),
):
    """Draft outreach email to the listing agent."""
    _init()

    from database.db import get_db
    from database.models import Property
    from crm.tracker import create_draft
    from outreach.templates import draft_outreach

    with get_db() as db:
        prop = (
            db.query(Property)
            .filter(Property.address.ilike(f"%{identifier}%"))
            .first()
        )
        if not prop:
            console.print(f"[red]Property not found: {identifier}[/red]")
            raise typer.Exit(1)

        result = draft_outreach(prop, outreach_type=outreach_type)

        console.print(Panel(
            f"[bold]To:[/bold]     {result['to_name']} <{result['to_email']}>\n"
            f"[bold]Phone:[/bold]  {result['to_phone']}\n"
            f"[bold]Subject:[/bold] {result['subject']}\n\n"
            f"{result['body']}",
            title=f"📧 Draft Outreach — {outreach_type}",
            border_style="cyan",
        ))

        # Save draft to CRM
        record = create_draft(db, prop, outreach_type=outreach_type)
        db.commit()

        console.print(f"\n[dim]Saved as draft #{record.id} in CRM. Use [bold]bot crm[/bold] to manage.[/dim]")
        console.print(f"[dim]Mode: [bold]{__import__('config.settings', fromlist=['OUTREACH_MODE']).OUTREACH_MODE}[/bold] — set OUTREACH_MODE=auto to enable automatic sending.[/dim]")


# ─────────────────────────────────────────────────────────────────────────────
# anomalies
# ─────────────────────────────────────────────────────────────────────────────

@app.command()
def anomalies(
    limit: int = typer.Option(30, "--limit", "-n"),
    code: Optional[str] = typer.Option(None, "--code", help="Filter by rejection code"),
):
    """Show listings that failed sanity checks and why."""
    _init()

    from database.db import get_db
    from database.models import PropertyAnomaly

    with get_db() as db:
        q = db.query(PropertyAnomaly).order_by(PropertyAnomaly.flagged_at.desc())
        if code:
            q = q.filter(PropertyAnomaly.rejection_code == code.upper())
        rows = q.limit(limit).all()
        total = db.query(PropertyAnomaly).count()

        # Summary by rejection code
        from sqlalchemy import func as sqlfunc
        counts = (
            db.query(PropertyAnomaly.rejection_code, sqlfunc.count().label("n"))
            .group_by(PropertyAnomaly.rejection_code)
            .all()
        )

    console.print(f"\n[bold red]⚠ Anomaly Report[/bold red]  ({total} total rejected)\n")

    # Code breakdown
    summary = Table(title="Rejection Code Summary", box=box.SIMPLE)
    summary.add_column("Code", style="red")
    summary.add_column("Count", justify="right")
    summary.add_column("What it means")
    code_meanings = {
        "MOCK_DATA":        "Synthetic data from mock adapter — not real listings",
        "NO_SOURCE_URL":    "No verifiable listing URL — cannot confirm it's real",
        "NO_LISTING_ID":    "No MLS# or source ID — cannot deduplicate",
        "PRICE_IMPLAUSIBLE":"Price is below the city sanity floor for Bay Area residential",
        "PPSF_TOO_LOW":     "Price/sqft too low — likely a data parsing error",
        "PPSF_TOO_HIGH":    "Price/sqft too high — likely a data parsing error",
        "ADDRESS_GENERIC":  "Address matches synthetic/mock pattern",
    }
    for rc, n in sorted(counts, key=lambda x: -x[1]):
        summary.add_row(rc, str(n), code_meanings.get(rc, "See rejection reason"))
    console.print(summary)

    if not rows:
        console.print("[dim]No anomalies recorded.[/dim]")
        return

    # Detail table
    console.print(f"\n[bold]Most recent {len(rows)} rejected listings:[/bold]")
    detail = Table(box=box.SIMPLE, show_lines=True)
    detail.add_column("Address", min_width=20)
    detail.add_column("City", width=14)
    detail.add_column("Price", justify="right", width=12)
    detail.add_column("Source", width=8)
    detail.add_column("Code", width=18, style="red")
    detail.add_column("Reason", min_width=35)

    for row in rows:
        detail.add_row(
            row.raw_address or "?",
            row.raw_city or "?",
            f"${row.raw_price:,.0f}" if row.raw_price else "?",
            row.source or "?",
            row.rejection_code or "?",
            (row.rejection_reason or "")[:120],
        )
    console.print(detail)

    if any(r.rejection_code == "MOCK_DATA" for r in rows):
        console.print(
            "\n[bold yellow]Note:[/bold yellow] MOCK_DATA rejections are expected if you previously "
            "ran [bold]--source mock[/bold]. Clear the DB and re-run with "
            "[bold]--source redfin[/bold] to get real data."
        )


# ─────────────────────────────────────────────────────────────────────────────
# crm
# ─────────────────────────────────────────────────────────────────────────────

@app.command()
def crm():
    """Show CRM summary and follow-ups due."""
    _init()

    from database.db import get_db
    from crm.tracker import get_crm_summary, get_follow_ups_due

    with get_db() as db:
        summary = get_crm_summary(db)
        console.print(Panel(
            f"Total outreach: {summary['total']}\n"
            f"  Drafts:       {summary['drafts']}\n"
            f"  Sent:         {summary['sent']}\n"
            f"  Replied:      {summary['replied']} (reply rate: {summary['reply_rate']})\n"
            f"  Follow-ups due: [bold yellow]{summary['follow_ups_due']}[/bold yellow]",
            title="📋 CRM Summary",
            border_style="cyan",
        ))

        due = get_follow_ups_due(db)
        if due:
            console.print("\n[bold yellow]Follow-ups due:[/bold yellow]")
            for r in due:
                prop = r.property
                console.print(
                    f"  • {prop.address if prop else '?'} — sent {r.sent_at.strftime('%Y-%m-%d') if r.sent_at else '?'}"
                    f" — agent: {r.agent_name or '?'}"
                )


# ─────────────────────────────────────────────────────────────────────────────
# watch / archive
# ─────────────────────────────────────────────────────────────────────────────

@app.command()
def watch(identifier: str = typer.Argument(help="Address fragment or UUID")):
    """Mark a property as watched (get alerts for any changes)."""
    _init()
    _toggle_flag(identifier, "is_watched", True, "👁 Watching")


@app.command()
def archive(identifier: str = typer.Argument(help="Address fragment or UUID")):
    """Archive (hide) a property from reports."""
    _init()
    _toggle_flag(identifier, "is_archived", True, "📦 Archived")


def _toggle_flag(identifier, field, value, label):
    from database.db import get_db
    from database.models import Property

    with get_db() as db:
        prop = db.query(Property).filter(Property.address.ilike(f"%{identifier}%")).first()
        if not prop:
            console.print(f"[red]Not found: {identifier}[/red]")
            raise typer.Exit(1)
        setattr(prop, field, value)
        db.commit()
        console.print(f"[green]{label}: {prop.address}[/green]")


# ─────────────────────────────────────────────────────────────────────────────
# underwrite command
# ─────────────────────────────────────────────────────────────────────────────

@app.command()
def underwrite_cmd(
    identifier: str = typer.Argument(help="Address fragment or UUID"),
    down: float = typer.Option(None, "--down", "-d", help="Down payment override"),
):
    """Run financial underwriting for a property."""
    _init()

    from database.db import get_db
    from database.models import Property
    from underwriting.calculator import underwrite, save_underwriting

    with get_db() as db:
        prop = db.query(Property).filter(Property.address.ilike(f"%{identifier}%")).first()
        if not prop:
            console.print(f"[red]Not found: {identifier}[/red]")
            raise typer.Exit(1)

        result = underwrite(prop, down_payment=down)
        save_underwriting(db, prop, result)
        db.commit()
        _print_underwriting(result, console)


# Alias
app.command(name="uw")(underwrite_cmd)


# ─────────────────────────────────────────────────────────────────────────────
# import-csv  (Redfin manual download fallback)
# ─────────────────────────────────────────────────────────────────────────────

@app.command(name="import-csv")
def import_csv(
    path: str = typer.Argument(help="Path to Redfin CSV download"),
    rescore: bool = typer.Option(True, "--rescore/--no-rescore"),
):
    """
    Import a manually-downloaded Redfin CSV file.

    Use this if the API adapter returns 0 results (bot detection).

    How to get the CSV:
      1. Go to redfin.com → search your city → set filters
      2. Scroll to bottom of results → click 'Download All'
      3. Run: python3 main.py import-csv ~/Downloads/redfin_*.csv
    """
    _init()

    import os
    from database.db import get_db
    from ingestion.redfin_adapter import RedfinAdapter
    from ingestion.normalizer import upsert_property
    from ingestion.sanity import check as sanity_check, log_anomaly
    from scoring.engine import score_and_update

    if not os.path.exists(path):
        console.print(f"[red]File not found: {path}[/red]")
        raise typer.Exit(1)

    with open(path, "r", encoding="utf-8-sig") as f:
        csv_text = f.read()

    adapter = RedfinAdapter()
    listings = adapter._parse_csv(csv_text)
    console.print(f"Parsed [bold]{len(listings)}[/bold] listings from {path}")

    total_new = 0
    total_updated = 0
    total_rejected = 0

    with get_db() as db:
        for normalized in listings:
            sanity = sanity_check(normalized)
            if not sanity.passed:
                log_anomaly(db, normalized, sanity)
                total_rejected += 1
                continue

            prop, created = upsert_property(db, normalized)
            if created:
                total_new += 1
            else:
                total_updated += 1

            if rescore:
                score_and_update(prop)

        db.commit()

    console.print(
        f"[green]Done.[/green] New: {total_new} | Updated: {total_updated} | "
        f"Rejected: {total_rejected}"
    )
    if total_new + total_updated > 0:
        console.print("Run [bold]python3 main.py report[/bold] to see ranked results.")


# ─────────────────────────────────────────────────────────────────────────────
# run — full pipeline
# ─────────────────────────────────────────────────────────────────────────────

@app.command()
def run(
    source: str = typer.Option("all", "--source", "-s"),
    alert: bool = typer.Option(True, "--alert/--no-alert"),
    allow_mock: bool = typer.Option(False, "--allow-mock", hidden=True),
):
    """Full pipeline: ingest → score → alert → report. Default source: all."""
    console.rule("[bold]🤖 Running Full Pipeline[/bold]")

    # Step 1: Ingest
    ingest(source=source, max_price=None, cities=None, rescore=True, allow_mock=allow_mock)

    # Step 2: Alerts
    if alert:
        from database.db import get_db
        from database.models import Property
        from alerts.notifier import check_and_alert
        from config import settings

        _init()
        with get_db() as db:
            props = (
                db.query(Property)
                .filter(Property.status == "active", Property.is_archived == False)
                .all()
            )
            n = check_and_alert(db, props)
            db.commit()
            console.print(f"[cyan]Alerts: {n} sent (threshold: {settings.ALERT_SCORE_THRESHOLD})[/cyan]")

    # Step 3: Report
    report(save=False)


# ─────────────────────────────────────────────────────────────────────────────
# add — manually add a property (FB Marketplace, word of mouth, etc.)
# ─────────────────────────────────────────────────────────────────────────────

@app.command()
def add(
    address: str = typer.Argument(help="Full street address"),
    city: str = typer.Argument(help="City name"),
    price: float = typer.Argument(help="List price"),
    beds: int = typer.Option(None, "--beds", "-b"),
    baths: float = typer.Option(None, "--baths"),
    sqft: int = typer.Option(None, "--sqft"),
    lot: int = typer.Option(None, "--lot", help="Lot size in sqft"),
    url: str = typer.Option("", "--url", "-u", help="Listing URL (FB Marketplace, etc.)"),
    notes: str = typer.Option("", "--notes", "-n", help="Your notes about this property"),
    source_name: str = typer.Option("manual", "--source", "-s", help="Source label (manual, facebook, word_of_mouth)"),
):
    """
    Manually add a property you found (FB Marketplace, word of mouth, driving, etc.).

    Example:
      python3 main.py add "123 Main St" Richmond 550000 --beds 3 --baths 2 --lot 5500
      python3 main.py add "456 Oak Ave" Oakland 650000 --url "https://fb.me/abc" --source facebook
    """
    _init()

    from database.db import get_db
    from ingestion.normalizer import normalize, upsert_property
    from scoring.engine import score_and_update

    raw = {
        "address":       address,
        "city":          city,
        "state":         "CA",
        "zip_code":      "",
        "list_price":    price,
        "beds":          beds,
        "baths":         baths,
        "sqft":          sqft,
        "lot_size_sqft": lot,
        "status":        "active",
        "listing_url":   url or f"manual://{source_name}",
        "external_id":   f"MANUAL-{address[:20].replace(' ', '-')}",
        "source":        source_name,
        "listing_remarks": notes or f"Manually added from {source_name}",
    }

    normalized = normalize(raw, source=source_name)

    with get_db() as db:
        prop, created = upsert_property(db, normalized)
        score_and_update(prop)
        if notes:
            prop.notes = notes
        db.commit()

        action = "Added" if created else "Updated"
        score_val = prop.total_score or 0
        rating = prop.rating or "skip"
        console.print(
            f"\n[green]{action}:[/green] {prop.address}, {prop.city} — "
            f"${prop.list_price:,.0f} — Score: {score_val:.0f} ({rating.upper()})"
        )
        console.print(f"[dim]Run [bold]python3 main.py show \"{address}\"[/bold] for full detail.[/dim]")

"""
SQLAlchemy ORM models.
All tables live in a single SQLite (or Postgres) database.
"""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Optional

from sqlalchemy import (
    Boolean,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
    func,
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    pass


# ─── Property ─────────────────────────────────────────────────────────────────


class Property(Base):
    """One row per unique real-world property (deduped across sources)."""

    __tablename__ = "properties"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))

    # ── Location ──────────────────────────────────────────────────────────────
    address: Mapped[str] = mapped_column(String(255), nullable=False)
    city: Mapped[str] = mapped_column(String(100))
    state: Mapped[str] = mapped_column(String(2), default="CA")
    zip_code: Mapped[Optional[str]] = mapped_column(String(10), nullable=True)
    latitude: Mapped[Optional[float]] = mapped_column(Float)
    longitude: Mapped[Optional[float]] = mapped_column(Float)

    # ── Listing basics ────────────────────────────────────────────────────────
    list_price: Mapped[Optional[float]] = mapped_column(Float)
    original_price: Mapped[Optional[float]] = mapped_column(Float)
    beds: Mapped[Optional[int]] = mapped_column(Integer)
    baths: Mapped[Optional[float]] = mapped_column(Float)
    sqft: Mapped[Optional[int]] = mapped_column(Integer)
    lot_size_sqft: Mapped[Optional[int]] = mapped_column(Integer)
    property_type: Mapped[Optional[str]] = mapped_column(String(60))  # SFR, Duplex, Condo…
    year_built: Mapped[Optional[int]] = mapped_column(Integer)
    zoning: Mapped[Optional[str]] = mapped_column(String(60))
    hoa_monthly: Mapped[Optional[float]] = mapped_column(Float, default=0.0)
    estimated_taxes_annual: Mapped[Optional[float]] = mapped_column(Float)
    days_on_market: Mapped[Optional[int]] = mapped_column(Integer, default=0)
    status: Mapped[str] = mapped_column(String(30), default="active")  # active, pending, sold

    # ── Financials (estimated) ────────────────────────────────────────────────
    estimated_rent_monthly: Mapped[Optional[float]] = mapped_column(Float)
    price_per_sqft: Mapped[Optional[float]] = mapped_column(Float)

    # ── Listing content ───────────────────────────────────────────────────────
    listing_remarks: Mapped[Optional[str]] = mapped_column(Text)
    agent_name: Mapped[Optional[str]] = mapped_column(String(150))
    agent_email: Mapped[Optional[str]] = mapped_column(String(150))
    agent_phone: Mapped[Optional[str]] = mapped_column(String(30))
    brokerage: Mapped[Optional[str]] = mapped_column(String(150))

    # ── Source tracking ───────────────────────────────────────────────────────
    source: Mapped[Optional[str]] = mapped_column(String(30))  # redfin, zillow, mock…
    external_id: Mapped[Optional[str]] = mapped_column(String(100))
    listing_url: Mapped[Optional[str]] = mapped_column(String(500))

    # ── Neighborhood / transit data ───────────────────────────────────────────
    walk_score: Mapped[Optional[int]] = mapped_column(Integer)
    transit_score: Mapped[Optional[int]] = mapped_column(Integer)
    bart_distance_miles: Mapped[Optional[float]] = mapped_column(Float)
    school_rating: Mapped[Optional[float]] = mapped_column(Float)
    crime_index: Mapped[Optional[int]] = mapped_column(Integer)  # lower = safer

    # ── Scoring output ────────────────────────────────────────────────────────
    total_score: Mapped[Optional[float]] = mapped_column(Float)
    score_breakdown: Mapped[Optional[str]] = mapped_column(Text)  # JSON
    score_explanation: Mapped[Optional[str]] = mapped_column(Text)
    rating: Mapped[Optional[str]] = mapped_column(String(20))  # excellent, good, watch, skip

    # ── Flags ─────────────────────────────────────────────────────────────────
    has_adu_signal: Mapped[bool] = mapped_column(Boolean, default=False)
    has_deal_signal: Mapped[bool] = mapped_column(Boolean, default=False)
    has_risk_signal: Mapped[bool] = mapped_column(Boolean, default=False)
    is_watched: Mapped[bool] = mapped_column(Boolean, default=False)
    is_archived: Mapped[bool] = mapped_column(Boolean, default=False)
    alert_sent: Mapped[bool] = mapped_column(Boolean, default=False)

    # ── Notes ─────────────────────────────────────────────────────────────────
    notes: Mapped[Optional[str]] = mapped_column(Text)

    # ── Timestamps ───────────────────────────────────────────────────────────
    first_seen_at: Mapped[datetime] = mapped_column(DateTime, default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=func.now(), onupdate=func.now())
    status_changed_at: Mapped[Optional[datetime]] = mapped_column(DateTime)

    # ── Relationships ─────────────────────────────────────────────────────────
    price_history: Mapped[list[PriceHistory]] = relationship(
        "PriceHistory", back_populates="property", cascade="all, delete-orphan"
    )
    outreach_records: Mapped[list[OutreachRecord]] = relationship(
        "OutreachRecord", back_populates="property", cascade="all, delete-orphan"
    )
    alerts: Mapped[list[Alert]] = relationship(
        "Alert", back_populates="property", cascade="all, delete-orphan"
    )
    underwriting: Mapped[Optional[Underwriting]] = relationship(
        "Underwriting", back_populates="property", uselist=False, cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<Property {self.address}, {self.city} — ${self.list_price:,.0f} score={self.total_score}>"


# ─── PriceHistory ─────────────────────────────────────────────────────────────


class PriceHistory(Base):
    __tablename__ = "price_history"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    property_id: Mapped[str] = mapped_column(ForeignKey("properties.id"), nullable=False)
    recorded_at: Mapped[datetime] = mapped_column(DateTime, default=func.now())
    price: Mapped[float] = mapped_column(Float, nullable=False)
    event: Mapped[str] = mapped_column(String(30), default="listed")  # listed, reduced, increased, sold

    property: Mapped[Property] = relationship("Property", back_populates="price_history")


# ─── Underwriting ─────────────────────────────────────────────────────────────


class Underwriting(Base):
    """Financial underwriting snapshot for a property."""

    __tablename__ = "underwriting"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    property_id: Mapped[str] = mapped_column(ForeignKey("properties.id"), nullable=False, unique=True)

    # Inputs used
    down_payment: Mapped[float] = mapped_column(Float)
    loan_amount: Mapped[float] = mapped_column(Float)
    interest_rate: Mapped[float] = mapped_column(Float)

    # Monthly fixed costs
    monthly_pi: Mapped[float] = mapped_column(Float)   # principal + interest
    monthly_tax: Mapped[float] = mapped_column(Float)
    monthly_insurance: Mapped[float] = mapped_column(Float)
    monthly_pmi: Mapped[float] = mapped_column(Float, default=0.0)
    monthly_hoa: Mapped[float] = mapped_column(Float, default=0.0)
    monthly_maintenance: Mapped[float] = mapped_column(Float)
    monthly_total_piti: Mapped[float] = mapped_column(Float)

    # Scenarios (monthly net, negative = you pay)
    owner_occupant_burn: Mapped[float] = mapped_column(Float)
    house_hack_net: Mapped[float] = mapped_column(Float)
    full_rental_net: Mapped[float] = mapped_column(Float)
    room_rental_net_low: Mapped[float] = mapped_column(Float)
    room_rental_net_mid: Mapped[float] = mapped_column(Float)
    room_rental_net_high: Mapped[float] = mapped_column(Float)

    # Cash to close
    cash_to_close: Mapped[float] = mapped_column(Float)

    # Appreciation scenarios (5-yr equity gain estimate)
    appreciation_conservative: Mapped[float] = mapped_column(Float)  # 2%/yr
    appreciation_moderate: Mapped[float] = mapped_column(Float)       # 4%/yr
    appreciation_optimistic: Mapped[float] = mapped_column(Float)     # 6%/yr

    # Summary
    good_first_property: Mapped[bool] = mapped_column(Boolean, default=False)
    summary_json: Mapped[Optional[str]] = mapped_column(Text)

    computed_at: Mapped[datetime] = mapped_column(DateTime, default=func.now())

    property: Mapped[Property] = relationship("Property", back_populates="underwriting")


# ─── OutreachRecord ───────────────────────────────────────────────────────────


class OutreachRecord(Base):
    __tablename__ = "outreach"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    property_id: Mapped[str] = mapped_column(ForeignKey("properties.id"), nullable=False)

    agent_name: Mapped[Optional[str]] = mapped_column(String(150))
    agent_email: Mapped[Optional[str]] = mapped_column(String(150))
    agent_phone: Mapped[Optional[str]] = mapped_column(String(30))

    outreach_type: Mapped[str] = mapped_column(String(30), default="initial")  # initial, followup, disclosure_request
    subject: Mapped[Optional[str]] = mapped_column(String(255))
    draft_body: Mapped[Optional[str]] = mapped_column(Text)

    status: Mapped[str] = mapped_column(String(20), default="draft")  # draft, approved, sent, replied
    sent_at: Mapped[Optional[datetime]] = mapped_column(DateTime)
    reply_received_at: Mapped[Optional[datetime]] = mapped_column(DateTime)
    reply_body: Mapped[Optional[str]] = mapped_column(Text)
    reply_sentiment: Mapped[Optional[str]] = mapped_column(String(20))  # positive, neutral, negative

    next_follow_up: Mapped[Optional[datetime]] = mapped_column(DateTime)
    notes: Mapped[Optional[str]] = mapped_column(Text)

    created_at: Mapped[datetime] = mapped_column(DateTime, default=func.now())

    property: Mapped[Property] = relationship("Property", back_populates="outreach_records")


# ─── Alert ────────────────────────────────────────────────────────────────────


class Alert(Base):
    __tablename__ = "alerts"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    property_id: Mapped[str] = mapped_column(ForeignKey("properties.id"), nullable=False)

    alert_type: Mapped[str] = mapped_column(String(30))  # new_match, price_drop, status_change, agent_reply
    message: Mapped[str] = mapped_column(Text)
    channels: Mapped[Optional[str]] = mapped_column(String(100))  # email, sms, telegram

    sent: Mapped[bool] = mapped_column(Boolean, default=False)
    sent_at: Mapped[Optional[datetime]] = mapped_column(DateTime)
    error: Mapped[Optional[str]] = mapped_column(Text)

    created_at: Mapped[datetime] = mapped_column(DateTime, default=func.now())

    property: Mapped[Property] = relationship("Property", back_populates="alerts")


# ─── PropertyAnomaly ──────────────────────────────────────────────────────────


class PropertyAnomaly(Base):
    """
    Listings rejected from active reporting due to sanity check failures.
    Kept for audit trail — useful to catch parser bugs and bad source data.
    """

    __tablename__ = "property_anomalies"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)

    # Raw data exactly as received from source
    raw_address: Mapped[Optional[str]] = mapped_column(String(255))
    raw_city: Mapped[Optional[str]] = mapped_column(String(100))
    raw_zip: Mapped[Optional[str]] = mapped_column(String(10))
    raw_price: Mapped[Optional[float]] = mapped_column(Float)
    raw_beds: Mapped[Optional[int]] = mapped_column(Integer)
    raw_sqft: Mapped[Optional[int]] = mapped_column(Integer)

    # Source provenance
    source: Mapped[Optional[str]] = mapped_column(String(30))
    source_listing_id: Mapped[Optional[str]] = mapped_column(String(100))
    source_url: Mapped[Optional[str]] = mapped_column(String(500))

    # Why it was rejected (human-readable)
    rejection_reason: Mapped[str] = mapped_column(Text)
    rejection_code: Mapped[str] = mapped_column(String(50))  # MOCK_DATA, NO_SOURCE_URL, PRICE_IMPLAUSIBLE, etc.

    flagged_at: Mapped[datetime] = mapped_column(DateTime, default=func.now())

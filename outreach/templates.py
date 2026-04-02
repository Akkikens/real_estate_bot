"""
Outreach Templates
==================
Human-sounding, non-spammy email/text templates for agent outreach.

Three outreach types:
  1. initial_inquiry  — First contact about a listing
  2. followup         — 5–7 days later if no response
  3. disclosure_request — After initial positive response; ask for docs

Design principles:
  • Short, clear, professional
  • Personal (mentions specific property details)
  • No spam signals
  • Asks one clear question per message
  • Never auto-sends without mode='auto' in settings
"""

from __future__ import annotations

from string import Template
from typing import Any

from database.models import Property

# ── Templates ─────────────────────────────────────────────────────────────────

INITIAL_INQUIRY = Template("""\
Subject: Question about $address — Interested Buyer

Hi $agent_name,

I came across your listing at $address in $city ($list_price) and it looks like a strong fit for what I'm looking for.

I'm a pre-approved buyer focused on the East Bay, specifically looking for homes with house-hacking potential or ADU opportunities. A few quick questions:

1. Is there any flexibility on price / are you seeing active interest?
2. Can you share any details on the lot or zoning — specifically whether an ADU has been explored or permitted?
3. Would the seller consider accepting an offer contingent on inspection?

I'm ready to move quickly if the fundamentals check out. Would you be available for a showing this week?

Thanks,
Akshay
""")

FOLLOWUP = Template("""\
Subject: Re: $address — Still Interested

Hi $agent_name,

Just following up on my message from a few days ago about $address in $city.

I'm still actively looking and this property remains near the top of my list. Has there been any new activity, or any change in the seller's timeline?

Happy to talk briefly by phone if that's easier.

Thanks,
Akshay
""")

DISCLOSURE_REQUEST = Template("""\
Subject: Disclosure Package Request — $address

Hi $agent_name,

Thank you for your time on $address — I'm serious about moving forward and want to review the disclosure package.

Could you please share:

• Seller disclosure statement (TDS/SPQ)
• Any known permits or permit history (especially for any secondary unit or additions)
• Preliminary title report if available
• HOA documents if applicable
• Most recent tax bill

Also, if the seller has any flexibility on the closing timeline or is open to a pre-inspection period, that would be helpful to know.

Looking forward to reviewing and can have a decision within 48 hours of receiving the disclosures.

Thanks,
Akshay
""")

ADU_SPECIFIC_INQUIRY = Template("""\
Subject: ADU / Second Unit Question — $address

Hi $agent_name,

I noticed your listing at $address mentions potential for a second unit or ADU. This is one of the key things I'm evaluating.

A few quick questions:
1. Is there any existing permitted secondary unit, or is this just potential?
2. What is the lot size and current zoning designation?
3. Has the seller or any prior owner pulled permits for additions?

Any info you can share would really help me assess the opportunity. Happy to schedule a showing if it looks like a strong fit.

Thanks,
Akshay
""")

PRICE_DROP_INQUIRY = Template("""\
Subject: Recent Price Reduction — $address

Hi $agent_name,

I noticed the price on $address was recently adjusted to $list_price. I've been watching this property and the updated price brings it closer to where I need to be.

Could you give me a sense of where the seller's head is at? Is there additional room, or is this the floor? Also, are there any offers currently in play?

I'd love to schedule a tour this week.

Thanks,
Akshay
""")


# ── Draft builder ─────────────────────────────────────────────────────────────

TEMPLATE_MAP = {
    "initial":          INITIAL_INQUIRY,
    "followup":         FOLLOWUP,
    "disclosure":       DISCLOSURE_REQUEST,
    "adu_inquiry":      ADU_SPECIFIC_INQUIRY,
    "price_drop":       PRICE_DROP_INQUIRY,
}


def draft_outreach(prop: Property, outreach_type: str = "initial") -> dict[str, str]:
    """
    Build a subject + body for the given outreach type.
    Returns {"subject": "...", "body": "...", "type": outreach_type}
    """
    tmpl = TEMPLATE_MAP.get(outreach_type, INITIAL_INQUIRY)

    # Choose best template variant
    if outreach_type == "initial" and prop.has_adu_signal:
        tmpl = ADU_SPECIFIC_INQUIRY

    price_str = f"${prop.list_price:,.0f}" if prop.list_price else "listed"

    mapping = {
        "address":    prop.address or "the property",
        "city":       prop.city or "your area",
        "list_price": price_str,
        "agent_name": (prop.agent_name or "").split()[0] or "there",  # first name only
    }

    body = tmpl.safe_substitute(mapping)

    # Extract subject from body (first line after "Subject: ")
    lines = body.strip().splitlines()
    subject = ""
    body_lines = []
    for i, line in enumerate(lines):
        if line.startswith("Subject:"):
            subject = line.replace("Subject:", "").strip()
        else:
            body_lines.append(line)

    return {
        "subject": subject,
        "body": "\n".join(body_lines).strip(),
        "type": outreach_type,
        "to_name": prop.agent_name or "",
        "to_email": prop.agent_email or "",
        "to_phone": prop.agent_phone or "",
    }

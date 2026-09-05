"""Generate sample invoice PDFs with paired ground-truth extractions.

Produces, for each invoice, a realistic PDF plus a ground-truth record
matching the target extraction schema exactly. The PDFs deliberately carry
more information than the schema (totals, tax, addresses, payment terms,
remit-to blocks) so that extraction is a real task rather than a lookup.

Three layout templates are used so an extractor cannot overfit to a single
vendor's paperwork.

Deterministic: a fixed seed means regenerating produces byte-identical
content, so ground truth stays valid across runs.
"""

from __future__ import annotations

import datetime as dt
import json
import random
import uuid
from decimal import Decimal
from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.enums import TA_RIGHT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.platypus import (
    HRFlowable,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)

SEED = 20260907
OUT_DIR = Path("src/generator/")
PDF_DIR = OUT_DIR / "sample_invoices_pdfs"

rng = random.Random(SEED)
# Seed uuid4 deterministically by driving it from our own RNG.
_uuid_rng = random.Random(SEED + 1)


def det_uuid() -> str:
    return str(uuid.UUID(int=_uuid_rng.getrandbits(128), version=4))


# --------------------------------------------------------------------------
# Reference data
# --------------------------------------------------------------------------

VENDORS = [
    ("Meridian Components Pte Ltd", "accounts@meridian-components.example.com",
     "18 Tuas Avenue 8\nSingapore 639234", "Singapore"),
    ("Harbourline Industrial Supply", "ar.team@harbourline-supply.example.com",
     "442 Dock Road, Unit 6\nRotterdam 3089 JR", "Netherlands"),
    ("Ashgrove Fasteners Ltd", "billing@ashgrovefasteners.example.com",
     "Unit 12, Calder Business Park\nLeeds LS12 6HQ", "United Kingdom"),
    ("Nordkap Precision AS", "faktura@nordkap-precision.example.com",
     "Storgata 47\n7010 Trondheim", "Norway"),
    ("Tan & Sons Packaging", "invoices@tanandsons.example.com",
     "9 Jalan Kilang Barat\nSingapore 159351", "Singapore"),
    ("Vector Polymer Works", "remittance@vectorpolymer.example.com",
     "3300 Industrial Parkway\nColumbus, OH 43204", "United States"),
    ("Caldera Metals GmbH", "kreditoren@caldera-metals.example.com",
     "Industriestrasse 88\n70565 Stuttgart", "Germany"),
    ("Brightwater Electricals", "ap@brightwater-elec.example.com",
     "14 Wharf Street\nAuckland 1010", "New Zealand"),
]

PARTS = [
    ("10442", "Hex bolt M8x40, zinc plated", "EA"),
    ("10457", "Hex nut M8, DIN 934", "EA"),
    ("21883", "Bearing housing, cast alloy", "EA"),
    ("30112", "Polymer gasket 120mm ID", "EA"),
    ("30119", "Polymer gasket 140mm ID", "EA"),
    ("44201", "Control relay 24VDC 2CO", "EA"),
    ("44290", "Terminal block, 6mm2 grey", "EA"),
    ("55730", "Corrugated carton 400x300x200", "CS"),
    ("55744", "Pallet wrap 500mm x 300m", "RL"),
    ("67012", "Stainless shim 0.5mm sheet", "SH"),
    ("67088", "Copper busbar 20x5mm", "M"),
    ("71355", "Filter cartridge, 10 micron", "EA"),
    ("71390", "O-ring kit, nitrile assorted", "KT"),
    ("88204", "Drive belt, 1250mm", "EA"),
]

BUYER = (
    "Kestrel Manufacturing Pte Ltd",
    "Accounts Payable\n27 Boon Lay Way, #04-11\nSingapore 609965",
)

TERMS = ["Net 30", "Net 45", "Net 60", "2/10 Net 30", "Net 14"]
CURRENCIES = ["SGD", "EUR", "GBP", "USD"]


# --------------------------------------------------------------------------
# Data generation
# --------------------------------------------------------------------------


def money(low: float, high: float) -> Decimal:
    """Prices carried as Decimal internally; only cast to float at the
    schema boundary. See the note in the README about float money."""
    return Decimal(str(round(rng.uniform(low, high), 2)))


def build_invoice(index: int, n_lines: int, include_expected_date: bool) -> dict:
    vendor_name, vendor_contact, vendor_addr, country = VENDORS[index % len(VENDORS)]
    parts = rng.sample(PARTS, n_lines)

    invoice_date = dt.date(2026, rng.randint(1, 9), rng.randint(1, 28))

    line_items = []
    delivery_dates = []
    for part_number, description, uom in parts:
        qty = rng.choice([1, 2, 5, 8, 10, 12, 24, 25, 40, 50, 100, 144, 250])
        price = money(0.35, 480.00)
        line_items.append(
            {
                "part_number": part_number,
                "description": description,
                "uom": uom,
                "quantity": qty,
                "unit_price": price,
            }
        )
        # One delivery date per line, parallel to line_items.
        delivery_dates.append(
            invoice_date + dt.timedelta(days=rng.randint(-21, 90))
        )

    expected_delivery_date = (
        invoice_date + dt.timedelta(days=rng.randint(14, 75))
        if include_expected_date
        else None
    )

    subtotal = sum(li["quantity"] * li["unit_price"] for li in line_items)
    tax_rate = Decimal(rng.choice(["0.00", "0.07", "0.09", "0.19", "0.20"]))
    tax = (subtotal * tax_rate).quantize(Decimal("0.01"))

    return {
        "invoice_number": f"INV-2026-{4100 + index}",
        "invoice_date": invoice_date,
        "po_number": f"PO-{rng.randint(80000, 89999)}",
        "vendor_name": vendor_name,
        "vendor_contact": vendor_contact,
        "vendor_address": vendor_addr,
        "vendor_country": country,
        "currency": rng.choice(CURRENCIES),
        "terms": rng.choice(TERMS),
        "line_items": line_items,
        "delivery_dates": delivery_dates,
        "expected_delivery_date": expected_delivery_date,
        "subtotal": subtotal,
        "tax_rate": tax_rate,
        "tax": tax,
        "total": subtotal + tax,
        # Schema identifiers. Stable per invoice.
        "vendor_id": det_uuid(),
        "invoice_id": det_uuid(),
        "purchase_order_id": det_uuid(),
    }


def to_ground_truth(inv: dict) -> dict:
    """Project an invoice onto the target extraction schema, exactly.

    Only the fields in the schema appear here. Everything else on the PDF
    is distractor content the extractor must ignore.
    """
    return {
        "line_items": [
            {
                "part_number": li["part_number"],
                "quantity": li["quantity"],
                "unit_price": float(li["unit_price"]),
            }
            for li in inv["line_items"]
        ],
        "vendor_id": inv["vendor_id"],
        "invoice_id": inv["invoice_id"],
        "expected_delivery_date": (
            inv["expected_delivery_date"].isoformat()
            if inv["expected_delivery_date"]
            else None
        ),
        "purchase_order_id": inv["purchase_order_id"],
        "delivery_dates": [d.isoformat() for d in inv["delivery_dates"]],
        "vendor_info": {
            "name": inv["vendor_name"],
            "contact": inv["vendor_contact"],
        },
    }


# --------------------------------------------------------------------------
# Rendering
# --------------------------------------------------------------------------

INK = colors.HexColor("#1a1a1a")
MUTED = colors.HexColor("#6b6b6b")
RULE = colors.HexColor("#c9c9c9")
BAND = colors.HexColor("#eeeeee")


def styles():
    s = getSampleStyleSheet()
    return {
        "title": ParagraphStyle("t", parent=s["Normal"], fontName="Helvetica-Bold",
                                fontSize=20, textColor=INK, leading=24),
        "h": ParagraphStyle("h", parent=s["Normal"], fontName="Helvetica-Bold",
                            fontSize=8, textColor=MUTED, leading=11,
                            spaceAfter=2),
        "b": ParagraphStyle("b", parent=s["Normal"], fontName="Helvetica",
                            fontSize=9, textColor=INK, leading=12),
        "bb": ParagraphStyle("bb", parent=s["Normal"], fontName="Helvetica-Bold",
                             fontSize=9, textColor=INK, leading=12),
        "sm": ParagraphStyle("sm", parent=s["Normal"], fontName="Helvetica",
                             fontSize=7.5, textColor=MUTED, leading=10),
        "r": ParagraphStyle("r", parent=s["Normal"], fontName="Helvetica",
                            fontSize=9, textColor=INK, alignment=TA_RIGHT),
    }


def fmt(d: Decimal) -> str:
    return f"{d:,.2f}"


def kv_block(st, pairs) -> Table:
    rows = [[Paragraph(k, st["h"]), Paragraph(v, st["b"])] for k, v in pairs]
    t = Table(rows, colWidths=[34 * mm, 52 * mm])
    t.setStyle(TableStyle([
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
        ("TOPPADDING", (0, 0), (-1, -1), 0),
        ("LEFTPADDING", (0, 0), (-1, -1), 0),
    ]))
    return t


def line_table(st, inv, variant: int) -> Table:
    """Three column arrangements, so field order and header wording differ
    across vendors the way they do in reality."""
    if variant == 0:
        head = ["Part No.", "Description", "UOM", "Qty", "Unit Price", "Amount"]
        widths = [22, 62, 12, 16, 26, 28]
        rows = [[li["part_number"], li["description"], li["uom"],
                 str(li["quantity"]), fmt(li["unit_price"]),
                 fmt(li["quantity"] * li["unit_price"])]
                for li in inv["line_items"]]
    elif variant == 1:
        head = ["Item", "Material No.", "Qty", "Price/Unit", "Delivery", "Net Value"]
        widths = [12, 26, 16, 26, 28, 28]
        rows = [[str(i + 1), li["part_number"], str(li["quantity"]),
                 fmt(li["unit_price"]), d.strftime("%d.%m.%Y"),
                 fmt(li["quantity"] * li["unit_price"])]
                for i, (li, d) in enumerate(
                    zip(inv["line_items"], inv["delivery_dates"]))]
    else:
        head = ["Part Number", "Ordered", "Unit Rate", "Ship Date", "Line Total"]
        widths = [34, 20, 28, 30, 30]
        rows = [[li["part_number"], f'{li["quantity"]} {li["uom"]}',
                 fmt(li["unit_price"]), d.strftime("%d %b %Y"),
                 fmt(li["quantity"] * li["unit_price"])]
                for li, d in zip(inv["line_items"], inv["delivery_dates"])]

    t = Table([head] + rows, colWidths=[w * mm for w in widths], repeatRows=1)
    style = [
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, -1), 8),
        ("TEXTCOLOR", (0, 0), (-1, 0), INK),
        ("BACKGROUND", (0, 0), (-1, 0), BAND),
        ("LINEBELOW", (0, 0), (-1, 0), 0.6, RULE),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("TOPPADDING", (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
        ("ALIGN", (-1, 1), (-1, -1), "RIGHT"),
    ]
    if variant == 0:
        style += [("ALIGN", (3, 1), (5, -1), "RIGHT")]
    elif variant == 1:
        style += [("ALIGN", (2, 1), (3, -1), "RIGHT"),
                  ("GRID", (0, 0), (-1, -1), 0.4, RULE)]
    else:
        style += [("ALIGN", (1, 1), (2, -1), "RIGHT"),
                  ("ROWBACKGROUNDS", (0, 1), (-1, -1),
                   [colors.white, colors.HexColor("#f7f7f7")])]
    t.setStyle(TableStyle(style))
    return t


def render(inv: dict, path: Path, variant: int) -> None:
    st = styles()
    doc = SimpleDocTemplate(
        str(path), pagesize=A4,
        leftMargin=18 * mm, rightMargin=18 * mm,
        topMargin=16 * mm, bottomMargin=16 * mm,
        title=inv["invoice_number"], author=inv["vendor_name"],
    )
    cur = inv["currency"]
    story = []

    header = Table(
        [[Paragraph(inv["vendor_name"], st["title"]),
          Paragraph("<b>TAX INVOICE</b>" if variant != 2 else "<b>INVOICE</b>",
                    ParagraphStyle("x", parent=st["title"], fontSize=15,
                                   alignment=TA_RIGHT))]],
        colWidths=[110 * mm, 64 * mm])
    header.setStyle(TableStyle([("VALIGN", (0, 0), (-1, -1), "TOP"),
                                ("LEFTPADDING", (0, 0), (-1, -1), 0),
                                ("RIGHTPADDING", (0, 0), (-1, -1), 0)]))
    story += [header,
              Paragraph(inv["vendor_address"].replace("\n", "<br/>") +
                        f'<br/>{inv["vendor_country"]}<br/>{inv["vendor_contact"]}',
                        st["sm"]),
              Spacer(1, 8),
              HRFlowable(width="100%", thickness=0.8, color=RULE),
              Spacer(1, 8)]

    left = kv_block(st, [
        ("BILL TO", f'<b>{BUYER[0]}</b><br/>{BUYER[1].replace(chr(10), "<br/>")}'),
    ])
    right_pairs = [
        ("INVOICE NO.", inv["invoice_number"]),
        ("INVOICE DATE", inv["invoice_date"].strftime("%d %B %Y")),
        ("PURCHASE ORDER", inv["po_number"]),
        ("PAYMENT TERMS", inv["terms"]),
        ("CURRENCY", cur),
    ]
    if inv["expected_delivery_date"]:
        label = {0: "EXPECTED DELIVERY", 1: "REQ. DELIVERY DATE",
                 2: "PROMISED DELIVERY"}[variant]
        right_pairs.append(
            (label, inv["expected_delivery_date"].strftime("%d %B %Y")))
    right = kv_block(st, right_pairs)

    meta = Table([[left, right]], colWidths=[88 * mm, 86 * mm])
    meta.setStyle(TableStyle([("VALIGN", (0, 0), (-1, -1), "TOP"),
                              ("LEFTPADDING", (0, 0), (-1, -1), 0)]))
    story += [meta, Spacer(1, 12)]

    # Reference identifiers. Real ERP invoices carry system keys like these.
    story += [
        Paragraph(
            f'Vendor ID: {inv["vendor_id"]} &nbsp;&nbsp;|&nbsp;&nbsp; '
            f'Invoice ID: {inv["invoice_id"]}<br/>'
            f'Purchase Order ID: {inv["purchase_order_id"]}', st["sm"]),
        Spacer(1, 10),
        line_table(st, inv, variant),
        Spacer(1, 8),
    ]

    totals = Table(
        [["Subtotal", f'{cur} {fmt(inv["subtotal"])}'],
         [f'Tax ({inv["tax_rate"] * 100:.0f}%)', f'{cur} {fmt(inv["tax"])}'],
         ["Total Due", f'{cur} {fmt(inv["total"])}']],
        colWidths=[36 * mm, 40 * mm], hAlign="RIGHT")
    totals.setStyle(TableStyle([
        ("FONTNAME", (0, 0), (-1, -1), "Helvetica"),
        ("FONTNAME", (0, 2), (-1, 2), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, -1), 9),
        ("ALIGN", (1, 0), (1, -1), "RIGHT"),
        ("LINEABOVE", (0, 2), (-1, 2), 0.8, INK),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
    ]))
    story += [totals, Spacer(1, 14)]

    if variant != 2 and inv["delivery_dates"]:
        earliest = min(inv["delivery_dates"]).strftime("%d %B %Y")
        latest = max(inv["delivery_dates"]).strftime("%d %B %Y")
        story += [Paragraph(
            f"Delivery schedule: consignments dated {earliest} through {latest}. "
            f"Partial shipments permitted under the referenced purchase order.",
            st["sm"]), Spacer(1, 6)]

    story += [
        HRFlowable(width="100%", thickness=0.5, color=RULE),
        Spacer(1, 5),
        Paragraph(
            f'Remit to {inv["vendor_name"]}. Please quote invoice number '
            f'{inv["invoice_number"]} and purchase order {inv["po_number"]} '
            f'with payment. Queries to {inv["vendor_contact"]}. '
            f'Goods remain the property of the seller until paid in full.',
            st["sm"]),
    ]
    doc.build(story)


# --------------------------------------------------------------------------
# Main
# --------------------------------------------------------------------------

def main() -> None:
    PDF_DIR.mkdir(parents=True, exist_ok=True)

    # (n_lines, include_expected_delivery_date) - spread of shapes including
    # the single-line and long-tail cases that break naive table parsers.
    specs = [
        (2, False),   # matches the reference schema shape exactly
        (2, True),
        (1, True),    # single line item
        (3, False),
        (4, True),
        (5, False),
        (8, True),    # long table
        (3, True),
        (6, False),
        (2, True),
    ]

    manifest = []
    for i, (n_lines, has_expected) in enumerate(specs):
        inv = build_invoice(i, n_lines, has_expected)
        variant = i % 3
        pdf_name = f'{inv["invoice_number"]}.pdf'
        render(inv, PDF_DIR / pdf_name, variant)

        manifest.append({
            "pdf": f"pdfs/{pdf_name}",
            "layout_variant": variant,
            "line_count": n_lines,
            "has_expected_delivery_date": has_expected,
            "expected_output": to_ground_truth(inv),
        })
        print(f"  {pdf_name}  variant={variant}  lines={n_lines}")

    (OUT_DIR / "ground_truth.json").write_text(
        json.dumps({"seed": SEED, "invoices": manifest}, indent=2), encoding="utf-8")
    print(f"\n{len(manifest)} invoices -> {OUT_DIR}")


if __name__ == "__main__":
    main()

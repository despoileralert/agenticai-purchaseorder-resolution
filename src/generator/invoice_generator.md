# Sample invoice PDFs

Ten generated invoice PDFs with paired ground-truth extractions, for testing
the document extraction stage of the PO exception resolution agent.

```
sample_invoices/
├── pdfs/INV-2026-4100.pdf ... INV-2026-4109.pdf
├── ground_truth.json
├── generate_sample_invoices.py
└── README.md
```

## What's in the set

| | |
|---|---|
| Invoices | 10 |
| Line items | 36 total (1 to 8 per invoice) |
| Layout templates | 3 |
| Vendors | 8, across 7 countries |
| `expected_delivery_date` null | 4 of 10 |

Three layouts are used so an extractor can't overfit to one vendor's
paperwork. They differ in column order, header wording (`Qty` vs `Ordered`,
`Delivery` vs `Ship Date`), date format (`14.06.2026`, `14 Jun 2026`),
and table styling (ruled grid, zebra striping, borderless).

**The PDFs carry more than the schema captures** — totals, tax lines,
payment terms, remit-to blocks, bill-to addresses, delivery narrative. That
is deliberate. If the page contained only the seven schema fields,
extraction would be a lookup and the eval would prove nothing. The
distractors are what make a passing score meaningful.

## Ground truth

`ground_truth.json` holds one record per invoice. `expected_output` matches
your schema exactly — same keys, same nesting, same types, dates as ISO
strings:

```json
{
  "pdf": "pdfs/INV-2026-4100.pdf",
  "layout_variant": 0,
  "line_count": 2,
  "expected_output": {
    "line_items": [{"part_number": "30112", "quantity": 250, "unit_price": 349.38}],
    "vendor_id": "5a2c1ca6-...",
    "invoice_id": "77806509-...",
    "expected_delivery_date": null,
    "purchase_order_id": "2f7befe9-...",
    "delivery_dates": ["2026-07-17", "2026-09-30"],
    "vendor_info": {"name": "Meridian Components Pte Ltd", "contact": "accounts@..."}
  }
}
```

Every field was verified recoverable from the rendered page text with
`pdfplumber` — all 10 invoices pass, no missing identifiers or prices.

Generation is deterministic (`SEED = 20260907`). Re-running reproduces the
same invoices, so ground truth stays valid. Change `specs` in the script to
alter the mix; regenerate both PDFs and ground truth together.

## Two interpretive calls I had to make

Your schema has `expected_delivery_date` (singular, `None`) alongside
`delivery_dates` (a list of two, matching two line items). I read that as:

- `expected_delivery_date` — one header-level promised date, nullable,
  rendered as a field in the invoice metadata block
- `delivery_dates` — one date per line item, positionally parallel to
  `line_items`, rendered in the line table

If you meant something else, say so and I'll regenerate.

## Four things worth changing in the schema

These matter because this schema feeds the three-way matcher, where a
representation bug becomes a false variance.

**`unit_price` as float will produce phantom discrepancies.** `0.1 + 0.2`
is not `0.3` in binary floating point. Multiply a float unit price by a
quantity of 250 and compare it against a PO line computed on a different
path, and you'll get variances of a few cents that no human can explain. Use
`Decimal`, or store integer minor units (cents). This is the single change
I'd make first — the generator carries `Decimal` internally and only casts
to `float` at the schema boundary, so switching is a one-line change.

**`delivery_dates` parallel to `line_items` will desync silently.** If
extraction drops or merges a line, the two arrays fall out of alignment and
every subsequent date attaches to the wrong part. Nothing raises. Nesting
the date inside each line item makes the coupling structural instead of
positional.

**No currency field.** Two of the sample vendors bill in EUR and GBP. Without
currency on the invoice, the matcher compares a number against a PO number
and reports a variance that is really an FX difference — or worse, reports
no variance when there is one.

**No unit of measure.** This is the case-versus-each problem. A supplier
invoicing 10 cases against a PO for 10 each is a 12x overbilling that looks
like a perfect quantity match. The `UnitOfMeasureMismatchError` in
`exceptions.py` can't fire if UOM never reaches the matcher. The PDFs do
carry a UOM column, so the data is there to extract when you want it.

## Suggested next step

Extend the generator to also emit matching PO and goods receipt records —
same identifiers, with seeded discrepancies (price variance above and below
tolerance, over- and under-delivery, missing receipt, duplicate invoice
number). That turns this from an extraction fixture into the full
three-way-match eval set, and the false-auto-approve metric becomes
computable.

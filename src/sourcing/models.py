from pydantic import BaseModel
from typing import TypedDict

class ReplacementRequest(BaseModel):
    part_number: str
    quantity: int
    unit_price: float
    vendor_name: str


class SupplierOffer(BaseModel):
    supplier_name: str
    supplier_email: str
    part_number: str
    available_quantity: int
    unit_price: float
    lead_time_days: int | None = None


class EmailDraft(BaseModel):
    subject: str
    body: str


class ItemMatchResult(BaseModel):
    #   To implement Literal["MATCH", "NO_MATCH", "UNCERTAIN"] if time allows
    is_match: bool
    confidence: float
    reason: str


class ValidatedOffer(BaseModel):
    offer: SupplierOffer
    match: ItemMatchResult


class SourcingState(TypedDict, total=False):
    request: ReplacementRequest

    offers: list[SupplierOffer]
    valid_offers: list[ValidatedOffer]
    ranked_offers: list[ValidatedOffer]

    recommended_offer: ValidatedOffer

    email_draft: EmailDraft

    # approval_decision: bool

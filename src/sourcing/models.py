from pydantic import BaseModel, EmailStr
from typing import TypedDict

class ReplacementRequest(BaseModel):
    order_item_id: int
    part_number: str
    description: str
    unit_price: float
    quantity: int
    currency: str


class SupplierOffer(BaseModel):
    supplier_name: str
    supplier_email: str

    part_number: str
    description: str

    unit_price: float
    currency: str
    available_quantity: int

    lead_time_days: int | None = None


class EmailDraft(BaseModel):
    to: EmailStr
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

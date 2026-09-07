from .models import SourcingState, ItemMatchResult, ValidatedOffer, EmailDraft
from .tools import search_suppliers
from .llm import validate_item_match, draft_purchase_email


# MAX_VALIDATION_CANDIDATES = 10

def search_supplier_node(state: SourcingState):
    offers = search_suppliers(state["request"])
    return {
        "offers": offers
    }


def validate_offers_node(state: SourcingState):
    request = state["request"]
    validated = []

    for offer in state["offers"]:
        if offer.available_quantity < request.quantity:
            continue
        if request.part_number and offer.part_number and request.part_number.lower() == offer.part_number.lower():
            match = ItemMatchResult(
                is_match=True,
                confidence=1.0,
                reason="Exact part number match."
            )

        else:
            match = validate_item_match(request, offer)

        if match.is_match:
            validated.append(ValidatedOffer(offer=offer, match=match))

    return {
        "valid_offers": validated
    }


def rank_offers_node(state: SourcingState):
    ranked = sorted(state["valid_offers"], key=lambda x: x.offer.unit_price)

    if not ranked:
        return {
            "ranked_offers": []
        }

    return {
        "ranked_offers": ranked,
        "recommended_offer": ranked[0]
    }


def draft_email_node(state: SourcingState):
    request = state["request"]
    recommendation = state["recommended_offer"]

    draft = draft_purchase_email(request, recommendation)

    return {
        "email_draft": draft,
    }

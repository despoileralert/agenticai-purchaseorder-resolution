from typing import TypedDict

# Temporary
from sourcing.models import ReplacementRequest


class OrchestratorState(TypedDict, total=False):
    invoice_id: int
    order_id: int
    order_item_id: int

    tracking_status: str

    replacement_request: ReplacementRequest

    replacement_result: dict

    error: str

from langgraph.graph import StateGraph, START, END

from .nodes import *

builder = StateGraph(SourcingState)

builder.add_node("search_suppliers", search_supplier_node)
builder.add_node("validate_offers", validate_offers_node)
builder.add_node("rank_offers", rank_offers_node)
builder.add_node("draft_email", draft_email_node)

builder.add_edge(START, "search_suppliers")
builder.add_edge("search_suppliers", "validate_offers")
builder.add_edge("validate_offers", "rank_offers")
builder.add_edge("rank_offers", "draft_email")
builder.add_edge("draft_email", END)

sourcing_graph = builder.compile()

from langgraph.graph import StateGraph, START, END

from .models import OrchestratorState

from .nodes import invoice_agent_node, tracking_agent_node, sourcing_agent_node, route_tracking_result


builder = StateGraph(OrchestratorState)


builder.add_node("invoice_agent", invoice_agent_node)
builder.add_node("tracking_agent", tracking_agent_node)
builder.add_node("supplier_sourcing", sourcing_agent_node)


builder.add_edge(START, "invoice_agent")
builder.add_edge("invoice_agent", "tracking_agent")
builder.add_conditional_edges("tracking_agent", route_tracking_result, {
    "supplier_sourcing": "supplier_sourcing",
    "finish": END
})
builder.add_edge("supplier_sourcing", END)

orchestrator = builder.compile()

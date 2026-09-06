from langgraph.graph import StateGraph, START, END

from .models import OrchestratorState

from .nodes import tracking_agent_node, sourcing_agent_node, route_tracking_result


builder = StateGraph(OrchestratorState)


builder.add_node("tracking_agent", tracking_agent_node)
builder.add_node("supplier_sourcing", sourcing_agent_node)


builder.add_edge(START, "tracking_agent")
builder.add_conditional_edges("tracking_agent", route_tracking_result, {
    "supplier_sourcing": "supplier_sourcing",
    "finish": END
})
builder.add_edge("supplier_sourcing", END)

orchestrator = builder.compile()

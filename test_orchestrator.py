from orchestration.graph import orchestrator


result = orchestrator.invoke({})


print("\nFinal state:")
print(result)

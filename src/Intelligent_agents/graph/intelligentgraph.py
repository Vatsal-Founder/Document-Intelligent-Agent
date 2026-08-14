from langgraph.graph import StateGraph,START,END
from Intelligent_agents.node import supervisor_node,route_next, financial_node,policy_node
from Intelligent_agents.state import DocumentState



graph=StateGraph(DocumentState)

graph.add_node("supervisor",supervisor_node)
graph.add_node("policy_agent",policy_node)
graph.add_node("financial_agent",financial_node)

graph.add_edge(START, "supervisor")
graph.add_conditional_edges ("supervisor", route_next , {"financial_agent":"financial_agent",
                                                            "policy_agent":"policy_agent",
                                                            END:END} )


graph.add_edge("financial_agent","supervisor")
graph.add_edge("policy_agent","supervisor")

workdone= graph.compile()

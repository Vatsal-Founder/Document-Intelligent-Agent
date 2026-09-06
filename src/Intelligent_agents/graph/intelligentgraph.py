from langgraph.graph import StateGraph,START,END
from Intelligent_agents.node import supervisor_node,route_next, financial_node,hitl_node,policy_node,next_grade,grader_node
from Intelligent_agents.state import DocumentState

from langgraph.checkpoint.memory import InMemorySaver



checkpointer = InMemorySaver()

graph=StateGraph(DocumentState)

graph.add_node("supervisor",supervisor_node)
graph.add_node("policy_agent",policy_node)
graph.add_node("financial_agent",financial_node)
graph.add_node('grader_node',grader_node)
graph.add_node("hitl",hitl_node)

graph.add_edge(START, "supervisor")
graph.add_conditional_edges ("supervisor", route_next , {"financial_agent":"financial_agent",
                                                            "policy_agent":"policy_agent",
                                                            END:END} )


graph.add_edge("financial_agent","supervisor")
graph.add_edge("policy_agent","grader_node")
graph.add_conditional_edges("grader_node",next_grade,{
    "supervisor": "supervisor",
    "policy_agent": "policy_agent",
    "hitl": "hitl",
})
graph.add_edge("hitl", END)  


workdone= graph.compile(checkpointer=checkpointer)

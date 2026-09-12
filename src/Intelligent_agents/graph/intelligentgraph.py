from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.memory import InMemorySaver

from Intelligent_agents.node import (
    supervisor_node, route_next, grader_node, next_grade, hitl_node,
    make_policy, make_finacial
)
from Intelligent_agents.state import DocumentState
from Intelligent_agents.agents import build_agents

checkpointer = InMemorySaver()

async def build_graph():
    # load MCP tools + build agents (async)
    financial_agent, policy_agent = await build_agents()

    # build the two agent-dependent nodes from the factories
    policy_node = make_policy(policy_agent)
    financial_node = make_finacial(financial_agent)

    graph = StateGraph(DocumentState)
    graph.add_node("supervisor", supervisor_node)
    graph.add_node("policy_agent", policy_node)
    graph.add_node("financial_agent", financial_node)
    graph.add_node("grader_node", grader_node)
    graph.add_node("hitl", hitl_node)

    graph.add_edge(START, "supervisor")
    graph.add_conditional_edges("supervisor", route_next, {
        "financial_agent": "financial_agent",
        "policy_agent": "policy_agent",
        END: END,
    })
    graph.add_edge("financial_agent", "supervisor")
    graph.add_edge("policy_agent", "grader_node")
    graph.add_conditional_edges("grader_node", next_grade, {
        "supervisor": "supervisor",
        "policy_agent": "policy_agent",
        "hitl": "hitl",
    })
    graph.add_edge("hitl", END)

    return graph.compile(checkpointer=checkpointer)
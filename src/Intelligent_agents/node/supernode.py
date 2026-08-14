from langgraph.graph import StateGraph,START,END
from pydantic import BaseModel
from langchain_core.messages import  HumanMessage, SystemMessage


from Intelligent_agents.model import supervisor_model, policy_model, financial_model
from Intelligent_agents.state import DocumentState, RouteDecision, PolicyResult, FinancialResult
from Intelligent_agents.agents import policy_agent, Financialagent


# ---------------------
## SUPERVISOR NODE
#---------------------

ROUTER_SYSTEM = """You coordinate specialist agents to answer loan queries.

On each turn, decide the next step:
- financial_agent: for account data and calculations (balances, rates, payments, overpayment impact)
- policy_agent: for contract terms (overpayment rules, penalties, payment breaks, early repayment)
- FINISH: when the conversation already contains enough information to fully answer the user's question

For a question needing both contract terms AND account data, route to each agent in turn,
then FINISH. Do not route to the same agent twice for the same information.
Extract the loan ID if mentioned."""

def supervisor_node(state: DocumentState) -> dict:
    decider = supervisor_model.with_structured_output(RouteDecision)
    decision = decider.invoke([
        SystemMessage(content=ROUTER_SYSTEM),
        *state["messages"],          # sees the full conversation incl. agent outputs
    ])

    if decision.next_agent == "FINISH":
        # synthesize final answer from accumulated results
        final = supervisor_model.invoke([
            SystemMessage(content="Synthesize a final answer for the user from the conversation above."),
            *state["messages"],
        ])
        return {"next_agent": "FINISH", "messages": [final]}

    return {"next_agent": decision.next_agent, "loan_id": decision.loan_id}

def route_next(state: DocumentState) -> str:
    if state["next_agent"] == "FINISH":
        return END
    return state["next_agent"]


# ---------------------
## POLICY NODE
#---------------------


def policy_node(state: DocumentState) -> dict:
    result = policy_agent.invoke({"messages": state["messages"]})
    agent_answer = result["messages"][-1].content

    structurer = policy_model.with_structured_output(PolicyResult)
    structured = structurer.invoke([
        HumanMessage(content=f"Extract the answer and cited clause from this response:\n{agent_answer}")
    ])

    return {
        "messages": result["messages"],
        "policy_result": structured,  
    }


# ---------------------
## FINANCIAL NODE
#---------------------


def financial_node(state: DocumentState) -> dict:
    result = Financialagent.invoke({"messages": state["messages"]})
    agent_answer = result["messages"][-1].content

    structurer = financial_model.with_structured_output(FinancialResult)
    structured = structurer.invoke([
        HumanMessage(content=f"Extract the answer and the key numeric value from this response:\n{agent_answer}")
    ])

    return {
        "messages": result["messages"],
        "financial_result": structured,
    }
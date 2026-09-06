from langgraph.graph import StateGraph,START,END
from pydantic import BaseModel
from langchain_core.messages import  HumanMessage, SystemMessage, AIMessage
from langgraph.types import interrupt,Command


from Intelligent_agents.model import supervisor_model, policy_model, financial_model, grader_model
from Intelligent_agents.state import DocumentState, RouteDecision, PolicyResult, FinancialResult, GradeResult
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
    messages = state["messages"]

    # on retry, inject a multi-query instruction
    if state.get("grade_attempts", 0) > 0:
        retry_note = HumanMessage(content=
            "The previous attempt was graded insufficient. Decompose this question "
            "into 2-3 more specific sub-questions, search the document for each, and "
            "synthesize a more complete answer.")
        messages = messages + [retry_note]

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

#-----------------
# Retrival Grade
#----------------
GRADER_SYSTEM = """You judge whether a policy answer sufficiently addresses the user's
question. Return 'sufficient' only if the answer clearly and confidently answers the
question and is grounded in a cited clause. Return 'insufficient' if the answer is
uncertain, declines, states information is missing, or lacks a citation."""

def grader_node(state: DocumentState) -> dict:
    question = state["messages"][0].content
    pr = state["policy_result"]
    retrieved = f"Answer: {pr.answer}\nCited clause: {pr.cited_clause}"

    grader = grader_model.with_structured_output(GradeResult)
    result = grader.invoke([
        SystemMessage(content=GRADER_SYSTEM),
        HumanMessage(content=f"Question: {question}\n\n{retrieved}"),
    ])
    attempts = state.get("grade_attempts", 0) + 1
    return {"retrieval_grade": result.grade, "grade_attempts": attempts}

def next_grade(state: DocumentState) -> str:
    if state["retrieval_grade"] == "sufficient":
        return "supervisor"
    if state["grade_attempts"] >= 2:
        return "hitl"              # tried twice, escalate to human
    return "policy_agent"          # retry with multi-query
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


# ---------------------
## Human in the loop Node
#---------------------


def hitl_node(state: DocumentState) -> dict:
    proposed = state["policy_result"].answer
    decision = interrupt({
        "question": state["messages"][0].content,
        "proposed_answer": proposed,
        "reason": "Low confidence after 2 retrieval attempts — please review.",
    })

    if decision == "yes":
        final = AIMessage(content=(
            f"{proposed}\n\n"
            "_Note: this response was flagged as low-confidence by the system and "
            "approved after human review._"
        ))
    else:
        final = AIMessage(content=(
            "After review, this question couldn't be answered with confidence from the "
            "available loan documents, and the proposed response was not approved. "
            "Please rephrase your question, or contact a loan advisor for clarification "
            "on this specific matter."
        ))

    return {"human_decision": decision, "messages": [final]}
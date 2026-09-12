from langgraph.graph import StateGraph,START,END
from pydantic import BaseModel
from langchain_core.messages import  HumanMessage, SystemMessage, AIMessage
from langgraph.types import interrupt,Command


from Intelligent_agents.model import supervisor_model, policy_model, financial_model, grader_model, ROUTER_SYSTEM, GRADER_SYSTEM
from Intelligent_agents.state import DocumentState, RouteDecision, PolicyResult, FinancialResult, GradeResult
from Intelligent_agents.agents import build_agents


# ---------------------
## SUPERVISOR NODE
#---------------------



async def supervisor_node(state: DocumentState) -> dict:
    decider = supervisor_model.with_structured_output(RouteDecision)
    decision = await decider.ainvoke([
        SystemMessage(content=ROUTER_SYSTEM),
        *state["messages"],          # sees the full conversation incl. agent outputs
    ])

    if decision.next_agent == "FINISH":
        # synthesize final answer from accumulated results
        final = await supervisor_model.ainvoke([
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

def make_policy(policy_agent):
        
    async def policy_node(state: DocumentState) -> dict:
        messages = state["messages"]

        # on retry, inject a multi-query instruction
        if state.get("grade_attempts", 0) > 0:
            retry_note = HumanMessage(content=
                "The previous attempt was graded insufficient. Decompose this question "
                "into 2-3 more specific sub-questions, search the document for each, and "
                "synthesize a more complete answer.")
            messages = messages + [retry_note]

        result = await policy_agent.ainvoke({"messages": messages}) 
        agent_answer = result["messages"][-1].content

        structurer = policy_model.with_structured_output(PolicyResult)
        structured = await structurer.ainvoke([
            HumanMessage(content=f"Extract the answer and cited clause from this response:\n{agent_answer}")
        ])

        return {
            "messages": result["messages"],
            "policy_result": structured,  
        }
    return policy_node

#-----------------
# Retrival Grade
#----------------

async def grader_node(state: DocumentState) -> dict:
    question = state["messages"][0].content
    pr = state["policy_result"]
    retrieved = f"Answer: {pr.answer}\nCited clause: {pr.cited_clause}"

    grader = grader_model.with_structured_output(GradeResult)
    result = await grader.ainvoke([
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

def make_finacial(Financialagent):
    async def financial_node(state: DocumentState) -> dict:
        result = await Financialagent.ainvoke({"messages": state["messages"]})
        agent_answer = result["messages"][-1].content

        structurer = financial_model.with_structured_output(FinancialResult)
        structured = await structurer.ainvoke([
            HumanMessage(content=f"Extract the answer and the key numeric value from this response:\n{agent_answer}")
        ])

        return {
            "messages": result["messages"],
            "financial_result": structured,
        }
    return financial_node


# ---------------------
## Human in the loop Node
#---------------------


async def hitl_node(state: DocumentState) -> dict:
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
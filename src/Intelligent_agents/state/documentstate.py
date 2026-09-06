from langgraph.graph import StateGraph,START,END
from pydantic import BaseModel
from langchain_core.messages import BaseMessage, HumanMessage, SystemMessage
from langgraph.graph.message import add_messages
from pydantic import BaseModel, Field
from typing import TypedDict, Annotated,List,Literal, Optional


class RouteDecision(BaseModel):
    next_agent: Literal["financial_agent", "policy_agent", "FINISH"] = Field(
        description="Which agent to call next, or FINISH if enough information "
        "has been gathered to answer the user's question."
    )
    loan_id: str | None = Field(
        description="The loan ID mentioned in the query, e.g. 'L001'. Null if none."
    )

class PolicyResult(BaseModel):
    answer: str = Field(description="The answer to the policy question")
    cited_clause: str = Field(description="The specific clause relied on, e.g. 'Clause 4.1'")


class FinancialResult(BaseModel):
    answer: str = Field(description="The answer to the financial question")
    value: float | None = Field(
        default=None,
        description="The key numeric result if the answer contains one "
        "(e.g. a balance or monthly payment). Null if not applicable."
    )

class GradeResult(BaseModel):
    grade: Literal["sufficient", "insufficient"] = Field(
        description="'sufficient' if the retrieved clauses clearly and unambiguously "
        "answer the question; 'insufficient' if they don't, or if the answer is "
        "ambiguous or requires clauses not present."
    )

class DocumentState(TypedDict):

    messages: Annotated[list[BaseMessage], add_messages]
    next_agent: str | None
    loan_id: str | None
    policy_result: PolicyResult | None
    financial_result: FinancialResult | None
    retrieval_grade: Literal["sufficient", "insufficient"] | None


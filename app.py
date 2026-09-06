from fastapi import FastAPI
from pydantic import BaseModel
from pydantic import BaseModel
from langgraph.types import Command
from Intelligent_agents.graph import workdone

app = FastAPI(title="Document Intelligence Agent")

class Query(BaseModel):
    question: str
    thread_id: str

class Resume(BaseModel):
    thread_id: str
    decision: str



class Answer(BaseModel):
    answer: str

@app.post("/query", response_model=Answer)
async def ask(query: Query):
    config = {"configurable": {"thread_id": query.thread_id}}
    result = workdone.invoke(
        {"messages": [("user", query.question)], "grade_attempts": 0},
        config=config,
    )

     # did it pause at the interrupt?
    if "__interrupt__" in result:
        interrupt_data = result["__interrupt__"][0].value
        return {
            "status": "needs_review",
            "thread_id": query.thread_id,
            "proposed_answer": interrupt_data["proposed_answer"],
            "reason": interrupt_data["reason"],
        }

    # normal completion
    return {
        "status": "complete",
        "answer": result["messages"][-1].content,
    }

@app.post("/resume")
async def resume(body: Resume):
    config = {"configurable": {"thread_id": body.thread_id}}
    final = workdone.invoke(Command(resume=body.decision), config=config)
    return {
        "status": "complete",
        "answer": final["messages"][-1].content,
    }


@app.get("/health")
async def health():
    return {"status": "ok"}
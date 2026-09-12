from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from langgraph.types import Command
from Intelligent_agents.graph import build_graph

# holds the compiled graph, built at startup
state = {"graph": None}

@asynccontextmanager
async def lifespan(app: FastAPI):
    state["graph"] = await build_graph()   # build once when server starts (loads MCP tools)
    yield

app = FastAPI(title="Document Intelligence Agent", lifespan=lifespan)

class Query(BaseModel):
    question: str
    thread_id: str

class Resume(BaseModel):
    thread_id: str
    decision: str

@app.post("/query")
async def ask(query: Query):
    workdone = state["graph"]
    config = {"configurable": {"thread_id": query.thread_id}}
    try:
        result = await workdone.ainvoke(          # ainvoke — async
            {"messages": [("user", query.question)], "grade_attempts": 0},
            config=config,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail="An error occurred processing your query.")

    if "__interrupt__" in result:
        interrupt_data = result["__interrupt__"][0].value
        return {
            "status": "needs_review",
            "thread_id": query.thread_id,
            "proposed_answer": interrupt_data["proposed_answer"],
            "reason": interrupt_data["reason"],
        }

    return {"status": "complete", "answer": result["messages"][-1].content}

@app.post("/resume")
async def resume(body: Resume):
    workdone = state["graph"]
    config = {"configurable": {"thread_id": body.thread_id}}
    try:
        final = await workdone.ainvoke(Command(resume=body.decision), config=config)
    except Exception as e:
        raise HTTPException(status_code=500, detail="An error occurred resuming your query.")
    return {"status": "complete", "answer": final["messages"][-1].content}

@app.get("/health")
async def health():
    return {"status": "ok"}
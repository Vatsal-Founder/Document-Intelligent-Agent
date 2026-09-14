import os
import sqlite3
from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException, Request
from pydantic import BaseModel
from langgraph.types import Command
from Intelligent_agents.graph import build_graph
from Intelligent_agents.agents.sub_agents import client as mcp_client
from Intelligent_agents.config import DB_PATH

from fastapi.middleware.cors import CORSMiddleware
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

# holds the compiled graph, built at startup
state = {"graph": None}

@asynccontextmanager
async def lifespan(app: FastAPI):
    # open the MCP session once and keep it alive for the app's lifetime —
    # every tool call from every request reuses this one subprocess instead
    # of spawning a new one per call
    async with mcp_client.session("loan-tools") as mcp_session:
        state["graph"] = await build_graph(mcp_session)   # build once when server starts (loads MCP tools)
        yield

app = FastAPI(title="Document Intelligence Agent", lifespan=lifespan)

limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# set ALLOWED_ORIGINS on the deployed backend to the deployed frontend's
# origin (comma-separated for more than one); defaults to the local Vite
# dev server so nothing needs to change for local development
ALLOWED_ORIGINS = os.environ.get("ALLOWED_ORIGINS", "http://localhost:5173,http://localhost:3000").split(",")

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_methods=["*"],
    allow_headers=["*"],
)

class Query(BaseModel):
    question: str
    thread_id: str

class Resume(BaseModel):
    thread_id: str
    decision: str

@app.post("/query")
@limiter.limit("10/hour")
async def ask(request: Request, query: Query):
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
@limiter.limit("10/hour")
async def resume(request: Request, body: Resume):
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

@app.get("/loans")
async def list_loans():
    con = sqlite3.connect(f"file:{DB_PATH}?mode=ro", uri=True)
    try:
        cursor = con.cursor()
        cursor.execute("""
            SELECT l.loan_id, c.name, l.product_type, l.term_months, c.employment_type, l.start_date
            FROM loans l JOIN customers c ON l.customer_id = c.customer_id
            ORDER BY l.loan_id
        """)
        rows = cursor.fetchall()
    finally:
        con.close()
    return [
        {
            "loan_id": r[0],
            "customer_name": r[1],
            "product_type": r[2],
            "term_years": r[3] // 12,
            "employment_type": r[4],
            "start_date": r[5],
        }
        for r in rows
    ]
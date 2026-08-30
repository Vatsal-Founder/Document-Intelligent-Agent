from fastapi import FastAPI
from pydantic import BaseModel
from Intelligent_agents.graph import workdone

app = FastAPI(title="Document Intelligence Agent")

class Query(BaseModel):
    question: str

class Answer(BaseModel):
    answer: str

@app.post("/query", response_model=Answer)
async def ask(query: Query):
    result = workdone.invoke({"messages": [("user", query.question)]})
    return {"answer": result["messages"][-1].content}

@app.get("/health")
async def health():
    return {"status": "ok"}
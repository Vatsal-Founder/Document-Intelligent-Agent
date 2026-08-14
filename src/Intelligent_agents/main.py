# src/Intelligent_agents/main.py
from Intelligent_agents.graph import workdone

def run_query(question: str):
    result = workdone.invoke({"messages": [("user", question)]})
    return result["messages"][-1].content

if __name__ == "__main__":
    # quick manual test: python -m Intelligent_agents.main
    print(run_query("What's the balance on L001?"))
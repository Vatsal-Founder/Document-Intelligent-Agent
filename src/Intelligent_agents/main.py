# src/Intelligent_agents/main.py

from Intelligent_agents.graph import workdone 

def run_query(question: str):
    for step in workdone.stream({
        "messages": [("user", question)],
        "grade_attempts": 0,
    }):
        print(step)

if __name__ == "__main__":
    print("--- Test 1: should be insufficient (retry loop) ---")
    run_query("For L003, what is the exact euro cost of early repayment on a Tuesday?")
# evals/run_eval.py
import asyncio
from Intelligent_agents.graph import build_graph
from evals.eval_set import EVAL_SET

from Intelligent_agents.agents.sub_agents import client as mcp_client

async def run():
    async with mcp_client.session("loan-tools") as mcp_session:
            graph = await build_graph(mcp_session)   # build once when server starts (loads MCP tools)

            results = []

            for i, item in enumerate(EVAL_SET):
                config = {"configurable": {"thread_id": f"eval-{i}"}}
                r = await graph.ainvoke(
                    {"messages": [("user", item["question"])], "grade_attempts": 0},
                    config=config,
                )

                # escalation queries: pass if it returned needs_review (interrupt)
                if item["type"] == "escalation":
                    passed = "__interrupt__" in r
                else:
                    answer = r["messages"][-1].content.lower().replace(",", "").replace("€", "")
                    passed = item["expected"].lower().replace(",", "") in answer

                results.append({"type": item["type"], "q": item["question"],
                                "expected": item["expected"], "passed": passed})
                print(f"{'✓' if passed else '✗'} [{item['type']}] {item['question'][:60]}")

                if not passed:
                    print(f"   expected: {item['expected']}")
                    print(f"   got: {r['messages'][-1].content[:200]}")

            # summary
            total = len(results)
            passed = sum(r["passed"] for r in results)
            print(f"\n{passed}/{total} passed ({100*passed//total}%)")

            # by type
            from collections import defaultdict
            by_type = defaultdict(lambda: [0, 0])
            for r in results:
                by_type[r["type"]][0] += r["passed"]
                by_type[r["type"]][1] += 1
            print("\nBy type:")
            for t, (p, tot) in by_type.items():
                print(f"  {t}: {p}/{tot}")

if __name__ == "__main__":
    asyncio.run(run())
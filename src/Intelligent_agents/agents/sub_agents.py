from Intelligent_agents.model import agentmodel, policy_model
from Intelligent_agents.model import finacial_prompte, policy_prompt
from langchain.agents import create_agent
from langchain_mcp_adapters.client import MultiServerMCPClient
from langchain_mcp_adapters.tools import load_mcp_tools
import os
import sys
from mcp import ClientSession
from pathlib import Path

SERVER_PATH = str(Path(__file__).resolve().parent.parent / "mcp_server" / "server.py")

client = MultiServerMCPClient({
    "loan-tools": {
        "command": sys.executable,
        "args": [SERVER_PATH],
        "transport": "stdio",
        "env": dict(os.environ),
    }
})

async def build_agents(mcp_session: ClientSession):
    """Build both agents, binding their tools to the given (already-open) MCP session.

    The caller owns the session's lifetime (opened once at app startup) — this
    function does not open or close it, since the agents built here get reused
    for every request for as long as the app runs.
    """
    all_tools = await load_mcp_tools(mcp_session)

    financial_tools = [t for t in all_tools if t.name in
        ("sql_db_list_tables", "sql_db_query",
         "monthly_payment", "lump_sum_recalc", "dti", "early_repayment_charge")]
    policy_tools = [t for t in all_tools if t.name == "retrieve_doc"]

    financial_agent = create_agent(
        model=agentmodel,
        tools=financial_tools,
        system_prompt=finacial_prompte,
    )
    policy_agent = create_agent(
        model=policy_model,
        tools=policy_tools,
        system_prompt=policy_prompt,
    )
    return financial_agent, policy_agent
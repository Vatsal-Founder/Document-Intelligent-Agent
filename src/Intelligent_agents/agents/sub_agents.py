from Intelligent_agents.model import agentmodel, policy_model
from Intelligent_agents.model import finacial_prompte, policy_prompt
from langchain.agents import create_agent
from langchain_mcp_adapters.client import MultiServerMCPClient

client = MultiServerMCPClient({
    "loan-tools": {
        "command": "python",
        "args": ["/Users/vatsal/Machine Learning/Gen AI/AIproject/src/Intelligent_agents/mcp_server/server.py"],
        "transport": "stdio",
    }
})

async def build_agents():
    """Load tools from the MCP server and build both agents. Async because MCP tool loading is async."""
    all_tools = await client.get_tools()

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
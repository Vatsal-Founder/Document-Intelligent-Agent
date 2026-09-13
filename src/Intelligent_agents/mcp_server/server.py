import os
os.environ["HF_HUB_OFFLINE"] = "1"
os.environ["TRANSFORMERS_OFFLINE"] = "1"
os.environ["HF_HUB_DISABLE_PROGRESS_BARS"] = "1"

import logging, sys
logging.basicConfig(level=logging.WARNING, stream=sys.stderr)

from mcp.server.fastmcp import FastMCP
import sqlite3
from Intelligent_agents.config import DB_PATH, CHROMA_PATH
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_chroma import Chroma
import asyncio


mcp= FastMCP("Intelligent Finacial MCP")

@mcp.tool()
async def sql_db_list_tables() -> str:
    """Input is an empty string, output is a comma-separated list of tables in the database."""
    con = sqlite3.connect(f"file:{DB_PATH}?mode=ro", uri=True)
    try:
        cursor = con.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = [row[0] for row in cursor.fetchall() if not row[0].startswith("sqlite_")]
        return ", ".join(tables)
    finally:
        con.close()

@mcp.tool()
async def sql_db_query(query: str) -> str:
    """Input to this tool is a detailed and correct SQL query, output is a result from the database.
    If the query is not correct, an error message will be returned.
    If an error is returned, rewrite the query, check the query, and try again."""
    # --- read-only guardrail: enforce BEFORE executing ---
    q = query.strip().lower()
    if not q.startswith("select"):
        return "Error: only SELECT queries are permitted."
    forbidden = ("insert", "update", "delete", "drop", "alter", "create", "replace", "truncate")
    if any(word in q.split() for word in forbidden):
        return "Error: query contains a forbidden keyword. Read-only access only."

    con = sqlite3.connect(f"file:{DB_PATH}?mode=ro", uri=True)
    try:
        cursor = con.cursor()
        cursor.execute(query)
        return str(cursor.fetchall())
    except Exception as e:
        return f"Error: {e}"
    finally:
        con.close()



#calculation tool
@mcp.tool()
async def monthly_payment(principal: float, annual_rate: float, term_months: int) -> str:
    """Calculates the monthly repayment for a loan given principal, annual rate, and term in months.
    USE WHEN: someone asks what the monthly payment is, or would be, for a given
    loan amount, rate, and term. Requires all three inputs — get them from the
    database first if they aren't provided in the question."""

    if annual_rate > 1:
        annual_rate = annual_rate / 100

    r = annual_rate / 12
    n = term_months
    result = principal / n if r == 0 else principal * (r*(1+r)**n) / ((1+r)**n - 1)
    return str(round(result, 2))

@mcp.tool()
async def lump_sum_recalc(outstanding_balance: float, annual_rate: float, remaining_months: int, lump_sum: float) -> str:
    """Recalculates the monthly payment after a one-off overpayment, keeping the term fixed.
    USE WHEN: someone asks how an overpayment or lump-sum payment would change their
    monthly payment. Requires current balance, rate, and remaining term — fetch these
    from the database for the specific loan before calling."""

    new_balance = outstanding_balance - lump_sum
    if new_balance <= 0:
        return str({"new_monthly_payment": 0, "note": "loan fully repaid"})
    if annual_rate > 1:
        annual_rate = annual_rate / 100
    r = annual_rate / 12
    n = remaining_months
    new_payment = new_balance / n if r == 0 else new_balance * (r*(1+r)**n) / ((1+r)**n - 1)
    return str({"new_balance": new_balance, "new_monthly_payment": round(new_payment, 2)})


@mcp.tool()
async def dti(total_monthly_debt: float, gross_monthly_income: float) -> str:
    """Calculates debt-to-income ratio as a percentage from total monthly debt and gross monthly income.
    USE WHEN: someone asks about affordability, or whether they can take on more debt.
    Requires their income and total monthly debt payments."""

    if gross_monthly_income <= 0:
        return str({"error": "income must be positive"})
    return str(round((total_monthly_debt / gross_monthly_income) * 100, 2))

@mcp.tool()
async def early_repayment_charge(outstanding_balance: float, annual_rate: float, months: int) -> str:
    """Calculates ERC as (months) of gross interest on the balance.
    The number of months comes from the loan's specific early-repayment clause."""
    if annual_rate > 1:
        annual_rate = annual_rate / 100
    return str(round(outstanding_balance * annual_rate / 12 * months, 2))


embeddings=HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")
vectorstore = Chroma(
    persist_directory= f"{CHROMA_PATH}",
    embedding_function=embeddings,
)


@mcp.tool()
async def retrieve_doc(query: str, loan_id: str) -> str:
    """Retrieves relevant clauses from a specific customer's loan agreement.
    USE WHEN: the question is about what the CONTRACT permits, requires, or states —
    overpayment rules, penalties, early-repayment terms, payment-break eligibility,
    rate-change notice, missed-payment consequences. Requires the loan_id to filter
    to the correct customer's agreement.
    DO NOT use for account figures like current balance or interest rate — those come
    from the database, not the contract."""
    retriver = vectorstore.as_retriever(
        search_type="mmr",
        search_kwargs={"k": 3, "fetch_k": 15, "filter": {"loan_id": loan_id}}
    )
    docs = retriver.invoke(query)
    if not docs:
        return "No relevant clauses found for this loan."
    return "\n\n".join(d.page_content for d in docs)

if __name__=="__main__":
    mcp.run()
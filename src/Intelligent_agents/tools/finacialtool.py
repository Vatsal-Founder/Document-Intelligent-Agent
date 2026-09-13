import sqlite3
from langchain.tools import tool
from langchain_groq import ChatGroq
from Intelligent_agents.model import agentmodel
from Intelligent_agents.config import DB_PATH



#SQL TOOl

@tool
def sql_db_list_tables() -> str:
    """Input is an empty string, output is a comma-separated list of tables in the database."""
    con = sqlite3.connect(f"file:{DB_PATH}?mode=ro", uri=True)
    try:
        cursor = con.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = [row[0] for row in cursor.fetchall() if not row[0].startswith("sqlite_")]
        return ", ".join(tables)
    finally:
        con.close()

@tool
def sql_db_query(query: str) -> str:
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
'''
@tool
def sql_db_query_checker(query: str) -> str:
    """Use this tool to double check if your query is correct before executing it.
    Always use this tool before executing a query with sql_db_query!"""
    trigger_prompt = """{query}
Double check the sqlite query above for common mistakes, including:
- Using NOT IN with NULL values
- Using UNION when UNION ALL should have been used
- Using BETWEEN for exclusive ranges
- Data type mismatch in predicates
- Properly quoting identifiers
- Using the correct number of arguments for functions
- Casting to the correct data type
- Using the proper columns for joins

If there are any of the above mistakes, rewrite the query. If there are no mistakes, just reproduce the original query.

Output the final SQL query only.

SQL Query: """.format(query=query)

    response = agentmodel.invoke(trigger_prompt)
    return response.text.strip()

'''
#calculation tool
@tool
def monthly_payment(principal: float, annual_rate: float, term_months: int) -> str:
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

@tool
def lump_sum_recalc(outstanding_balance: float, annual_rate: float, remaining_months: int, lump_sum: float) -> str:
    """Recalculates the monthly payment after a one-off overpayment, keeping the term fixed.
    USE WHEN: someone asks how an overpayment or lump-sum payment would change their
    monthly payment. Requires current balance, rate, and remaining term — fetch these
    from the database for the specific loan before calling."""

    new_balance = outstanding_balance - lump_sum
    if new_balance <= 0:
        return {"new_monthly_payment": 0, "note": "loan fully repaid"}
    new_payment = float(monthly_payment.invoke({
    "principal": new_balance,
    "annual_rate": annual_rate,
    "term_months": remaining_months
}))
    return str({"new_balance": new_balance, "new_monthly_payment": round(new_payment, 2)})

@tool
def dti(total_monthly_debt: float, gross_monthly_income: float) -> str:
    """Calculates debt-to-income ratio as a percentage from total monthly debt and gross monthly income.
    USE WHEN: someone asks about affordability, or whether they can take on more debt.
    Requires their income and total monthly debt payments."""

    if gross_monthly_income <= 0:
        return {"error": "income must be positive"}
    return str(round((total_monthly_debt / gross_monthly_income) * 100, 2))

@tool
def early_repayment_charge(outstanding_balance: float, annual_rate: float, months: int) -> str:
    """Calculates ERC as (months) of gross interest on the balance.
    The number of months comes from the loan's specific early-repayment clause."""
    if annual_rate > 1:
        annual_rate = annual_rate / 100
    return str(round(outstanding_balance * annual_rate / 12 * months, 2))


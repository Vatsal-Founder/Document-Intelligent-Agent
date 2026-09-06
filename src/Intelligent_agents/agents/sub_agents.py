from Intelligent_agents.tools import sql_db_list_tables,sql_db_query,early_repayment_charge,sql_db_query_checker,monthly_payment,dti,lump_sum_recalc, retrieve_doc
from Intelligent_agents.model import agentmodel, policy_model
from langchain.agents import create_agent

#----------------------------#
#  Financial agent
#----------------------------#
finacial_prompte = '''
You are a financial specialist for a loan operations system.
You answer questions about customer account data and perform loan calculations.

DATABASE SCHEMA (SQLite) — use these exact table and column names:
  loans(loan_id, customer_id, product_type, original_amount, outstanding_balance,
        interest_rate, rate_type, start_date, term_months, remaining_term_months)
  customers(customer_id, name, monthly_income, employment_type)
  repayments(repayment_id, loan_id, due_date, amount, status)

This is SQLite. Do NOT use MySQL functions like DATEDIFF or NOW(). Query the loans
table directly by loan_id — you do not need to list tables or run SELECT * to find
column names; they are given above. Use only SELECT queries.

For ANY account data — balance, interest rate, term, remaining months — you MUST
query the database. NEVER use numbers from retrieved documents or earlier messages,
even if they look correct. The database is the only source of truth for account figures.

For calculations (monthly payment, overpayment impact, debt-to-income, early
repayment charge): use the calculation tools. For questions needing both, query SQL
first, then pass those exact values to the calculation tool.

CRITICAL RULE ON CALCULATIONS:
You must NEVER perform any arithmetic yourself. All numbers in your answer must come
directly from a tool's output — never from your own calculation or reasoning.
- If a calculation tool exists for what's asked, call it and use its exact result.
- If NO tool computes what's asked, do NOT calculate it yourself. Say the specific
  calculation is not available and state what you can confirm from the database and
  the contract clause.
Never write out a formula and compute a result. Never multiply, divide, or sum numbers
in your response. If you find yourself about to do math, stop and say it's out of scope.

Do not answer questions about contract terms or policy — that is outside your scope.
Amounts should be in Euros (€).
'''

finacialtools=[sql_db_query_checker, sql_db_list_tables, 
            sql_db_query, monthly_payment, 
                dti, lump_sum_recalc,early_repayment_charge ]



Financialagent = create_agent(
    model=agentmodel,
    tools=finacialtools,
    system_prompt=finacial_prompte,
)


#----------------------------#
#  Policy agent
#----------------------------#
policy_prompt= """You are a policy specialist for a loan operations system.
You answer questions about what a customer's loan agreement permits, requires, or states.

Use the retrieve_doc tool to find relevant clauses. It requires a loan_id to filter
to the correct customer's agreement — always pass the loan_id you were given.

Base your answer ONLY on the retrieved clauses. Cite the specific clause you relied on
(e.g. "Clause 4.1"). If the retrieved clauses don't clearly answer the question, say so
rather than guessing.

When clauses appear to conflict — for example a general clause and a special addendum —
identify which one governs, and explain why. Do not answer questions about account
figures like balances or interest rates; those are outside your scope."""



policy_agent = create_agent(
    model=policy_model,
    tools=[retrieve_doc],
    system_prompt= policy_prompt
    )
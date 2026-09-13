# evals/eval_set.py

EVAL_SET = [
    # ---- RAG-only (policy) ----
    {"question": "For L003, is there a penalty for overpaying?",
     "expected": "2.00%", "type": "policy"},
    {"question": "For L001, can I make overpayments without a penalty?",
     "expected": "10%", "type": "policy"},
    {"question": "For L003, can I take a payment break?",
     "expected": "prohibited", "type": "policy"},
    {"question": "For L002, is there a charge for early repayment?",
     "expected": "no", "type": "policy"},
    {"question": "For L002, how much notice do I get before a rate change?",
     "expected": "30", "type": "policy"},

    # ---- RAG conflict (the L004 addendum) ----
    {"question": "For L004, can I overpay without penalty?",
     "expected": "A.2", "type": "policy_conflict"},

    # ---- SQL-only (financial) ----
    {"question": "What is the outstanding balance on L001?",
     "expected": "240000", "type": "sql"},
    {"question": "What is the interest rate on L002?",
     "expected": "4.5", "type": "sql"},
    {"question": "What is the outstanding balance on L003?",
     "expected": "190000", "type": "sql"},
    {"question": "How many months remain on L004?",
     "expected": "18", "type": "sql"},

    # ---- Calc-only ----
    {"question": "What's the monthly payment on a 200000 loan at 4% over 25 years?",
     "expected": "1055", "type": "calc"},
    {"question": "What is the debt-to-income ratio if I earn 5000 a month and pay 1500 in debt?",
     "expected": "30", "type": "calc"},

    # ---- Mixed (both agents) ----
    {"question": "For L004, can I overpay 5000 without penalty, and what would my new monthly payment be?",
     "expected": "398", "type": "mixed"},
    {"question": "For L001, if I overpay 20000, what would my new monthly payment be?",
     "expected": "1183", "type": "mixed"},

    # ---- Escalation (should trigger HITL / needs_review) ----
    {"question": "For L003, what is the exact euro penalty for converting from fixed to variable rate mid-term?",
     "expected": "needs_review", "type": "escalation"},
]
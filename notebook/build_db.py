from langgraph.checkpoint.sqlite import SqliteSaver
from dotenv import load_dotenv
from langgraph.graph.message import add_messages
import os
import sqlite3
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent
DB_PATH = PROJECT_ROOT / "loan_data.db"

con = sqlite3.connect(DB_PATH)
cur = con.cursor()

# --- schema ---
cur.execute("""
CREATE TABLE customers (
    customer_id     TEXT PRIMARY KEY,
    name            TEXT,
    monthly_income  REAL,
    employment_type TEXT
)
""")

cur.execute("""
CREATE TABLE loans (
    loan_id                TEXT PRIMARY KEY,
    customer_id            TEXT,
    product_type           TEXT,      
    original_amount        REAL,
    outstanding_balance    REAL,
    interest_rate          REAL,      
    rate_type              TEXT,   
    start_date             TEXT,     
    term_months            INTEGER,
    remaining_term_months  INTEGER,
    FOREIGN KEY (customer_id) REFERENCES customers(customer_id)
)
""")

cur.execute("""
CREATE TABLE repayments (
    repayment_id  INTEGER PRIMARY KEY AUTOINCREMENT,
    loan_id       TEXT,
    due_date      TEXT,       
    amount        REAL,
    status        TEXT,      
    FOREIGN KEY (loan_id) REFERENCES loans(loan_id)
)
""")

# --- seed: 5 customers, each a distinct scenario ---
customers = [
    ('C001', 'Aoife Byrne',    5000, 'full_time'),   # standard fixed
    ('C002', 'Liam Murphy',    6200, 'full_time'),    # variable rate
    ('C003', 'Saoirse Kelly',  3800, 'full_time'),    # has missed payments
    ('C004', 'Cian Walsh',     7500, 'self_employed'),# near end of term
    ('C005', 'Niamh Doyle',    4400, 'full_time'),    # recent loan, early in term
]
cur.executemany("INSERT INTO customers VALUES (?,?,?,?)", customers)

loans = [
    # loan_id, cust, product,             orig,    outstanding, rate,  rate_type, start,        term, remaining
    ('L001','C001','fixed_mortgage',      250000,  240000,      0.035,'fixed',   '2023-01-15', 300,  264),
    ('L002','C002','variable_mortgage',   300000,  180000,      0.045,'variable','2016-06-01', 300,  120),
    ('L003','C003','fixed_mortgage',      200000,  190000,      0.040,'fixed',   '2024-03-10', 300,  282),
    ('L004','C004','fixed_mortgage',      150000,  12000,       0.030,'fixed',   '2005-09-01', 300,  18),
    ('L005','C005','variable_mortgage',   280000,  278000,      0.042,'variable','2026-01-05', 360,  356),
]
cur.executemany("INSERT INTO loans VALUES (?,?,?,?,?,?,?,?,?,?)", loans)

# --- repayments: a few per loan, covering paid / missed / upcoming ---
repayments = [
    ('L001','2026-06-30', 1240, 'paid'),
    ('L001','2026-07-30', 1240, 'paid'),
    ('L001','2026-08-30', 1240, 'upcoming'),
    ('L003','2026-05-30', 1010, 'paid'),
    ('L003','2026-06-30', 1010, 'missed'),   # <- the missed-payment scenario
    ('L003','2026-07-30', 1010, 'missed'),
    ('L003','2026-08-30', 1010, 'upcoming'),
    ('L004','2026-07-30',  700, 'paid'),
    ('L004','2026-08-30',  700, 'upcoming'), # near end of term
]
cur.executemany(
    "INSERT INTO repayments (loan_id, due_date, amount, status) VALUES (?,?,?,?)",
    repayments
)

con.commit()
con.close()
print("Database built.")
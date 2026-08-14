from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent

DB_PATH = PROJECT_ROOT / "loan_data.db"
CHROMA_PATH = PROJECT_ROOT / "chroma_db"
DOCS_PATH = PROJECT_ROOT / "Loan_docs"


from langchain_chroma import Chroma
from langchain.tools import tool
from dotenv import load_dotenv
load_dotenv() 
from langchain_huggingface import HuggingFaceEmbeddings
from config import CHROMA_PATH

embeddings=HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")
vectorstore = Chroma(
    persist_directory= f"{CHROMA_PATH}",
    embedding_function=embeddings,
)


@tool
def retrieve_doc(query: str, loan_id: str) -> str:
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


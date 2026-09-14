from langchain_community.document_loaders import PyPDFLoader
from pypdf import PdfReader
from langchain_openai import OpenAIEmbeddings
from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter
import glob
import os
from dotenv import load_dotenv
load_dotenv()
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent  # up from notebook/ to the repo root


CHROMA_PATH = PROJECT_ROOT / "chroma_db"
DOCS_PATH = PROJECT_ROOT / "Loan_docs"

from langchain_chroma import Chroma

embeddings = OpenAIEmbeddings(model="text-embedding-3-small")

pdf_dir = DOCS_PATH

all_chunks=[]

pdf_files = glob.glob("%s/*.pdf" % pdf_dir)
for file in pdf_files:
    filename = os.path.basename(file)
    loan_id = filename.split("_")[0]
    
    loader = PdfReader(file)
    
    docs = [
    Document(
        page_content=page.extract_text() or "",
        metadata={"source": filename,
                    "loan_id":loan_id,
                     "page": i, },
    )
    for i, page in enumerate(loader.pages)
        ]

    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=1000,
        chunk_overlap=300,
        add_start_index=True
        ).split_documents(docs)

    all_chunks.extend(text_splitter)

vectorstore = Chroma.from_documents(documents=all_chunks,
                        embedding=embeddings,
                        persist_directory=str(CHROMA_PATH),
                        )


print(f"Indexed {len(all_chunks)} chunks from {len(pdf_files)} documents")  
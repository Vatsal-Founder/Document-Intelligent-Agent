FROM python:3.11-slim

# system deps sometimes needed by chromadb / sentence-transformers
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# install uv
RUN pip install --no-cache-dir uv

# copy dependency files first (layer caching — deps only reinstall if these change)
COPY pyproject.toml uv.lock ./

RUN uv sync --frozen --no-dev --no-install-project

# copy the application code and data
COPY app.py ./
COPY src ./src
COPY loan_data.db ./
COPY chroma_db ./chroma_db
COPY Loan_docs ./Loan_docs

# install dependencies into the image
RUN uv sync --frozen --no-dev

EXPOSE 8000

CMD ["uv", "run", "uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8000"]
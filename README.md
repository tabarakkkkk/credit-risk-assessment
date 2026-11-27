# CreditLens credit-risk assessment

## Run the application

```powershell
.\.venv\Scripts\python.exe -m streamlit run app/main.py
```

Use the seeded account for the first login:

```text
Email: analyst@creditlens.local
Password: CreditLens@2026
```

The account values can be overridden with `CREDITLENS_SEEDED_EMAIL` and
`CREDITLENS_SEEDED_PASSWORD` environment variables.

## Train the model

The raw dataset is stored at `data/raw/credit_risk_dataset.csv`.

```powershell
.\.venv\Scripts\python.exe -m src.cleaning
.\.venv\Scripts\python.exe -m src.train
```

Cleaning reads from `data/raw/` and writes `data/processed/credit_risk_cleaned.csv`. Training saves the
complete preprocessing and classifier pipeline to
`models/credit_risk_xgboost.joblib`.

## Validation

```powershell
.\.venv\Scripts\python.exe -m pytest -q
```

The current test metrics are recorded in [docs/metrics.md](docs/metrics.md).

## Current integration boundary

The ML pipeline and Streamlit assessment are connected. The project does not
currently contain RAG, graph, agent, or LLM service implementations, so the
Chatbot page remains an explicit disabled state instead of returning fabricated
responses.

## Policy RAG

Policy documents live in `policies/data/rag/`. Build the persistent ChromaDB
collection and embeddings with:

```powershell
.\.venv\Scripts\python.exe -m rag.ingest
```

Search independently of Streamlit or the agent:

```powershell
.\.venv\Scripts\python.exe -c "from rag.retriever import policies_search; print(policies_search('What is the standard DTI range?'))"
```

Run the 20-question Hit@3 evaluation with:

```powershell
.\.venv\Scripts\python.exe -m rag.eval
```

The project uses a deterministic offline local embedding function, so no API
key or model download is required. The persistent vector database is stored in
`rag/chroma_db/`. Ingestion uses SHA-256 chunk IDs, so rerunning it does not
duplicate existing records.

RAG test logs are stored in `tests/logs/`: ingestion/idempotency results,
Hit@3 evaluation results, and independent search examples.

## Setup without activating `.venv`

If the project has no `.venv`, create it and install all dependencies:

```powershell
py -3 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
```

All project commands can then be run through `.\.venv\Scripts\python.exe`.
This is important because plain `python` may use a different installation and
show `ModuleNotFoundError: No module named 'chromadb'`.

## What has been updated

- Moved the raw dataset to `data/raw/` and cleaned data to `data/processed/`.
- Moved the SQLite application database to `data/app/`.
- Added required full-name validation.
- Added application history with submission time and prediction result.
- Prevented editing submitted applications; users start a new request instead.
- Added a repository layer under `app/repositories/`.
- Added 10 policy documents and `policies/docs_index.md`.
- Added ChromaDB ingestion, metadata, SHA-256 IDs, and idempotency.
- Added independent RAG retrieval and 20-question Hit@3 evaluation.
- Achieved `Hit@3: 95.00%`.
- Added RAG logs under `tests/logs/`.

## Project structure

```text
credit-risk-assessment/
├── README.md
├── requirements.txt
├── app/                       # Streamlit UI and services
├── config/                    # Example environment configuration
├── data/raw/                  # Original dataset
├── data/processed/            # Cleaned ML dataset
├── data/app/                  # SQLite application database
├── docs/                      # Metrics and documentation
├── ml/                        # ML service boundary and schemas
├── models/                    # Saved ML model
├── policies/data/rag/         # Policy Markdown documents
├── policies/docs_index.md     # RAG source index
├── rag/                       # Ingestion, retrieval, evaluation, ChromaDB
├── src/                       # Cleaning, training, preprocessing, prediction
└── tests/                     # Automated tests and logs
```

## Remaining course requirements

The ML and RAG tools are complete. The remaining major work is the Neo4j graph
tool, a LangGraph workflow with an LLM and maximum five iterations, connecting
ML/RAG/Neo4j as Agent tools, connecting the real Agent to the Streamlit chatbot,
agent iteration logs, an architecture diagram, and end-to-end Agent test logs.

The ML result is an assessment aid, not an approval or rejection decision. The
policy documents are educational sample policies and must not be treated as
real lending rules.

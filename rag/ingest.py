"""Build the persistent loan policy ChromaDB collection idempotently."""

import hashlib
import re
from pathlib import Path

import chromadb
from langchain_text_splitters import RecursiveCharacterTextSplitter
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
POLICY_DIR = ROOT / "policies" / "data" / "rag"
CHROMA_DIR = ROOT / "rag" / "chroma_db"
COLLECTION_NAME = "loan_policies"
EMBEDDING_MODEL = "all-MiniLM-L6-v2"


class LocalHashEmbeddingFunction:
    """Offline, deterministic embedding function with no model download."""

    dimension = 384

    def name(self):
        return "local-hash-embeddings"

    def __call__(self, input):
        vectors = []
        for text in input:
            vector = np.zeros(self.dimension, dtype=np.float32)
            tokens = re.findall(r"[a-z0-9%]+", text.lower())
            for token in tokens:
                digest = hashlib.sha256(token.encode("utf-8")).digest()
                index = int.from_bytes(digest[:4], "little") % self.dimension
                vector[index] += 1.0 if digest[4] % 2 else -1.0
            norm = np.linalg.norm(vector)
            vectors.append((vector / norm if norm else vector).tolist())
        return vectors

    def embed_query(self, input):
        return self(input if isinstance(input, list) else [input])


def get_collection():
    client = chromadb.PersistentClient(path=str(CHROMA_DIR))
    embedding_function = LocalHashEmbeddingFunction()
    try:
        return client.get_or_create_collection(
            name=COLLECTION_NAME,
            metadata={"hnsw:space": "cosine"},
            embedding_function=embedding_function,
        )
    except ValueError as error:
        if "embedding function conflict" not in str(error).lower():
            raise
        # A prior failed first run may have left an empty collection with the
        # old default embedding configuration. Recreate that exact collection.
        client.delete_collection(COLLECTION_NAME)
        return client.create_collection(
            name=COLLECTION_NAME,
            metadata={"hnsw:space": "cosine"},
            embedding_function=embedding_function,
        )


def _metadata(path, chunk):
    headings = re.findall(r"^##\s+(.+)$", chunk, re.MULTILINE)
    section = headings[0] if headings else "document"
    section_number = re.match(r"Section\s+(\d+)", section, re.IGNORECASE)
    return {
        "source": path.name,
        "topic": path.stem.replace("_", " "),
        "section": section,
        "section_number": section_number.group(1) if section_number else "0",
        "document_type": "policy",
    }


def ingest():
    files = sorted(POLICY_DIR.glob("*.md"))
    if not files:
        raise FileNotFoundError(f"No policy documents found in {POLICY_DIR}")
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=700,
        chunk_overlap=100,
        separators=["\n## ", "\n", ". ", " ", ""],
    )
    collection = get_collection()
    ids, texts, metadatas = [], [], []
    for path in files:
        chunks = splitter.split_text(path.read_text(encoding="utf-8"))
        for chunk in chunks:
            chunk = chunk.strip()
            if not chunk:
                continue
            ids.append(hashlib.sha256(chunk.encode("utf-8")).hexdigest())
            texts.append(chunk)
            metadatas.append(_metadata(path, chunk))
    existing = set(collection.get(ids=ids, include=[]).get("ids", []))
    new = [(i, t, m) for i, t, m in zip(ids, texts, metadatas) if i not in existing]
    if new:
        collection.add(
            ids=[x[0] for x in new],
            documents=[x[1] for x in new],
            metadatas=[x[2] for x in new],
        )
    print(f"Found {len(files)} documents")
    print(f"Created {len(ids)} chunks")
    print(f"Inserted {len(new)} new chunks")
    print(f"Skipped {len(ids) - len(new)} duplicate chunks")
    print(f"Collection: {COLLECTION_NAME} ({collection.count()} total chunks)")
    return collection.count()


if __name__ == "__main__":
    ingest()

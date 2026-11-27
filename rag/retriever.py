"""Standalone semantic search over the persisted policy collection."""

from .ingest import get_collection, ingest


def policies_search(query, k=3, min_score=0.35):
    if not isinstance(query, str) or not query.strip():
        raise ValueError("query must be a non-empty string")
    collection = get_collection()
    if collection.count() == 0:
        ingest()
        collection = get_collection()
    result = collection.query(query_texts=[query], n_results=k)
    matches = []
    for text, metadata, distance in zip(
        result["documents"][0], result["metadatas"][0], result["distances"][0]
    ):
        score = max(0.0, 1.0 - float(distance))
        if score >= min_score:
            matches.append({"text": text, **metadata, "score": round(score, 4)})
    return matches

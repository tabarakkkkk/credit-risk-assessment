"""Evaluate whether the expected policy document appears in the top three."""

import json
from pathlib import Path

from .retriever import policies_search


def evaluate():
    questions = json.loads((Path(__file__).parent / "eval_questions.json").read_text(encoding="utf-8"))
    hits = 0
    for item in questions:
        results = policies_search(item["question"], k=3, min_score=0.0)
        sources = {result["source"] for result in results}
        hits += bool(sources.intersection(item["expected_sources"]))
    hit_at_3 = hits / len(questions) if questions else 0
    print(f"Questions evaluated: {len(questions)}")
    print(f"Correct top-3 results: {hits}")
    print(f"Hit@3: {hit_at_3:.2%}")
    print("Status: PASS" if hit_at_3 >= 0.80 else "Status: REVIEW")
    return hit_at_3


if __name__ == "__main__":
    evaluate()

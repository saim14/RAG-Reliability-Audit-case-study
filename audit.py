#!/usr/bin/env python3
import collections
import json
import math
import re
from pathlib import Path

ROOT = Path(__file__).parent
STOPWORDS = set("the a an is are does do can how what when at in on for of to and or be with it i all per".split())

def load_json(path):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

CORPUS = load_json(ROOT / "data" / "corpus.json")
CASES = load_json(ROOT / "data" / "eval_cases.json")

def terms(text):
    return [t for t in re.findall(r"[a-z0-9$]+", text.lower()) if t not in STOPWORDS]

def sentences(text):
    return re.split(r"(?<=[.!?])\s+", text.strip())

def lexical_overlap(question, doc):
    q = set(terms(question))
    d = set(terms(doc["title"] + " " + doc["text"]))
    return len(q & d)

def baseline(case):
    # Deliberately weak baseline:
    # 1) raw token overlap,
    # 2) no freshness policy,
    # 3) always answers,
    # 4) always takes the first sentence.
    doc = max(CORPUS, key=lambda d: lexical_overlap(case["question"], d))
    return {
        "doc_id": doc["id"],
        "answer": sentences(doc["text"])[0],
        "score": float(lexical_overlap(case["question"], doc)),
    }

DOC_TERMS = [terms(d["title"] + " " + d["text"]) for d in CORPUS]
AVG_DL = sum(map(len, DOC_TERMS)) / len(DOC_TERMS)
DF = collections.Counter()
for ts in DOC_TERMS:
    for token in set(ts):
        DF[token] += 1

def bm25(question, index):
    tokens = DOC_TERMS[index]
    tf = collections.Counter(tokens)
    dl = len(tokens)
    score = 0.0
    k1, b = 1.5, 0.75
    for token in terms(question):
        if token not in DF:
            continue
        idf = math.log(1 + (len(CORPUS) - DF[token] + 0.5) / (DF[token] + 0.5))
        freq = tf[token]
        score += idf * (freq * (k1 + 1)) / (freq + k1 * (1 - b + b * dl / AVG_DL))

    # Freshness is explicit rather than accidental.
    if CORPUS[index]["status"] == "legacy":
        score *= 0.55
    return score

def reliability_aware(case, threshold=2.5):
    scores = [bm25(case["question"], i) for i in range(len(CORPUS))]
    best_index = max(range(len(CORPUS)), key=lambda i: scores[i])
    doc = CORPUS[best_index]
    best_score = scores[best_index]

    # Evidence gate: unsupported questions should not force an answer.
    if best_score < threshold:
        return {"doc_id": None, "answer": "INSUFFICIENT_EVIDENCE", "score": best_score}

    # Query-aware passage selection.
    q_terms = set(terms(case["question"]))
    answer = max(
        sentences(doc["text"]),
        key=lambda s: len(q_terms & set(terms(s)))
    )
    return {"doc_id": doc["id"], "answer": answer, "score": best_score}

def evaluate(system):
    rows = []
    for case in CASES:
        pred = system(case)
        if case["should_abstain"]:
            evidence_ok = pred["doc_id"] is None
            answer_ok = pred["answer"] == "INSUFFICIENT_EVIDENCE"
        else:
            evidence_ok = pred["doc_id"] == case["expected_doc"]
            answer_ok = all(
                required.lower() in pred["answer"].lower()
                for required in case["required_evidence"]
            )

        rows.append({
            "id": case["id"],
            "question": case["question"],
            "expected_doc": case["expected_doc"],
            "predicted_doc": pred["doc_id"],
            "answer": pred["answer"],
            "score": round(pred["score"], 3),
            "evidence_ok": evidence_ok,
            "answer_ok": answer_ok,
            "pass": evidence_ok and answer_ok,
        })
    return rows

def summary(rows):
    supported = [r for r, c in zip(rows, CASES) if not c["should_abstain"]]
    unsupported = [r for r, c in zip(rows, CASES) if c["should_abstain"]]
    return {
        "overall_pass_rate": sum(r["pass"] for r in rows) / len(rows),
        "evidence_or_abstention_accuracy": sum(r["evidence_ok"] for r in rows) / len(rows),
        "supported_answer_accuracy": sum(r["answer_ok"] for r in supported) / len(supported),
        "unsupported_abstention_rate": sum(r["answer"] == "INSUFFICIENT_EVIDENCE" for r in unsupported) / len(unsupported),
    }

def pct(x):
    return f"{100*x:.1f}%"

def main():
    base = evaluate(baseline)
    improved = evaluate(reliability_aware)

    print("RAG Reliability Audit")
    print("=" * 72)
    for name, rows in [("BASELINE", base), ("RELIABILITY-AWARE", improved)]:
        s = summary(rows)
        print(f"\n{name}")
        print("-" * 72)
        print("overall pass rate:              ", pct(s["overall_pass_rate"]))
        print("evidence / abstention accuracy: ", pct(s["evidence_or_abstention_accuracy"]))
        print("supported answer accuracy:      ", pct(s["supported_answer_accuracy"]))
        print("unsupported abstention rate:    ", pct(s["unsupported_abstention_rate"]))

        print("\nFailures:")
        failures = [r for r in rows if not r["pass"]]
        if not failures:
            print("  none")
        for r in failures:
            print(f'  {r["id"]}: {r["question"]}')
            print(f'    predicted_doc={r["predicted_doc"]!r} score={r["score"]}')
            print(f'    answer={r["answer"]}')

if __name__ == "__main__":
    main()

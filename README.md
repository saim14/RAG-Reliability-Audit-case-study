# RAG Reliability Audit — Public Case Study

A reproducible, model-free case study showing how a small RAG system can appear plausible while still failing on **stale evidence, answer extraction, and unsupported questions**.

This repository is intentionally built as a public engineering artifact rather than a marketing mockup. It contains:

- a synthetic but realistic SaaS knowledge base,
- 20 labeled evaluation cases,
- a weak baseline retrieval/answering pipeline,
- a stronger reliability-aware pipeline,
- deterministic evaluation code,
- failure traces and a prioritized fix plan.

No API keys or paid models are required.

## Executive result

| Metric | Baseline | Reliability-aware |
|---|---:|---:|
| Overall reliability pass rate | 40% | **95%** |
| Correct evidence / abstention | 70% | **100%** |
| Supported-answer correctness | 56.3% | **93.8%** |
| Unsupported-question abstention | 0% | **100%** |
| Failed cases | 12 / 20 | **1 / 20** |

The point is not that BM25 is universally “better.” The point is that reliability improves when the system is evaluated as a chain:

**query → retrieval → evidence state → answer → abstention / failure classification**

## What the audit found

### 1. Stale-document failure
The baseline selects the legacy retention document on two cases. For deleted-content retention it answers **90 days** when the current policy says **30 days**; for application-log retention it also retrieves the obsolete policy rather than the current source.

**Fix:** explicitly model document status/version and penalize legacy evidence during retrieval.

### 2. Retrieval success ≠ answer success
Several cases retrieve the correct document but return the wrong sentence because the baseline always uses the first sentence.

**Fix:** score candidate evidence sentences against the query instead of assuming the first sentence is the answer.

### 3. Unsupported questions become hallucinations
For questions such as HIPAA BAA, on-prem deployment, upload-size limits, and SOC 2 Type II, the baseline always returns *something*.

**Fix:** add an evidence-confidence gate and return `INSUFFICIENT_EVIDENCE` when the retrieval score is below threshold.

### 4. One failure remains
The improved pipeline still misses the SLA-credit deadline question because sentence-level lexical overlap favors the uptime sentence.

That failure is kept intentionally. A useful audit should expose remaining weaknesses rather than present a perfect score.

## Reproduce

```bash
python audit.py
python -m unittest -v
```

The implementation uses only the Python standard library. GitHub Actions runs both the audit and its regression tests.

## Repository structure

```
.
├── .github/workflows/audit.yml
├── audit.py
├── test_audit.py
├── data/
│   ├── corpus.json
│   └── eval_cases.json
├── RESULTS.md
└── README.md
```

## Evaluation design

The 20 cases include:

- 16 answerable questions with a known source document and required answer evidence,
- 4 intentionally unsupported questions that should trigger abstention,
- a legacy/current policy conflict,
- multi-sentence documents where retrieval can be right while extraction is wrong.

The benchmark checks two separate layers:

1. **Evidence correctness** — was the right current document retrieved, or did the system abstain when evidence was absent?
2. **Answer correctness** — does the returned answer contain the required evidence, or correctly return `INSUFFICIENT_EVIDENCE`?

## Why this matters in real RAG systems

A single “accuracy” score can hide qualitatively different failures:

- wrong or stale document,
- right document / wrong passage,
- unsupported synthesis,
- failure to abstain.

Those failures need different fixes. The audit therefore keeps failure traces per case instead of reducing everything to one score.

## Scope note

The corpus is fictional so the repository can be fully public and reproducible. The evaluation methodology is the same pattern I use for bounded RAG reliability work: representative cases, evidence traces, failure taxonomy, and prioritized remediation.

## Author

**Saim Islam**  
AI / RAG reliability, evaluation, and failure analysis

Upwork service:  
https://www.upwork.com/services/product/development-it-a-rag-reliability-audit-with-a-scored-failure-map-and-fix-plan-2101681866994116339

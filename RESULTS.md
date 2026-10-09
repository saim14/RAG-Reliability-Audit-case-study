# Audit Results

This report records the deterministic output of `python audit.py` for the included 20-case benchmark.

## Scorecard

| Metric | Baseline | Reliability-aware | Delta |
|---|---:|---:|---:|
| Overall reliability pass rate | 45.0% | **95.0%** | **+50.0 pp** |
| Correct evidence / abstention | 70.0% | **100.0%** | **+30.0 pp** |
| Supported-answer correctness | 56.3% | **93.8%** | **+37.5 pp** |
| Unsupported-question abstention | 0.0% | **100.0%** | **+100.0 pp** |

## Baseline failure map

### Stale evidence
- **Q03** — "How long can deleted content stay in backups?"
- Baseline selects `retention_2024` and returns **90 days**.
- Current evidence is `retention_2026`: **30 days**.

### Right document, wrong passage
The baseline retrieves the correct document but returns the first sentence for:
- Q02 — MFA requirement
- Q07 — SLA credit claim deadline
- Q08 — Severity 1 response target
- Q10 — audit-log retention
- Q12 — annual-contract refund policy
- Q15 — point-in-time recovery window

This is an important RAG distinction: **retrieval success is not answer success**.

### Unsupported-answer hallucinations
The baseline refuses to abstain on all four unsupported questions:
- Q17 — HIPAA BAA
- Q18 — on-prem deployment
- Q19 — maximum upload size
- Q20 — SOC 2 Type II

The returned text is fluent but unrelated evidence.

## Reliability-aware fixes

### Fix 1 — freshness-aware retrieval
Legacy documents receive an explicit score penalty. This removes the stale 90-day retention answer.

### Fix 2 — query-aware passage selection
Instead of always returning the first sentence, candidate sentences are scored by overlap with the question.

### Fix 3 — evidence threshold
If the best retrieval score is below 2.5, the system returns:

```
INSUFFICIENT_EVIDENCE
```

This changes unsupported-question abstention from **0% to 100%**.

## Remaining failure

### Q07 — SLA credit deadline
Question:
> When must an SLA credit claim be filed?

Expected evidence:
> within 30 days

The correct document is retrieved, but the simple passage selector chooses:
> The Enterprise SLA provides 99.95% monthly uptime.

This remains a genuine failure and is deliberately not patched away.

### Recommended next fix
Add a semantic or learned reranker at the passage layer, then keep the same 20-case set as a regression gate. The key is to improve Q07 **without regressing the other 19 cases**.

## Failure taxonomy

| Failure class | Baseline | Reliability-aware |
|---|---:|---:|
| stale document | 1 | 0 |
| correct doc / wrong passage | 6 | 1 |
| unsupported answer instead of abstention | 4 | 0 |
| total failed cases | 11 | 1 |

## Interpretation

The improvement did not come from a larger language model. It came from making failure boundaries explicit:

1. document freshness,
2. evidence relevance,
3. passage selection,
4. abstention.

That is the main engineering lesson of this case study.

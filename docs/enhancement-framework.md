# Enhancement Experiment Framework

**Version**: 1.0
**Date**: 2026-05-02
**Purpose**: Define measurable metrics for baseline vs OpenClaw-enhanced comparison

---

## Metrics Definition

### Primary Metrics (Judging Criteria Alignment)

| Metric | Definition | Baseline Target | Enhanced Target | Measurement |
|--------|-----------|----------------|-----------------|-------------|
| **Detection Rate** | % of ground truth artifacts found | ≥80% | ≥95% | findings / ground_truth × 100 |
| **IR Accuracy** | % of findings that are correct | 100% | 100% | true_positives / total_findings |
| **False Positives** | Findings not in ground truth | 0 | 0 | count |
| **False Negatives** | Ground truth not detected | ≤1 | 0 | count |
| **Avg Confidence** | Mean confidence across findings | ≥0.85 | ≥0.90 | sum(confidence) / count |
| **Self-Corrections** | Contradictions detected and resolved | ≥1 | ≥3 | count |
| **Corroboration Rate** | Findings with cross-tool evidence | ≥60% | ≥90% | corroborated / total_findings |
| **Audit Completeness** | Findings with full evidence chain | 100% | 100% | has_tool+output+timestamp+hash |

### Secondary Metrics (Differentiation)

| Metric | Definition | Why It Matters |
|--------|-----------|---------------|
| **Token Usage** | Total tokens consumed per case | Efficiency benchmark |
| **Execution Time** | Wall clock time for full analysis | Performance comparison |
| **Decision Log Depth** | Reasoning steps recorded | Audit trail quality |
| **Constraint Type** | Prompt-based vs Architectural | Judge scoring criteria #4 |

---

## Baseline vs Enhanced Comparison Template

### Test Case 001: Synthetic Linux Compromise

| Metric | Baseline (Manual) | Enhanced (OpenClaw) | Δ |
|--------|-------------------|---------------------|---|
| Detection Rate | 83% (5/6) | TBD | — |
| True Positives | 4 | TBD | — |
| Low Confidence | 1 (F-005) | TBD | — |
| False Negatives | 1 (syslog) | TBD | — |
| False Positives | 0 | TBD | — |
| Avg Confidence | 0.87 | TBD | — |
| Self-Corrections | 1 | TBD | — |
| Corroboration Rate | 80% (4/5) | TBD | — |
| Constraint Type | N/A (manual) | Architectural | — |
| Decision Logging | No | Yes (JSONL) | — |
| Token Usage | 3,000 (est) | TBD | — |

---

## Enhancement #1: OpenClaw Self-Correction Loop

### What Changes
```
BEFORE (Baseline):
  SleuthKit fls → body file
  YARA scan → matches
  Manual comparison → findings
  Manual confidence assessment

AFTER (Enhanced):
  OpenClaw orchestrates:
  1. Run SleuthKit fls → parse output
  2. Run YARA scan → parse matches
  3. Cross-reference: inode mapping from fls ↔ YARA file paths
  4. For each finding: check corroboration across tools
  5. If confidence < threshold: auto re-run with extended params
  6. Log every decision + reasoning to JSONL
  7. Generate structured report with evidence hashes
```

### Key Innovation Points (for judging)

1. **Architectural Self-Correction**: Not prompt-based "be careful" — structural loop with re-run triggers
2. **Evidence-Anchored Findings**: Every finding has hash chain: tool → raw output → SHA256 → timestamp
3. **Cross-Tool Corroboration**: Findings scored by multi-tool agreement, not single-source
4. **Decision Audit Trail**: Complete reasoning chain in JSONL, not just results

### Configuration

```yaml
self_correction:
  confidence_threshold: 0.75
  max_re_runs: 3
  re_run_strategies:
    - broaden_yara_rules
    - extract_and_rescan
    - cross_reference_timeline
  audit_log: ./logs/forensic_audit.jsonl
  evidence_hash: true
  write_sandbox:
    allowed_paths:
      - ./analysis/*
      - ./exports/*
      - ./reports/*
    denied_paths:
      - /cases/*
      - /mnt/*
      - /media/*
```

---

## Demo Narrative (3-5 minutes)

### Act 1: The Problem (30s)
"DFIR analysts face thousands of artifacts. Manual correlation is slow and error-prone.
Protocol SIFT gives us Claude Code + DFIR tools. But without structured self-correction,
findings can have hallucinations and no audit trail."

### Act 2: Baseline Run (60s)
Show baseline execution on test case:
- SleuthKit finds files → YARA scans → 5 findings generated
- BUT: F-005 has low confidence, syslog artifact missed entirely
- No decision log, no evidence hash chain

### Act 3: OpenClaw Enhancement (90s)
Show enhanced run:
- Same test case, OpenClaw orchestrates
- Self-correction loop detects F-005 low confidence → auto re-runs YARA
- Cross-tool corroboration catches syslog via timeline analysis
- Every finding now has: tool → output → hash → timestamp
- Evidence integrity enforced at architecture level, not prompt level

### Act 4: Results (30s)
Show comparison table:
- Detection: 83% → 100%
- Self-corrections: 1 → 3
- Audit trail: None → Complete JSONL
- Evidence integrity: Manual → Architectural

### Act 5: Why This Matters (30s)
"Judges can verify our constraints are real — not just 'be careful' prompts.
Every finding traces back to a specific tool execution with a SHA256 hash.
This is what production DFIR tooling needs: not more features, but more trust."

---

_Last updated: 2026-05-02 D4_

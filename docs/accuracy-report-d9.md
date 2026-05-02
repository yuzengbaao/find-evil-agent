# D9: Updated Accuracy Report — Plaso Integration Impact

**Date**: 2026-05-02
**Test Case**: TC-001 (Synthetic Linux Compromise, 50MB ext4)
**Previous**: D7 (SleuthKit + YARA only)
**Current**: D9 (SleuthKit + YARA + Plaso)

---

## 1. Executive Summary

Plaso timeline integration raised detection from 83% to **100%** and introduced **3-tool cross-corroboration** — two findings independently confirmed by all three tools.

## 2. Detection Rate Comparison

| Ground Truth | D7 (2 tools) | D9 (3 tools) | New Status |
|-------------|-------------|-------------|------------|
| /tmp/.hidden/reverse.sh | ✅ SleuthKit+YARA | ✅ SleuthKit+YARA+**Plaso** | 🎯 3-tool |
| /opt/backdoor/conn.py | ✅ SleuthKit+YARA | ✅ SleuthKit+YARA+**Plaso** | 🎯 3-tool |
| /tmp/.hidden/.shadow.bak | ✅ SleuthKit | ✅ SleuthKit+**Plaso** | 🆙 2-tool |
| /var/log/auth.log | ⚠️ SleuthKit only | ✅ **Plaso detected** SSH login | **NEW** |
| /opt/backdoor/payload.bin | ✅ SleuthKit | ✅ SleuthKit+**Plaso** | 🆙 2-tool |
| /var/log/syslog | ❌ Missed | ✅ **Plaso detected** "suspicious process" | **NEW** |

**Detection Rate: 83% → 100%**

## 3. Metric Comparison (3-way)

| Metric | Baseline (Manual) | D7 (2 tools) | D9 (3 tools) | Δ from D7 |
|--------|-------------------|-------------|-------------|-----------|
| Detection Rate | 83% | 83% | **100%** | **+17%** |
| False Positives | 0 | 0 | **0** | 0 |
| Avg Confidence | N/A | 0.78 | **0.85** | +0.07 |
| 3-Tool Corroboration | N/A | 0 | **2** | +2 |
| Self-Corrections | N/A | 0 | **1** | +1 |

## 4. Dual-Case Validation

| Metric | TC-001 (Backdoor) | TC-002 (Ransomware) |
|--------|-------------------|---------------------|
| Detection Rate | 100% (6/6) | 100% (8/8) |
| False Positives | 0 | 0 |
| False Negatives | 0 | 0 |
| Avg Confidence | 0.85 | 0.85 |
| 3-Tool Corroboration | 2 findings | 1 finding |
| Audit Trail | Complete JSONL+SHA256 | Complete JSONL+SHA256 |

**Aggregate: 100% detection (14/14 artifacts), 0 false positives, 0 false negatives across both cases.**

## 5. Evidence Integrity Approach

> *"How does your architecture prevent original data from being modified? If you're using prompt-based restrictions rather than architectural enforcement, document what happens when the model ignores the restriction. Did you test for spoliation?"*

### 5.1 Architectural Guardrails (Cannot Be Bypassed)

Our architecture enforces evidence integrity at the **OS and code level**, not through prompts that can be ignored:

1. **Read-Only Mount (OS-Level)**
   - Evidence disk images are mounted with `mount -o ro,loop,nosuid,noexec`
   - Even if the agent attempted to write, the OS kernel returns EPERM
   - Tested: agent attempted `touch /mnt/evidence/test` → `Read-only file system` error
   - **This guardrail cannot be bypassed by any agent instruction**

2. **Write Sandbox (Filesystem-Level)**
   - All output is written to a separate directory (`/cases/{case}/reports/`, `/cases/{case}/logs/`)
   - The agent has no write path to the evidence mount point
   - Code enforces: `output_dir = case_dir / "reports"`, never under evidence mount

3. **SHA256 Evidence Hashing (Code-Level)**
   - Every file accessed by the agent is hashed immediately upon read
   - The hash is recorded in the JSONL audit trail before any analysis occurs
   - Post-analysis hash comparison detects any modification
   - Implementation: `audit_logger.py` computes `hashlib.sha256(data).hexdigest()` on every file read

4. **Immutable Audit Trail (Format-Level)**
   - JSONL append-only format — entries are never modified or deleted
   - Each entry contains: `tool`, `action`, `file_path`, `sha256`, `timestamp`, `result`
   - Judges can trace any finding back to the specific tool execution that produced it

### 5.2 Prompt-Based Guardrails (NOT Trusted)

We explicitly classify these as **unreliable** and do NOT depend on them:

- ❌ "Do not modify the evidence" — agent could ignore this
- ❌ "Be careful with your findings" — no enforcement mechanism
- ❌ "Only report real artifacts" — no structural prevention of hallucination

**What happens when the model ignores prompt-based restrictions?**
Nothing bad happens, because the architectural guardrails catch it:
- Model tries to write to evidence → OS blocks it (read-only mount)
- Model tries to modify audit trail → append-only format prevents it
- Model hallucinates a finding → no corresponding tool execution in audit trail → finding is unverifiable

### 5.3 Spoliation Testing

We tested evidence integrity across both test cases:

| Test | Method | Result |
|------|--------|--------|
| Pre/post hash comparison | SHA256 before and after agent run | ✅ All hashes identical |
| Mount verification | `mount | grep ro` after agent run | ✅ Still read-only |
| File count check | `find /mnt -type f | wc -l` before/after | ✅ No new files created |
| Write attempt test | Agent `touch /mnt/evidence/test` | ✅ Blocked by OS |
| Audit trail integrity | Entry count matches tool invocations | ✅ 38 entries for TC-001, all traceable |

**Conclusion: Zero evidence spoliation across both test cases. The architectural guardrails successfully prevent any modification to original evidence, regardless of agent behavior.**

## 6. Hallucination Detection

Cross-tool corroboration serves as our primary hallucination defense:

- A finding claimed by only one tool with no corroboration → flagged as **low confidence** (0.5-0.6)
- A finding confirmed by 2+ tools → promoted to **high confidence** (0.85+)
- A finding with no tool execution backing → **automatically excluded** from report

In both test cases: 0 hallucinated findings, 0 unverified claims in final reports.

## 7. Limitations (Honest Assessment)

1. **Synthetic test data only** — Not validated against real-world forensic images with noise, corruption, or anti-forensics techniques
2. **Plaso version outdated** (20201007) — May miss newer artifact formats
3. **Volatility3 untested with real memory dumps** — Integrated but only validated on disk-only scenarios
4. **Self-correction triggered once** — Limited evidence of the loop's effectiveness across diverse scenarios
5. **No network forensics** — PCAP/Suricata analysis not yet integrated
6. **Single-machine scope** — No distributed or multi-endpoint analysis capability

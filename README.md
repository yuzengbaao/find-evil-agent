# 🔍 Self-Correcting DFIR Agent for Protocol SIFT

> FIND EVIL! Hackathon Submission — SANS Institute / Devpost

## Overview

An autonomous incident response agent built on **OpenClaw** that extends Protocol SIFT with architectural self-correction, evidence-anchored findings, and verifiable audit trails.

Unlike prompt-based guardrails, our agent enforces **structural constraints** at the orchestration layer — every finding must trace back to specific tool output with timestamps and token usage.

## Key Innovations

### 1. Architectural Self-Correction
- **Contrast Detection**: Agent compares findings across multiple DFIR tools (Volatility + SleuthKit + Plaso) to detect contradictions
- **Automatic Re-run**: When findings conflict, agent re-executes the disputed tool with different parameters
- **Confidence Scoring**: Each finding gets a confidence score based on cross-tool corroboration

### 2. Evidence-Anchored Findings
- Every finding links to: source tool → raw output file → timestamp → token count
- No finding without verifiable tool output — hallucination-proof by architecture

### 3. Structural Read-Only Boundaries
- Evidence paths (`/cases/`, `/mnt/`, `/media/`) enforced at OS level (not prompt level)
- Write sandboxing: agent can only write to `./analysis/`, `./exports/`, `./reports/`
- Judges can verify constraints are architectural, not prompt-based

## Architecture

```
User/OpenClaw
     │
     ▼
┌─────────────────────────────────────────────────┐
│              Agent Orchestration                 │
│  ┌───────────┐  ┌───────────┐  ┌──────────────┐ │
│  │ Reasoning │←→│ Self-Corr │←→│ Audit Trail  │ │
│  │  Engine   │  │  Engine   │  │   Logger     │ │
│  └─────┬─────┘  └─────┬─────┘  └──────┬───────┘ │
│        │              │               │          │
│  ┌─────▼──────────────▼───────────────▼───────┐  │
│  │            DFIR Tool Router                │  │
│  │  Volatility │ SleuthKit │ Plaso │ YARA     │  │
│  └─────────────────────┬─────────────────────┘  │
│                        │                         │
│  ┌─────────────────────▼─────────────────────┐  │
│  │          Evidence Integrity Layer          │  │
│  │  Read-only mount │ Write sandbox │ Hash    │  │
│  └───────────────────────────────────────────┘  │
└─────────────────────────────────────────────────┘
```

## Tech Stack

| Component | Technology |
|-----------|-----------|
| Agent Framework | OpenClaw (Direct Agent Extension) |
| DFIR Tools | Protocol SIFT (Volatility 3, SleuthKit, Plaso, EZ Tools, YARA) |
| Self-Correction | Contrast Detection + Automatic Re-run |
| Audit Trail | Structured JSON logs + token tracking |
| Evidence Integrity | OS-level read-only mount + write sandbox |

## Quick Start

```bash
git clone https://github.com/yuzengbaao/find-evil-agent.git
cd find-evil-agent
pip install -r requirements.txt
cp .env.example .env
python scripts/agent.py --case /cases/srl --config config/default.yaml
```

## Project Structure

```
find-evil-agent/
├── README.md              ← This file
├── LICENSE                ← MIT
├── config/                ← Agent configurations
├── scripts/
│   ├── agent.py           ← Main agent entry point
│   ├── self_correct.py    ← Self-correction engine
│   ├── audit_logger.py    ← Structured audit trail
│   └── accuracy_report.py ← Benchmarking framework
├── analysis/              ← Agent output (generated)
├── logs/                  ← Execution logs (generated)
├── docs/                  ← Documentation
├── diagrams/              ← Architecture diagrams
├── tests/                 ← Test suite
└── evidence-samples/      ← Sample evidence for testing
```

## Author

**zengbao yu** ([@yuzengbaao](https://devpost.com/yuzengbaao))

## License

MIT License — see [LICENSE](LICENSE)

# Environment Setup

## System Requirements

- **OS**: Linux (Ubuntu 22.04 LTS recommended, or SANS SIFT workstation)
- **Python**: 3.10+
- **Disk**: 500MB+ free space for tools + case data
- **RAM**: 2GB+ (4GB+ for large disk images)

## Installed Tools

### Core DFIR Tools
```bash
# SleuthKit 4.11+ (filesystem analysis)
sudo apt install sleuthkit -y
# Verify: fls -V

# YARA 4.1+ (malware signature matching)
sudo apt install yara -y
# Verify: yara --version

# Plaso (timeline analysis)
pip install plaso  # or: sudo apt install python3-plaso
# Verify: log2timeline.py --version

# Volatility3 2.28+ (memory forensics, optional)
pip install volatility3
# Verify: vol -h
```

### Python Dependencies
```bash
pip install -r requirements.txt
```

Or install individually:
```bash
pip install hashlib json datetime pathlib argparse
# All are stdlib — no external Python packages required
```

## SANS SIFT Workstation

This agent is designed to run on the **Protocol SIFT** workstation (provided by the hackathon). On SIFT:

1. All DFIR tools (SleuthKit, YARA, Plaso, Volatility3) are pre-installed
2. Python 3.10+ is available
3. Simply clone the repo and run:

```bash
git clone https://github.com/yuzengbaao/find-evil-agent
cd find-evil-agent
python3 scripts/agent.py --case /path/to/your/case
```

## File Structure

```
find-evil-agent/
├── scripts/
│   ├── agent.py           # Main orchestration agent
│   ├── audit_logger.py    # JSONL audit trail with SHA256
│   ├── self_correct.py    # Cross-tool contradiction detection
│   ├── deduplicate.py     # Artifact-level dedup + corroboration
│   └── produce-demo-video.py  # Demo video generation
├── config/
│   └── default.yaml       # Agent configuration
├── docs/
│   ├── architecture-diagram.png
│   ├── accuracy-report-d9.md
│   ├── dual-case-evaluation.md
│   └── environment.md     # This file
├── evidence-packages/
│   ├── tc-001-backdoor/   # Test case with audit trail
│   └── tc-002-ransomware/ # Test case with audit trail
└── README.md
```

## Running Test Cases

```bash
# Clone
git clone https://github.com/yuzengbaao/find-evil-agent
cd find-evil-agent

# Run on provided test cases (requires synthetic disk images)
python3 scripts/agent.py --case evidence-packages/tc-001-backdoor
python3 scripts/agent.py --case evidence-packages/tc-002-ransomware

# Run on your own case
mkdir -p /cases/my-case/evidence
cp suspect_disk_image.dd /cases/my-case/evidence/
python3 scripts/agent.py --case /cases/my-case
```

## Output

After running, check:
- `reports/agent_report.md` — Human-readable findings
- `reports/agent_report.json` — Machine-readable findings
- `logs/forensic_audit_*.jsonl` — Complete audit trail (SHA256-hashed)

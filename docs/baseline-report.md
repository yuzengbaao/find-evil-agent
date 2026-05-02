# Baseline Report — Test Case 001

**Date**: 2026-05-02
**Evidence**: test-disk.img (50MB ext4, synthetic compromised Linux system)
**Tools**: SleuthKit 4.11.1 + YARA 4.1.3

## Ground Truth

| # | Artifact | Location | Type | Expected Detection |
|---|----------|----------|------|--------------------|
| 1 | Reverse shell script | /tmp/.hidden/reverse.sh | bash netcat | CRITICAL |
| 2 | Python reverse shell | /opt/backdoor/conn.py | Python socket | CRITICAL |
| 3 | Credential dump | /tmp/.hidden/.shadow.bak | plaintext creds | HIGH |
| 4 | SSH auth log | /var/log/auth.log | login from attacker IP | MEDIUM |
| 5 | Malware payload | /opt/backdoor/payload.bin | binary with NOP sled | CRITICAL |
| 6 | Syslog evidence | /var/log/syslog | kernel suspicious process | LOW |

## Baseline Results

### Tool Execution Summary

| Tool | Command | Output | Exit | Duration(ms) | Tokens |
|------|---------|--------|------|-------------|--------|
| SleuthKit fls | `fls -r -m / evidence/test-disk.img` | exports/fls_body.txt | 0 | 1500 | 1200 |
| SleuthKit mactime | `mactime -b exports/fls_body.txt` | exports/timeline.csv | 0 | 600 | 800 |
| SleuthKit icat x3 | `icat evidence/test-disk.img <inode>` | exports/*_extracted.txt | 0 | 300 | 400 |
| YARA | `yara -r malware_rules.yar /mnt/evidence/` | exports/yara_results.txt | 0 | 800 | 600 |

### Findings

| ID | Title | Severity | Tool | Confidence | Corroboration | Status |
|----|-------|----------|------|------------|---------------|--------|
| F-001 | Reverse Shell Script | CRITICAL | yara | 0.95 | sleuthkit (inode 20) | Verified |
| F-002 | Python Reverse Shell | CRITICAL | yara | 0.95 | sleuthkit x2 | Verified |
| F-003 | Hidden Credential Dump | HIGH | sleuthkit | 0.85 | — | Verified |
| F-004 | Suspicious SSH Login | MEDIUM | sleuthkit-icat | 0.90 | sleuthkit | Verified |
| F-005 | Malware Payload Binary | CRITICAL | yara | 0.70 | sleuthkit | Low confidence |

### Accuracy vs Ground Truth

| Ground Truth | Detected? | Finding ID | Notes |
|-------------|-----------|------------|-------|
| 1. Reverse shell | YES | F-001 | YARA + SleuthKit match |
| 2. Python shell | YES | F-002 | YARA + SleuthKit + icat |
| 3. Credential dump | YES | F-003 | SleuthKit file listing |
| 4. SSH log | YES | F-004 | SleuthKit icat extraction |
| 5. Malware payload | PARTIAL | F-005 | YARA match but confidence 0.70 |
| 6. Syslog evidence | NO | — | NOT detected by current rules |

**Detection Rate**: 5/6 = 83% (4 verified + 1 low confidence + 1 missed)
**False Positives**: 0
**False Negatives**: 1 (syslog not in YARA rules)

### Self-Correction Triggered

| Contradiction | Type | Resolution |
|--------------|------|-----------|
| F-005 confidence < 0.75 | confidence_below_threshold | Re-run YARA with broader rules |

## Baseline Weaknesses (OpenClaw enhancement targets)

1. **No syslog analysis** — no log parsing rules in YARA
2. **F-005 low confidence** — hex rule didn't match directly from raw image
3. **No cross-tool contradiction detection** — findings are independent
4. **No decision logging** — agent reasoning not captured
5. **Manual workflow** — tools run sequentially by hand
6. **No evidence hash chain** — output files not integrity-verified

## Metrics Summary

| Metric | Value |
|--------|-------|
| Total Findings | 5 |
| True Positives | 4 |
| Low Confidence | 1 |
| False Negatives | 1 |
| False Positives | 0 |
| Avg Confidence | 0.87 |
| Total Tokens | 3,000 |
| Detection Rate | 83% |

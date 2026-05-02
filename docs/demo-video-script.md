# Demo Video Script (3-5 minutes)

**FIND EVIL! Hackathon — Self-Correcting DFIR Agent**

---

## ACT 1: The Problem (0:00 - 0:45)

### Visual: Terminal, dark theme, forensic case directory

**Narration:**
"DFIR analysts face a massive challenge: thousands of artifacts across disk images, memory dumps, and log files. Current AI tools can help, but they have three critical flaws: they can hallucinate findings, they can't trace conclusions back to evidence, and their constraints are just prompts that can be ignored."

**Screen:**
```
Problem:
❌ LLM hallucination → fake findings
❌ No audit trail → can't verify conclusions  
❌ Prompt-based constraints → can be bypassed
```

---

## ACT 2: Our Architecture (0:45 - 1:30)

### Visual: Architecture diagram (animated build)

**Narration:**
"We built a structurally self-correcting DFIR agent on OpenClaw that orchestrates four forensic tools: SleuthKit for filesystem analysis, YARA for signature matching, Plaso for timeline reconstruction, and Volatility3 for memory forensics."

**Screen (build up step by step):**
```
Step 1: SleuthKit fls → file listing
Step 2: YARA scan → malware detection
Step 3: Plaso timeline → log event parsing
Step 4: Volatility3 → memory analysis (auto-detect)

Then: Deduplicate by artifact
Then: Self-correct on low confidence
Then: Audit trail with SHA256 hashes
```

**Key line:**
"The critical difference: our constraints are architectural, not prompts. Read-only mounts enforced by the OS, write sandboxes enforced by the filesystem, evidence integrity enforced by SHA256 hashing."

---

## ACT 3: Live Demo — TC-001 (1:30 - 3:00)

### Visual: Terminal recording of actual agent run

**Action 1: Start agent**
```bash
python3 scripts/agent.py --case /cases/test-case-001
```

**Screen output (real):**
```
[AGENT] Starting DFIR analysis
  [MOUNT] Mounted test-disk.img (read-only)
  [SLEUTHKIT] Running file system analysis...
  [YARA] Scanning /mnt/evidence_test-disk...
  [PLASO] Running timeline analysis...
  [VOLATILITY] No memory dumps — skipping
```

**Narration:**
"One command. The agent automatically mounts the evidence read-only, runs all applicable tools, and generates findings."

**Action 2: Show deduplicated results**
```bash
python3 scripts/deduplicate.py logs/forensic_audit_*.jsonl
```

**Screen output (highlight):**
```
UF-006: Reverse Shell — /opt/backdoor/conn.py
  ├─ SleuthKit fls → inode 26
  ├─ YARA → python_reverse_shell rule matched
  └─ Plaso → syslog "suspicious process reverse.sh"
  Confidence: 0.90 | CRITICAL | 3 tools agree
```

**Narration:**
"Three independent forensic tools confirmed the same backdoor. Not 'the AI thinks there's a backdoor' — three real tools independently agree, with SHA256 hashes proving the evidence wasn't tampered with."

**Action 3: Show audit trail**
```bash
head -5 logs/forensic_audit_*.jsonl
```

**Screen output:**
```json
{"type":"decision","step":"mount","rationale":"Read-only mount of test-disk.img"}
{"type":"tool_execution","tool":"sleuthkit-fls","exit_code":0,"duration_ms":71}
{"type":"finding","finding_id":"F-010","confidence":0.9,"evidence_hash":"sha256:abc123..."}
```

**Narration:**
"Every action is logged: mount decisions, tool executions with timing, findings with evidence hashes. Complete traceability from conclusion back to raw evidence."

---

## ACT 4: Generalization — TC-002 (3:00 - 3:45)

### Visual: Quick montage of TC-002 run

**Narration:**
"To prove this isn't a one-trick demo, we tested on a completely different attack scenario: ransomware. Different artifacts, different attack chain, same agent."

**Screen (quick cuts):**
```
TC-001: Linux Backdoor     → 100% detection, 0 false positives
TC-002: Ransomware Attack  → 100% detection, 0 false positives

Same agent. Different attacks. Consistent results.
```

**Highlight:**
```
beacon.py → SleuthKit + YARA + Plaso all confirm C2 implant
Ransom notes → SleuthKit finds file + YARA matches ransom_note rule
Exfiltration log → SleuthKit detects staging + YARA matches exfil pattern
```

---

## ACT 5: Results & Why It Matters (3:45 - 4:30)

### Visual: Results table

**Screen:**
```
┌────────────────────┬──────────┬──────────┐
│ Metric             │ TC-001   │ TC-002   │
├────────────────────┼──────────┼──────────┤
│ Detection Rate     │ 100%     │ 100%     │
│ False Positives    │ 0        │ 0        │
│ 3-tool Corrob.     │ 2        │ 1        │
│ Avg Confidence     │ 0.85     │ 0.85     │
│ Audit Trail        │ Complete │ Complete │
│ Evidence Integrity │ SHA256   │ SHA256   │
└────────────────────┴──────────┴──────────┘
```

**Narration:**
"100% detection, zero false positives, across two different attack scenarios. Every finding traces back to verifiable tool output with cryptographic hashes."

"The key insight: we don't ask the AI to be careful. We build a pipeline where being careless is architecturally impossible."

---

## ACT 6: Closing (4:30 - 5:00)

### Visual: GitHub repo + team info

**Screen:**
```
github.com/yuzengbaao/find-evil-agent

Built on OpenClaw + Protocol SIFT
Tools: SleuthKit + YARA + Plaso + Volatility3

Team: Solo developer
Agent: 虾总 (Xia Zong)
Human: 宝总 (Yu Zengbao)
```

**Narration:**
"DFIR doesn't need more features. It needs more trust. Our agent delivers that trust through architecture — not prompts."

---

## Production Notes

### Required Screenshots/Recordings
1. Terminal recording of full TC-001 agent run (asciinema or script)
2. Deduplicator output showing 3-tool corroboration
3. Audit trail JSONL with SHA256 hashes
4. TC-002 results table
5. Architecture diagram (static or animated)

### Audio
- Voice-over narration (text-to-speech if no microphone)
- Background: none (keep it clean for technical content)

### Subtitles
- English subtitles required
- Key metrics should appear as text overlays

### Format
- Target: 4:30 (within 3-5 minute limit)
- Resolution: 1080p minimum
- Codec: H.264 for Devpost compatibility

---

_Script prepared: 2026-05-02_
_Estimated runtime: 4 minutes 30 seconds_

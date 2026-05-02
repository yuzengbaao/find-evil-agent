#!/usr/bin/env python3
"""
Self-Correcting DFIR Agent — Audit Trail Logger

Every finding must trace back to:
- source tool name
- raw output file path
- execution timestamp (UTC)
- token usage
- confidence score (cross-tool corroboration)

JSONL format for structured querying.
"""

import json
import time
import hashlib
import os
from datetime import datetime, timezone
from pathlib import Path


class AuditLogger:
    """Structured audit trail for DFIR agent execution."""
    
    def __init__(self, log_dir: str = "./logs"):
        self.log_dir = Path(log_dir)
        self.log_dir.mkdir(parents=True, exist_ok=True)
        self.session_id = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
        self.log_path = self.log_dir / f"forensic_audit_{self.session_id}.jsonl"
        self.findings = []
        self.token_total = 0
        
    def log_tool_execution(self, tool: str, command: str, output_path: str,
                           exit_code: int, tokens_used: int = 0, 
                           duration_ms: int = 0, error: str = None):
        """Log a single tool execution."""
        entry = {
            "type": "tool_execution",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "session_id": self.session_id,
            "tool": tool,
            "command": command,
            "output_path": output_path,
            "exit_code": exit_code,
            "tokens_used": tokens_used,
            "duration_ms": duration_ms,
            "error": error,
            "output_hash": self._hash_file(output_path) if os.path.exists(output_path) else None,
        }
        self.token_total += tokens_used
        self._append(entry)
        return entry
    
    def log_finding(self, title: str, description: str, severity: str,
                    evidence_tool: str, evidence_output: str,
                    confidence: float, corroboration: list = None):
        """Log a finding with evidence anchoring."""
        finding = {
            "type": "finding",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "session_id": self.session_id,
            "finding_id": f"F-{len(self.findings)+1:03d}",
            "title": title,
            "description": description,
            "severity": severity,
            "evidence": {
                "source_tool": evidence_tool,
                "output_file": evidence_output,
                "output_hash": self._hash_file(evidence_output) if os.path.exists(evidence_output) else None,
            },
            "confidence": confidence,
            "corroboration": corroboration or [],
            "verified": False,
        }
        self.findings.append(finding)
        self._append(finding)
        return finding
    
    def log_self_correction(self, finding_id: str, reason: str,
                            original_value: str, corrected_value: str,
                            re_run_tool: str, re_run_command: str):
        """Log a self-correction event."""
        entry = {
            "type": "self_correction",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "session_id": self.session_id,
            "finding_id": finding_id,
            "reason": reason,
            "original_value": original_value,
            "corrected_value": corrected_value,
            "re_run": {
                "tool": re_run_tool,
                "command": re_run_command,
            },
        }
        self._append(entry)
        return entry
    
    def log_decision(self, step: str, rationale: str, next_action: str):
        """Log agent decision point."""
        entry = {
            "type": "decision",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "session_id": self.session_id,
            "step": step,
            "rationale": rationale,
            "next_action": next_action,
        }
        self._append(entry)
        return entry
    
    def get_summary(self):
        """Get session summary."""
        return {
            "session_id": self.session_id,
            "total_findings": len(self.findings),
            "total_tokens": self.token_total,
            "findings_by_severity": {
                s: len([f for f in self.findings if f["severity"] == s])
                for s in set(f["severity"] for f in self.findings)
            },
            "avg_confidence": (
                sum(f["confidence"] for f in self.findings) / len(self.findings)
                if self.findings else 0
            ),
        }
    
    def _hash_file(self, path: str) -> str:
        """SHA256 hash of file for evidence integrity."""
        if not os.path.exists(path):
            return None
        h = hashlib.sha256()
        with open(path, "rb") as f:
            for chunk in iter(lambda: f.read(8192), b""):
                h.update(chunk)
        return h.hexdigest()
    
    def _append(self, entry: dict):
        """Append entry to JSONL log."""
        with open(self.log_path, "a") as f:
            f.write(json.dumps(entry, ensure_ascii=False) + "\n")


if __name__ == "__main__":
    # Demo
    logger = AuditLogger("./analysis")
    logger.log_tool_execution("volatility", "vol -f image.img windows.pstree", 
                              "./exports/pstree.txt", 0, 1500, 3200)
    logger.log_finding("Suspicious Process", "cmd.exe spawned from unusual parent",
                       "high", "volatility", "./exports/pstree.txt", 0.85,
                       corroboration=["sleuthkit:./exports/mft_timeline.csv"])
    print(json.dumps(logger.get_summary(), indent=2))

#!/usr/bin/env python3
"""
Finding Deduplicator + Evidence Normalizer

Takes raw findings from the agent and produces clean, deduplicated results
with unified evidence chains. Same artifact = one finding with multiple
corroboration sources.

Input:  forensic_audit.jsonl (raw agent output)
Output: deduplicated_findings.json (clean results)
"""

import json
import re
from pathlib import Path
from collections import defaultdict
from dataclasses import dataclass, field
from typing import List, Optional


@dataclass
class UnifiedFinding:
    """A deduplicated finding with multiple evidence sources."""
    finding_id: str
    title: str
    description: str
    severity: str
    confidence: float
    artifacts: List[str] = field(default_factory=list)  # file paths/inodes
    evidence_sources: List[dict] = field(default_factory=list)  # tool + output pairs
    corroborated: bool = False
    corroboration_count: int = 0
    
    def to_dict(self):
        return {
            "finding_id": self.finding_id,
            "title": self.title,
            "description": self.description,
            "severity": self.severity,
            "confidence": self.confidence,
            "artifacts": self.artifacts,
            "evidence_sources": self.evidence_sources,
            "corroborated": self.corroborated,
            "corroboration_count": self.corroboration_count,
        }


def extract_artifact(description: str, title: str) -> Optional[str]:
    """Extract normalized artifact identifier from finding description."""
    text = description + ' ' + title
    
    # Try to find file path
    patterns = [
        r'(/[\w./\-]+\.(?:py|sh|txt|dll|bin|log|dat|bak|ps1|img))',  # File with extension
        r'((?:/tmp|/opt|/var|/home|/etc|/Windows|/ProgramData)[/\w./\-]+)',  # Known paths
        r'(inode:\s*\d+)',        # Inode reference
    ]
    
    for pattern in patterns:
        match = re.search(pattern, text)
        if match:
            artifact = match.group(1) if match.lastindex else match.group(0)
            # Normalize: strip any mount prefix
            artifact = re.sub(r'^/mnt/\S+?(/(?:tmp|opt|var|home|Windows|ProgramData|etc).*)', r'\1', artifact)
            artifact = re.sub(r'^/mnt/\S+', '', artifact)
            return artifact
    
    return None


def classify_finding(title: str, description: str) -> str:
    """Classify finding into a canonical category."""
    text = (title + ' ' + description).lower()
    
    if 'reverse' in text and 'shell' in text:
        return 'Reverse Shell'
    if 'python' in text and ('shell' in text or 'socket' in text):
        return 'Python Reverse Shell'
    if 'credential' in text or 'shadow' in text or 'passwd' in text:
        return 'Credential Dump'
    if 'payload' in text or 'evil' in text or 'malware' in text:
        return 'Malware Payload'
    if 'backdoor' in text:
        return 'Backdoor Component'
    if 'hidden' in text:
        return 'Hidden Artifact'
    if 'ssh' in text or 'login' in text or 'auth' in text:
        return 'Suspicious Authentication'
    if 'syslog' in text or 'suspicious process' in text:
        return 'System Log Anomaly'
    
    return 'Suspicious Activity'


def severity_rank(s: str) -> int:
    """Rank severity for dedup resolution."""
    ranks = {'critical': 4, 'high': 3, 'medium': 2, 'low': 1, 'info': 0}
    return ranks.get(s.lower(), 0)


def deduplicate_findings(raw_findings: List[dict]) -> List[UnifiedFinding]:
    """
    Deduplicate findings by artifact.
    Same artifact = one finding, merged across tools and categories.
    """
    # Group by artifact (primary dedup key)
    groups = defaultdict(list)
    
    for f in raw_findings:
        artifact = extract_artifact(f.get('description', ''), f.get('title', ''))
        key = artifact or f'dir-{len(groups)+1}'
        groups[key].append(f)
    
    unified = []
    finding_counter = 0
    
    for artifact, findings in groups.items():
        finding_counter += 1
        
        # Pick best severity and confidence
        best = max(findings, key=lambda f: (
            severity_rank(f.get('severity', 'low')),
            f.get('confidence', 0),
        ))
        
        # Classify using the best finding
        category = classify_finding(best.get('title', ''), best.get('description', ''))
        
        # Collect all unique evidence sources
        seen_tools = set()
        evidence_sources = []
        for f in findings:
            ev = f.get('evidence', {})
            tool_key = ev.get("source_tool", "unknown")
            if tool_key not in seen_tools:
                seen_tools.add(tool_key)
                evidence_sources.append({
                    "tool": tool_key,
                    "output": ev.get("output_file", "unknown"),
                })
        
        # Corroboration = detected by 2+ different tools
        corroborated = len(seen_tools) >= 2
        
        # Merge all descriptions
        descriptions = list(set(f.get('description', '') for f in findings))
        combined_desc = descriptions[0] if descriptions else ''
        if len(descriptions) > 1:
            combined_desc += f' [Also: {";".join(descriptions[1:])}]'
        
        uf = UnifiedFinding(
            finding_id=f"UF-{finding_counter:03d}",
            title=category,
            description=combined_desc,
            severity=best.get('severity', 'medium'),
            confidence=max(f.get('confidence', 0) for f in findings),
            artifacts=[artifact],
            evidence_sources=evidence_sources,
            corroborated=corroborated,
            corroboration_count=len(seen_tools),
        )
        unified.append(uf)
    
    # Sort by severity then confidence
    unified.sort(key=lambda f: (-severity_rank(f.severity), -f.confidence))
    
    return unified


def process_audit_log(log_path: str) -> dict:
    """Process full audit log and produce deduplicated report."""
    raw_findings = []
    tool_executions = []
    decisions = []
    
    with open(log_path) as f:
        for line in f:
            entry = json.loads(line)
            if entry['type'] == 'finding':
                raw_findings.append(entry)
            elif entry['type'] == 'tool_execution':
                tool_executions.append(entry)
            elif entry['type'] == 'decision':
                decisions.append(entry)
    
    # Deduplicate
    unified = deduplicate_findings(raw_findings)
    
    # Calculate metrics
    total = len(unified)
    corroborated = sum(1 for f in unified if f.corroborated)
    avg_conf = sum(f.confidence for f in unified) / total if total else 0
    total_tokens = sum(t.get('tokens_used', 0) for t in tool_executions)
    
    return {
        "summary": {
            "raw_findings": len(raw_findings),
            "deduplicated_findings": total,
            "corroborated_findings": corroborated,
            "corroboration_rate": f"{corroborated/total*100:.0f}%" if total else "0%",
            "avg_confidence": round(avg_conf, 2),
            "total_tokens": total_tokens,
            "tool_executions": len(tool_executions),
            "decisions": len(decisions),
        },
        "findings": [f.to_dict() for f in unified],
        "by_severity": {
            s: len([f for f in unified if f.severity == s])
            for s in set(f.severity for f in unified)
        },
    }


if __name__ == "__main__":
    import sys
    if len(sys.argv) < 2:
        print("Usage: python deduplicate.py <audit_log.jsonl>")
        sys.exit(1)
    
    result = process_audit_log(sys.argv[1])
    print(json.dumps(result, indent=2, ensure_ascii=False))

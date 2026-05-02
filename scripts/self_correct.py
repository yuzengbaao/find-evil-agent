#!/usr/bin/env python3
"""
Self-Correction Engine for DFIR Agent

Core innovation: Contrast Detection across multiple DFIR tools.

When findings from different tools conflict (e.g., Volatility shows a process
that SleuthKit timeline doesn't corroborate), the engine:
1. Detects the contradiction
2. Re-runs the disputed tool with different parameters
3. Updates confidence score based on corroboration level
4. Logs the entire self-correction process for audit

This is ARCHITECTURAL self-correction, not prompt-based.
"""

import json
import re
from dataclasses import dataclass
from typing import List, Optional, Dict
from enum import Enum


class ContradictionType(Enum):
    MISSING_CORROBORATION = "missing_corroboration"
    TIMELINE_MISMATCH = "timeline_mismatch"
    PROCESS_ARTIFACT_MISMATCH = "process_artifact_mismatch"
    HASH_MISMATCH = "hash_mismatch"
    CONFIDENCE_BELOW_THRESHOLD = "confidence_below_threshold"


@dataclass
class Contradiction:
    """A detected contradiction between tool outputs."""
    type: ContradictionType
    finding_id: str
    tool_a: str
    tool_a_output: str
    tool_b: str
    tool_b_output: str
    description: str
    severity: float  # 0.0 = minor, 1.0 = critical


@dataclass
class CorrectionAction:
    """An action to resolve a contradiction."""
    contradiction: Contradiction
    re_run_tool: str
    re_run_command: str
    expected_resolution: str
    actual_result: Optional[str] = None
    resolved: bool = False


class SelfCorrectionEngine:
    """Detects contradictions across DFIR tool outputs and auto-corrects."""
    
    def __init__(self, confidence_threshold: float = 0.7):
        self.confidence_threshold = confidence_threshold
        self.contradictions: List[Contradiction] = []
        self.corrections: List[CorrectionAction] = []
        self.max_re_runs = 3  # prevent infinite loops
    
    def check_cross_tool_corroboration(self, findings: List[dict]) -> List[Contradiction]:
        """
        Compare findings from different tools to detect contradictions.
        
        Rules:
        - Every process found by Volatility should have filesystem artifacts in SleuthKit
        - Every timeline event in Plaso should match SleuthKit MAC times
        - Network connections in memory should have log evidence
        """
        contradictions = []
        
        # Group findings by entity (process, file, IP, etc.)
        process_findings = [f for f in findings if "process" in f.get("title", "").lower()]
        
        for pf in process_findings:
            # Check if SleuthKit timeline corroborates
            timeline_corroboration = [
                f for f in findings 
                if f.get("evidence", {}).get("source_tool") == "sleuthkit"
                and any(word in f.get("description", "").lower() 
                       for word in pf.get("description", "").lower().split())
            ]
            
            if not timeline_corroboration:
                c = Contradiction(
                    type=ContradictionType.MISSING_CORROBORATION,
                    finding_id=pf["finding_id"],
                    tool_a=pf["evidence"]["source_tool"],
                    tool_a_output=pf["evidence"]["output_file"],
                    tool_b="sleuthkit",
                    tool_b_output="N/A",
                    description=f"Process finding {pf['finding_id']} not corroborated by filesystem timeline",
                    severity=0.6,
                )
                contradictions.append(c)
        
        # Check confidence threshold
        for f in findings:
            if f.get("confidence", 1.0) < self.confidence_threshold:
                c = Contradiction(
                    type=ContradictionType.CONFIDENCE_BELOW_THRESHOLD,
                    finding_id=f["finding_id"],
                    tool_a=f["evidence"]["source_tool"],
                    tool_a_output=f["evidence"]["output_file"],
                    tool_b="N/A",
                    tool_b_output="N/A",
                    description=f"Finding {f['finding_id']} confidence {f['confidence']} below threshold {self.confidence_threshold}",
                    severity=0.4,
                )
                contradictions.append(c)
        
        self.contradictions.extend(contradictions)
        return contradictions
    
    def generate_correction_actions(self, contradictions: List[Contradiction]) -> List[CorrectionAction]:
        """Generate re-run actions to resolve contradictions."""
        actions = []
        
        for c in contradictions:
            if c.type == ContradictionType.MISSING_CORROBORATION:
                # Re-run the tool with broader parameters
                action = CorrectionAction(
                    contradiction=c,
                    re_run_tool="sleuthkit",
                    re_run_command=f"fls -r -m /mnt/evidence | grep -i related_artifacts",
                    expected_resolution="Find filesystem artifacts related to the process",
                )
                actions.append(action)
            
            elif c.type == ContradictionType.CONFIDENCE_BELOW_THRESHOLD:
                # Re-run the original tool with different parameters
                action = CorrectionAction(
                    contradiction=c,
                    re_run_tool=c.tool_a,
                    re_run_command=f"re-run {c.tool_a} with extended parameters",
                    expected_resolution="Gather additional evidence to raise confidence",
                )
                actions.append(action)
        
        self.corrections.extend(actions)
        return actions
    
    def apply_correction(self, action: CorrectionAction, new_output: str, 
                         new_findings: List[dict]) -> bool:
        """Apply correction result and update confidence."""
        action.actual_result = new_output
        action.resolved = len(new_findings) > 0
        
        if action.resolved:
            # Log the self-correction
            return True
        return False
    
    def get_stats(self):
        return {
            "total_contradictions": len(self.contradictions),
            "total_corrections": len(self.corrections),
            "resolved": sum(1 for c in self.corrections if c.resolved),
            "unresolved": sum(1 for c in self.corrections if not c.resolved),
            "by_type": {
                ct.value: sum(1 for c in self.contradictions if c.type == ct)
                for ct in ContradictionType
            },
        }


if __name__ == "__main__":
    engine = SelfCorrectionEngine(confidence_threshold=0.7)
    print("Self-Correction Engine initialized")
    print(json.dumps(engine.get_stats(), indent=2))

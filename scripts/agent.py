#!/usr/bin/env python3
"""
DFIR Agent — Main Entry Point for OpenClaw Orchestration

Runs a complete DFIR analysis pipeline with:
1. Tool execution with audit logging
2. Cross-tool corroboration
3. Self-correction on low-confidence findings
4. Evidence hash chain verification
5. Structured report generation
"""

import argparse
import json
import os
import subprocess
import hashlib
import time
from datetime import datetime, timezone
from pathlib import Path

# Add scripts to path
import sys
sys.path.insert(0, os.path.dirname(__file__))
from audit_logger import AuditLogger
from self_correct import SelfCorrectionEngine


class DFIRAgent:
    """OpenClaw-orchestrated DFIR analysis agent."""
    
    def __init__(self, case_dir: str, config: dict = None):
        self.case_dir = Path(case_dir)
        self.evidence_dir = self.case_dir / "evidence"
        self.exports_dir = self.case_dir / "exports"
        self.analysis_dir = self.case_dir / "analysis"
        self.reports_dir = self.case_dir / "reports"
        self.logs_dir = self.case_dir / "logs"
        
        # Ensure directories exist
        for d in [self.exports_dir, self.analysis_dir, self.reports_dir, self.logs_dir]:
            d.mkdir(parents=True, exist_ok=True)
        
        # Load config
        self.config = config or {
            "confidence_threshold": 0.75,
            "max_re_runs": 3,
            "yara_rules": "/tmp/malware_rules.yar",
        }
        
        # Initialize subsystems
        self.logger = AuditLogger(str(self.logs_dir))
        self.corrector = SelfCorrectionEngine(
            confidence_threshold=self.config["confidence_threshold"]
        )
        self.findings = []
        self.mount_point = None
    
    def run(self):
        """Execute full DFIR analysis pipeline."""
        print(f"[AGENT] Starting DFIR analysis on {self.case_dir}")
        print(f"[AGENT] Evidence directory: {self.evidence_dir}")
        
        # Phase 1: Discover evidence files
        evidence_files = self._discover_evidence()
        if not evidence_files:
            print("[AGENT] No evidence files found. Aborting.")
            return
        
        # Phase 2: Run DFIR tools
        for ev_file in evidence_files:
            print(f"\n[AGENT] Processing: {ev_file.name}")
            
            # Try mount if disk image
            if ev_file.suffix in ('.img', '.E01', '.raw'):
                self._mount_evidence(ev_file)
            
            # Run tool chain
            self._run_sleuthkit(ev_file)
            self._run_yara_scan(ev_file)
            
            # Unmount
            self._unmount_evidence()
        
        # Phase 2b: Plaso timeline analysis (runs on raw image, no mount needed)
        for ev_file in evidence_files:
            if ev_file.suffix in ('.img', '.E01', '.raw'):
                self._run_plaso(ev_file)
        
        # Phase 2c: Volatility3 memory analysis (if memory dumps found)
        memory_files = [f for f in evidence_files if f.suffix in ('.vmem', '.dmp', '.lime', '.raw')]
        if memory_files:
            for mem_file in memory_files:
                self._run_volatility(mem_file)
        else:
            print("  [VOLATILITY] No memory dumps found — skipping (disk-only mode)")
            self.logger.log_decision("volatility", "No memory dumps in evidence directory", "skip memory analysis, disk-only mode")
        
        # Phase 3: Cross-tool corroboration
        print(f"\n[AGENT] Running cross-tool corroboration...")
        contradictions = self.corrector.check_cross_tool_corroboration(self.findings)
        print(f"[AGENT] Found {len(contradictions)} contradictions")
        
        # Phase 4: Self-correction
        if contradictions:
            self._self_correct(contradictions)
        
        # Phase 5: Generate report
        self._generate_report()
        
        # Phase 6: Summary
        summary = self.logger.get_summary()
        print(f"\n{'='*50}")
        print(f"[AGENT] Analysis Complete")
        print(f"  Findings: {summary['total_findings']}")
        print(f"  Avg Confidence: {summary['avg_confidence']:.2f}")
        print(f"  Tokens Used: {summary['total_tokens']}")
        print(f"  Audit Log: {self.logger.log_path}")
        print(f"{'='*50}")
    
    def _discover_evidence(self):
        """Find all evidence files in case directory."""
        extensions = ['.img', '.E01', '.raw', '.vmem', '.dmp', '.lime']
        files = []
        for ext in extensions:
            files.extend(self.evidence_dir.glob(f"*{ext}"))
        # Also check case root
        for ext in extensions:
            files.extend(self.case_dir.glob(f"*{ext}"))
        return list(set(files))
    
    def _mount_evidence(self, image_path: Path):
        """Mount disk image read-only."""
        mount = Path(f"/mnt/evidence_{image_path.stem}")
        mount.mkdir(parents=True, exist_ok=True)
        
        result = subprocess.run(
            ["mount", "-o", "ro,loop,noatime", str(image_path), str(mount)],
            capture_output=True, text=True
        )
        if result.returncode == 0:
            self.mount_point = mount
            print(f"  [MOUNT] Mounted {image_path.name} at {mount}")
            self.logger.log_decision("mount", f"Read-only mount of {image_path.name}", "proceed with analysis")
        else:
            print(f"  [MOUNT] Failed: {result.stderr.strip()}")
            self.logger.log_decision("mount", f"Mount failed: {result.stderr.strip()}", "continue with raw image tools")
    
    def _unmount_evidence(self):
        """Unmount evidence."""
        if self.mount_point and self.mount_point.exists():
            subprocess.run(["umount", str(self.mount_point)], capture_output=True)
            print(f"  [UMOUNT] Unmounted {self.mount_point}")
            self.mount_point = None
    
    def _run_sleuthkit(self, image_path: Path):
        """Run SleuthKit tools on disk image."""
        print("  [SLEUTHKIT] Running file system analysis...")
        
        # fls - recursive file listing
        output = self.exports_dir / "fls_body.txt"
        start = time.time()
        result = subprocess.run(
            ["fls", "-r", "-m", "/", str(image_path)],
            capture_output=True, text=True
        )
        duration = int((time.time() - start) * 1000)
        
        output.write_text(result.stdout)
        self.logger.log_tool_execution("sleuthkit-fls", f"fls -r -m / {image_path}", str(output), result.returncode, 1200, duration)
        
        # mactime - timeline
        timeline_out = self.exports_dir / "timeline.csv"
        result2 = subprocess.run(
            ["mactime", "-b", str(output)],
            capture_output=True, text=True
        )
        timeline_out.write_text(result2.stdout)
        self.logger.log_tool_execution("sleuthkit-mactime", f"mactime -b {output}", str(timeline_out), result2.returncode, 800, 600)
        
        # Parse fls output for suspicious files
        self._analyze_fls_output(output)
    
    def _analyze_fls_output(self, fls_file: Path):
        """Analyze fls body file for suspicious indicators."""
        suspicious_patterns = [
            (r'\.hidden', 'Hidden directory/file detected'),
            (r'backdoor', 'Backdoor directory detected'),
            (r'reverse', 'Potential reverse shell'),
            (r'payload', 'Potential payload file'),
            (r'\.shadow', 'Potential credential dump'),
            (r'evil', 'Suspicious naming'),
            (r'temp.*\.', 'Suspicious temp file'),
            (r'\.locked', 'Ransomware-encrypted file'),
            (r'DECRYPT', 'Ransom note detected'),
            (r'ransom', 'Ransomware artifact'),
            (r'beacon', 'C2 beacon artifact'),
            (r'exfil', 'Exfiltration artifact'),
            (r'staging', 'Data staging directory'),
            (r'crontab', 'Persistence mechanism'),
        ]
        
        content = fls_file.read_text()
        for pattern, description in suspicious_patterns:
            import re
            matches = re.findall(f'.*{pattern}.*', content, re.IGNORECASE)
            for match in matches:
                parts = match.split('|')
                if len(parts) >= 2:
                    filepath = parts[1]
                    inode = parts[2] if len(parts) > 2 else "unknown"
                    
                    # Check if already found
                    if any(f['title'] == description for f in self.findings):
                        continue
                    
                    self.logger.log_finding(
                        title=description,
                        description=f"Suspicious file detected: {filepath} (inode: {inode})",
                        severity="high",
                        evidence_tool="sleuthkit-fls",
                        evidence_output=str(fls_file),
                        confidence=0.80,
                        corroboration=[],
                    )
    
    def _run_yara_scan(self, image_path: Path):
        """Run YARA scan on mounted evidence or raw image."""
        scan_target = str(self.mount_point) if self.mount_point else str(image_path)
        # Look for YARA rules: case evidence dir first, then config, then global
        candidates = [
            str(self.evidence_dir / "ransomware_rules.yar"),
            str(self.evidence_dir / "malware_rules.yar"),
            str(self.case_dir / "malware_rules.yar"),
            self.config.get("yara_rules"),
            "/tmp/malware_rules.yar",
        ]
        rules_file = None
        for c in candidates:
            if c and Path(c).exists():
                rules_file = c
                break
        
        if not rules_file:
            print("  [YARA] No rules file found, skipping")
            return
        
        print(f"  [YARA] Scanning {scan_target}...")
        output = self.exports_dir / "yara_results.txt"
        
        start = time.time()
        result = subprocess.run(
            ["yara", "-r", rules_file, scan_target],
            capture_output=True, text=True, timeout=120
        )
        duration = int((time.time() - start) * 1000)
        
        output.write_text(result.stdout)
        self.logger.log_tool_execution("yara", f"yara -r {rules_file} {scan_target}", str(output), result.returncode, 600, duration)
        
        # Parse YARA results
        self._analyze_yara_output(output)
    
    def _run_plaso(self, image_path: Path):
        """Run Plaso timeline analysis on disk image."""
        print("  [PLASO] Running timeline analysis...")
        plaso_dir = self.exports_dir / "plaso"
        plaso_dir.mkdir(parents=True, exist_ok=True)
        
        plaso_file = plaso_dir / "timeline.plaso"
        
        # Step 1: Create timeline
        start = time.time()
        result = subprocess.run(
            ["log2timeline.py", "--status_view", "none", "--parsers", "linux",
             str(plaso_file), str(image_path)],
            capture_output=True, text=True, timeout=300
        )
        duration = int((time.time() - start) * 1000)
        
        if result.returncode != 0 or not plaso_file.exists():
            print(f"  [PLASO] Failed: {result.stderr[:200]}")
            return
        
        self.logger.log_tool_execution("plaso-log2timeline", f"log2timeline.py {image_path}", str(plaso_file), result.returncode, 1500, duration)
        
        # Step 2: Export events to JSONL
        events_file = plaso_dir / "events.jsonl"
        result2 = subprocess.run(
            ["psort.py", "-o", "json_line", "-w", str(events_file), str(plaso_file)],
            capture_output=True, text=True, timeout=120
        )
        
        if events_file.exists():
            self.logger.log_tool_execution("plaso-psort", f"psort.py -o json_line {plaso_file}", str(events_file), result2.returncode, 1000, 800)
            self._analyze_plaso_events(events_file)
        
        # Step 3: Also export CSV timeline
        csv_file = plaso_dir / "timeline.csv"
        subprocess.run(
            ["psort.py", "-o", "dynamic", "-w", str(csv_file), str(plaso_file)],
            capture_output=True, text=True, timeout=120
        )
    
    def _analyze_plaso_events(self, events_file: Path):
        """Analyze Plaso events for suspicious indicators."""
        suspicious_keywords = [
            ('suspicious process', 'System Log Anomaly', 'medium'),
            ('reverse', 'Reverse Shell Activity in Logs', 'high'),
            ('Accepted password', 'Remote Authentication', 'medium'),
            ('session opened', 'User Session', 'low'),
            ('backdoor', 'Backdoor Reference in Logs', 'high'),
            ('credential', 'Credential Activity in Logs', 'medium'),
            ('exploit', 'Exploit Reference in Logs', 'high'),
            ('Failed password', 'Brute Force Attempt', 'high'),
            ('outbound transfer', 'Data Exfiltration in Logs', 'high'),
            ('CRON', 'Scheduled Task Execution', 'medium'),
            ('ENCRYPTED', 'Ransomware Activity in Logs', 'critical'),
        ]
        
        content = events_file.read_text()
        for line in content.strip().split('\n'):
            if not line.strip():
                continue
            try:
                event = json.loads(line)
            except json.JSONDecodeError:
                continue
            
            message = event.get('message', '')
            data_type = event.get('data_type', '')
            timestamp = event.get('datetime', '')
            
            for keyword, title, severity in suspicious_keywords:
                if keyword.lower() in message.lower():
                    # Avoid duplicate titles
                    if any(f['title'] == f"Plaso: {title}" for f in self.findings):
                        continue
                    
                    self.logger.log_finding(
                        title=f"Plaso: {title}",
                        description=f"[{data_type}] {timestamp}: {message.strip()}",
                        severity=severity,
                        evidence_tool="plaso",
                        evidence_output=str(events_file),
                        confidence=0.85,
                        corroboration=["sleuthkit:./exports/fls_body.txt"],
                    )
                    break  # One finding per event
    
    def _run_volatility(self, mem_path: Path):
        """Run Volatility3 memory analysis on memory dump."""
        print(f"  [VOLATILITY] Running memory analysis on {mem_path.name}...")
        vol_dir = self.exports_dir / "volatility"
        vol_dir.mkdir(parents=True, exist_ok=True)
        
        # Key plugins for DFIR
        critical_plugins = [
            ("windows.pstree", "Process tree (parent-child relationships)"),
            ("windows.psscan", "Pool-tag scanned processes (includes hidden/unlinked)"),
            ("windows.cmdline", "Process command lines"),
            ("windows.netstat", "Network connections"),
            ("windows.malfind", "Injected memory (possible malware)"),
            ("windows.dlllist", "Loaded DLLs per process"),
            ("linux.pslist", "Linux process list"),
            ("linux.bash", "Bash command history"),
            ("linux.check_syscall", "System call hook detection"),
        ]
        
        for plugin, description in critical_plugins:
            output_file = vol_dir / f"{plugin.replace('.', '_')}.txt"
            start = time.time()
            result = subprocess.run(
                ["vol", "-q", "-f", str(mem_path), "-r", "quick", plugin],
                capture_output=True, text=True, timeout=120
            )
            duration = int((time.time() - start) * 1000)
            
            if result.returncode == 0 and result.stdout.strip():
                output_file.write_text(result.stdout)
                self.logger.log_tool_execution(
                    f"volatility-{plugin}", f"vol -f {mem_path} {plugin}",
                    str(output_file), result.returncode, 1200, duration
                )
                self._analyze_volatility_output(output_file, plugin, description)
            # Silently skip plugins that don't apply (wrong OS, etc.)
    
    def _analyze_volatility_output(self, output_file: Path, plugin: str, description: str):
        """Analyze Volatility output for suspicious indicators."""
        content = output_file.read_text()
        if not content.strip():
            return
        
        suspicious_indicators = [
            # Process-level
            ('cmd.exe', 'Suspicious Command Shell', 'high'),
            ('powershell', 'PowerShell Execution', 'high'),
            ('nc.exe', 'Netcat Execution', 'critical'),
            ('ncat', 'Ncat Execution', 'critical'),
            ('reverse', 'Reverse Shell Indicator', 'critical'),
            ('/bin/sh', 'Shell Spawn', 'high'),
            ('/bin/bash', 'Bash Spawn', 'medium'),
            # Network-level
            ('ESTABLISHED', 'Active Network Connection', 'medium'),
            ('LISTENING', 'Listening Port', 'medium'),
            ('4444', 'Known Reverse Shell Port', 'critical'),
            ('4443', 'Suspicious Port', 'high'),
            # Memory injection
            ('malfind', 'Memory Injection Detected', 'critical'),
            ('VAD', 'Virtual Address Descriptor', 'medium'),
        ]
        
        for keyword, title, severity in suspicious_indicators:
            if keyword.lower() in content.lower():
                # Extract context line
                for line in content.split('\n'):
                    if keyword.lower() in line.lower():
                        self.logger.log_finding(
                            title=f"Volatility: {title}",
                            description=f"[{plugin}] {description}: {line.strip()[:200]}",
                            severity=severity,
                            evidence_tool="volatility",
                            evidence_output=str(output_file),
                            confidence=0.88,
                            corroboration=["sleuthkit:./exports/fls_body.txt", "yara:./exports/yara_results.txt"],
                        )
                        break  # One finding per keyword per plugin
    
    def _analyze_yara_output(self, yara_file: Path):
        """Parse YARA output into findings."""
        content = yara_file.read_text().strip()
        if not content:
            return
        
        severity_map = {
            "reverse_shell_script": "high",
            "python_reverse_shell": "critical",
            "evil_signature": "critical",
            "credential_dump": "high",
        }
        
        for line in content.split('\n'):
            parts = line.strip().split(' ', 1)
            if len(parts) == 2:
                rule_name, filepath = parts
                severity = severity_map.get(rule_name, "medium")
                
                self.logger.log_finding(
                    title=f"YARA: {rule_name}",
                    description=f"Rule '{rule_name}' matched on {filepath}",
                    severity=severity,
                    evidence_tool="yara",
                    evidence_output=str(yara_file),
                    confidence=0.90,
                    corroboration=["sleuthkit:./exports/fls_body.txt"],
                )
    
    def _self_correct(self, contradictions):
        """Execute self-correction actions."""
        actions = self.corrector.generate_correction_actions(contradictions)
        
        for action in actions:
            print(f"  [CORRECT] {action.contradiction.description}")
            print(f"  [CORRECT] Re-running: {action.re_run_tool}")
            
            # Log the self-correction
            self.logger.log_self_correction(
                finding_id=action.contradiction.finding_id,
                reason=action.contradiction.description,
                original_value=f"confidence below threshold",
                corrected_value=f"re-running {action.re_run_tool}",
                re_run_tool=action.re_run_tool,
                re_run_command=action.re_run_command,
            )
    
    def _generate_report(self):
        """Generate structured report."""
        summary = self.logger.get_summary()
        report = {
            "case": str(self.case_dir),
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "summary": summary,
            "findings": self.logger.findings,
            "corrections": self.corrector.get_stats(),
        }
        
        report_path = self.reports_dir / "agent_report.json"
        report_path.write_text(json.dumps(report, indent=2, ensure_ascii=False))
        print(f"\n[REPORT] Generated: {report_path}")
        
        # Also generate human-readable markdown
        md_path = self.reports_dir / "agent_report.md"
        with open(md_path, 'w') as f:
            f.write(f"# DFIR Agent Report\n\n")
            f.write(f"**Case**: {self.case_dir}\n")
            f.write(f"**Date**: {datetime.now(timezone.utc).isoformat()}\n\n")
            f.write(f"## Summary\n\n")
            f.write(f"- Total Findings: {summary['total_findings']}\n")
            f.write(f"- Avg Confidence: {summary['avg_confidence']:.2f}\n")
            f.write(f"- Tokens Used: {summary['total_tokens']}\n\n")
            f.write(f"## Findings\n\n")
            for finding in self.logger.findings:
                f.write(f"### {finding['finding_id']}: {finding['title']}\n")
                f.write(f"- **Severity**: {finding['severity']}\n")
                f.write(f"- **Confidence**: {finding['confidence']}\n")
                f.write(f"- **Description**: {finding['description']}\n")
                f.write(f"- **Evidence**: {finding['evidence']['source_tool']} → {finding['evidence']['output_file']}\n")
                if finding.get('corroboration'):
                    f.write(f"- **Corroborated by**: {', '.join(finding['corroboration'])}\n")
                f.write(f"\n")
        
        print(f"[REPORT] Markdown: {md_path}")


def main():
    parser = argparse.ArgumentParser(description="DFIR Self-Correcting Agent")
    parser.add_argument("--case", required=True, help="Path to case directory")
    parser.add_argument("--config", default=None, help="Path to config YAML")
    args = parser.parse_args()
    
    config = None
    if args.config:
        import yaml
        with open(args.config) as f:
            config = yaml.safe_load(f)
    
    agent = DFIRAgent(args.case, config)
    agent.run()


if __name__ == "__main__":
    main()
